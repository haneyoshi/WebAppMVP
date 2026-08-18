import unittest
from datetime import date

from app import create_app, db
from app.models import (
    Area,
    Assignment,
    AttendanceRecord,
    Building,
    User,
    assignment_workers,
)


class AssignmentAndAvailabilityApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        })
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            building = Building(building_name="Test Building")
            db.session.add(building)
            db.session.flush()
            areas = [
                Area(area_name="Area One", building_id=building.building_id),
                Area(area_name="Area Two", building_id=building.building_id),
            ]
            db.session.add_all(areas)
            db.session.flush()
            self.areas = {
                area.area_name: area.area_id
                for area in areas
            }
            self.users = {}
            for name, role, area in (
                ("Worker One", "worker", areas[0]),
                ("Worker Two", "worker", areas[1]),
                ("Coordinator", "coordinator", None),
                ("Supervisor", "supervisor", None),
            ):
                user = User(
                    name=name,
                    email=f"{name.lower().replace(' ', '')}@example.com",
                    role=role,
                    area_id=area.area_id if area else None,
                )
                user.set_password("demo")
                db.session.add(user)
                db.session.flush()
                self.users[name] = user.user_id
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    def login(self, name):
        self.client.post("/auth/login", json={
            "email": f"{name.lower().replace(' ', '')}@example.com",
            "password": "demo",
        })

    def payload(self):
        return {
            "assignment_date": date.today().isoformat(),
            "assignment_type": "Snow clearing",
            "location_task": "North entrance",
            "worker_ids": [self.users["Worker One"], self.users["Worker Two"]],
            "note": "Priority route",
        }

    def test_coordinator_creates_and_updates_multi_worker_assignment(self):
        self.login("Coordinator")
        response = self.client.post("/assignments", json=self.payload())

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.get_json()["workers"]), 2)
        assignment_id = response.get_json()["assignment_id"]

        payload = self.payload()
        payload["worker_ids"] = [self.users["Worker One"]]
        payload["location_task"] = "South entrance"
        updated = self.client.put(f"/assignments/{assignment_id}", json=payload)
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.get_json()["location_task"], "South entrance")
        self.assertEqual(len(updated.get_json()["workers"]), 1)

    def test_assignment_supports_structured_destination(self):
        self.login("Coordinator")
        payload = self.payload()
        payload["destination_area_id"] = self.areas["Area Two"]

        created = self.client.post("/assignments", json=payload)

        self.assertEqual(created.status_code, 201)
        assignment = created.get_json()
        self.assertEqual(assignment["destination_area_id"], self.areas["Area Two"])
        self.assertEqual(assignment["destination_area_name"], "Area Two")
        self.assertEqual(assignment["destination_building_name"], "Test Building")

        listed = self.client.get("/assignments").get_json()
        self.assertEqual(listed[0]["destination_area_id"], self.areas["Area Two"])

    def test_assignment_update_can_set_and_clear_structured_destination(self):
        self.login("Coordinator")
        payload = self.payload()
        created = self.client.post("/assignments", json=payload).get_json()

        payload["destination_area_id"] = self.areas["Area Two"]
        updated = self.client.put(
            f"/assignments/{created['assignment_id']}", json=payload
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(
            updated.get_json()["destination_area_id"], self.areas["Area Two"]
        )

        payload["destination_area_id"] = None
        updated = self.client.put(
            f"/assignments/{created['assignment_id']}", json=payload
        )
        self.assertEqual(updated.status_code, 200)
        self.assertIsNone(updated.get_json()["destination_area_id"])

    def test_assignment_without_destination_remains_valid(self):
        self.login("Coordinator")
        response = self.client.post("/assignments", json=self.payload())

        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response.get_json()["destination_area_id"])
        self.assertEqual(response.get_json()["location_task"], "North entrance")

    def test_assignment_rejects_nonexistent_destination_area(self):
        self.login("Coordinator")
        payload = self.payload()
        payload["destination_area_id"] = 999

        response = self.client.post("/assignments", json=payload)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["error"], "destination_area_id 999 not found")

    def test_coordinator_deletes_assignment_and_worker_associations(self):
        self.login("Coordinator")
        created = self.client.post("/assignments", json=self.payload()).get_json()
        assignment_id = created["assignment_id"]

        deleted = self.client.delete(f"/assignments/{assignment_id}")

        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(deleted.get_json(), {
            "message": "Assignment deleted",
            "assignment_id": assignment_id,
        })
        self.assertEqual(
            self.client.get(f"/assignments/{assignment_id}").status_code,
            404,
        )
        with self.app.app_context():
            association_count = db.session.execute(
                db.select(db.func.count()).select_from(assignment_workers).where(
                    assignment_workers.c.assignment_id == assignment_id
                )
            ).scalar_one()
            self.assertEqual(association_count, 0)
            self.assertIsNone(db.session.get(Assignment, assignment_id))

    def test_assignment_deletion_restores_attendance_availability(self):
        with self.app.app_context():
            db.session.add(AttendanceRecord(
                user_id=self.users["Worker One"],
                attendance_date=date.today(),
                present=True,
                status="Working",
            ))
            db.session.commit()
        self.login("Coordinator")
        payload = self.payload()
        payload["destination_area_id"] = self.areas["Area Two"]
        assignment_id = self.client.post(
            "/assignments", json=payload
        ).get_json()["assignment_id"]

        before = {
            row["name"]: row
            for row in self.client.get("/workers/availability").get_json()
        }
        self.assertEqual(before["Worker One"]["status"], "Assigned elsewhere")
        self.assertEqual(before["Worker Two"]["status"], "Assigned elsewhere")
        self.assertEqual(len(before["Worker One"]["assignments"]), 1)
        self.assertEqual(len(before["Worker Two"]["assignments"]), 1)

        self.client.delete(f"/assignments/{assignment_id}")

        after = {
            row["name"]: row
            for row in self.client.get("/workers/availability").get_json()
        }
        self.assertEqual(after["Worker One"]["assignments"], [])
        self.assertEqual(after["Worker One"]["status"], "Working")
        self.assertEqual(after["Worker Two"]["assignments"], [])
        self.assertEqual(after["Worker Two"]["status"], "Away")

    def test_supervisor_can_delete_assignment(self):
        self.login("Coordinator")
        assignment_id = self.client.post(
            "/assignments", json=self.payload()
        ).get_json()["assignment_id"]
        self.login("Supervisor")

        self.assertEqual(
            self.client.delete(f"/assignments/{assignment_id}").status_code,
            200,
        )

    def test_assignment_deletion_authorization_and_missing_error(self):
        self.login("Coordinator")
        assignment_id = self.client.post(
            "/assignments", json=self.payload()
        ).get_json()["assignment_id"]

        self.login("Worker One")
        self.assertEqual(
            self.client.delete(f"/assignments/{assignment_id}").status_code,
            403,
        )
        unauthenticated_client = self.app.test_client()
        self.assertEqual(
            unauthenticated_client.delete(
                f"/assignments/{assignment_id}"
            ).status_code,
            401,
        )

        self.login("Coordinator")
        missing = self.client.delete("/assignments/999")
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(missing.get_json(), {"error": "Assignment not found"})

    def test_worker_can_view_but_not_manage_assignments(self):
        self.login("Worker One")
        self.assertEqual(self.client.get("/assignments").status_code, 200)
        self.assertEqual(self.client.post("/assignments", json=self.payload()).status_code, 403)

    def test_assignment_validates_workers(self):
        self.login("Coordinator")
        payload = self.payload()
        payload["worker_ids"] = [999]
        self.assertEqual(self.client.post("/assignments", json=payload).status_code, 404)

        payload = self.payload()
        payload["worker_ids"] = [self.users["Coordinator"]]
        self.assertEqual(self.client.post("/assignments", json=payload).status_code, 400)

    def test_availability_uses_assignment_without_exposing_absence_reason(self):
        with self.app.app_context():
            db.session.add(AttendanceRecord(
                user_id=self.users["Worker Two"],
                attendance_date=date.today(),
                present=False,
                status="Away",
                absence_reason="Private medical reason",
            ))
            db.session.commit()
        self.login("Coordinator")
        payload = self.payload()
        payload["destination_area_id"] = self.areas["Area Two"]
        self.client.post("/assignments", json=payload)

        response = self.client.get("/workers/availability")
        self.assertEqual(response.status_code, 200)
        self.assertEqual({row["status"] for row in response.get_json()}, {"Assigned elsewhere"})
        self.assertTrue(all("absence_reason" not in row for row in response.get_json()))
        self.assertTrue(all(
            row["assignments"][0]["destination_area_id"] == self.areas["Area Two"]
            for row in response.get_json()
        ))
        self.assertTrue(all(
            row["assignments"][0]["destination_area_name"] == "Area Two"
            for row in response.get_json()
        ))

    def test_availability_requires_authentication(self):
        self.assertEqual(self.client.get("/workers/availability").status_code, 401)

    def test_availability_preserves_attendance_then_away_precedence(self):
        with self.app.app_context():
            db.session.add(AttendanceRecord(
                user_id=self.users["Worker One"],
                attendance_date=date.today(),
                present=True,
                status="Working",
            ))
            db.session.commit()
        self.login("Coordinator")

        response = self.client.get("/workers/availability")

        self.assertEqual(response.status_code, 200)
        statuses = {row["name"]: row["status"] for row in response.get_json()}
        self.assertEqual(statuses["Worker One"], "Working")
        self.assertEqual(statuses["Worker Two"], "Away")


if __name__ == "__main__":
    unittest.main()
