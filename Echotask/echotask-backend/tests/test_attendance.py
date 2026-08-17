import unittest
from datetime import date

from app import create_app, db
from app.models import Area, AttendanceRecord, Building, User


class AttendanceApiTestCase(unittest.TestCase):
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
        return self.client.post("/auth/login", json={
            "email": f"{name.lower().replace(' ', '')}@example.com",
            "password": "demo",
        })

    def test_worker_checks_in_once_per_day(self):
        self.login("Worker One")
        response = self.client.post("/attendance/check-in")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["status"], "Working")
        duplicate = self.client.post("/attendance/check-in")
        self.assertEqual(duplicate.status_code, 409)
        self.assertEqual(duplicate.get_json(), {"error": "Already checked in."})

    def test_coordinator_creates_and_corrects_official_attendance(self):
        self.login("Coordinator")
        response = self.client.post("/attendance", json={
            "user_id": self.users["Worker One"],
            "attendance_date": date.today().isoformat(),
            "status": "Away",
            "absence_reason": "Medical appointment",
        })

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["absence_reason"], "Medical appointment")
        record_id = response.get_json()["attendance_record_id"]
        corrected = self.client.patch(f"/attendance/{record_id}", json={
            "status": "Assigned elsewhere",
            "absence_reason": None,
        })
        self.assertEqual(corrected.status_code, 200)
        self.assertEqual(corrected.get_json()["status"], "Assigned elsewhere")

    def test_worker_sees_only_own_private_attendance(self):
        with self.app.app_context():
            db.session.add_all([
                AttendanceRecord(
                    user_id=self.users["Worker One"], attendance_date=date.today(),
                    present=False, status="Away", absence_reason="Private one",
                ),
                AttendanceRecord(
                    user_id=self.users["Worker Two"], attendance_date=date.today(),
                    present=False, status="Away", absence_reason="Private two",
                ),
            ])
            db.session.commit()
            other_id = AttendanceRecord.query.filter_by(
                user_id=self.users["Worker Two"]
            ).one().attendance_record_id

        self.login("Worker One")
        listed = self.client.get("/attendance")
        self.assertEqual(len(listed.get_json()), 1)
        self.assertEqual(listed.get_json()[0]["absence_reason"], "Private one")
        self.assertEqual(self.client.get(f"/attendance/{other_id}").status_code, 403)

    def test_worker_cannot_manage_official_attendance(self):
        self.login("Worker One")
        response = self.client.post("/attendance", json={
            "user_id": self.users["Worker One"], "status": "Away"
        })
        self.assertEqual(response.status_code, 403)

    def test_attendance_requires_authentication_and_valid_status(self):
        self.assertEqual(self.client.get("/attendance").status_code, 401)
        self.login("Supervisor")
        response = self.client.post("/attendance", json={
            "user_id": self.users["Worker One"], "status": "Late"
        })
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
