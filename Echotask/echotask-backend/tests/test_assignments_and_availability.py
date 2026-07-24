import unittest
from datetime import date

from app import create_app, db
from app.models import Area, AttendanceRecord, Building, User


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
            self.users = {}
            for name, role, area in (
                ("Worker One", "worker", areas[0]),
                ("Worker Two", "worker", areas[1]),
                ("Coordinator", "coordinator", None),
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
        self.client.post("/assignments", json=self.payload())

        response = self.client.get("/workers/availability")
        self.assertEqual(response.status_code, 200)
        self.assertEqual({row["status"] for row in response.get_json()}, {"Assigned elsewhere"})
        self.assertTrue(all("absence_reason" not in row for row in response.get_json()))

    def test_availability_requires_authentication(self):
        self.assertEqual(self.client.get("/workers/availability").status_code, 401)


if __name__ == "__main__":
    unittest.main()
