import unittest

from app import create_app, db
from app.models import Area, Building, User


class UserManagementApiTestCase(unittest.TestCase):
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
            area = Area(area_name="Test Area", building_id=building.building_id)
            db.session.add(area)
            db.session.flush()
            self.area_id = area.area_id
            for name, role in (("Supervisor", "supervisor"), ("Coordinator", "coordinator")):
                user = User(name=name, email=f"{role}@example.com", role=role)
                user.set_password("demo")
                db.session.add(user)
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    def login(self, role):
        self.client.post("/auth/login", json={
            "email": f"{role}@example.com", "password": "demo"
        })

    def worker_payload(self):
        return {
            "name": "New Worker",
            "email": "newworker@example.com",
            "password": "new-password",
            "role": "worker",
            "area_id": self.area_id,
        }

    def test_supervisor_creates_hashed_account_and_deactivates_without_deleting(self):
        self.login("supervisor")
        created = self.client.post("/users", json=self.worker_payload())
        self.assertEqual(created.status_code, 201)
        user_id = created.get_json()["user_id"]

        deactivated = self.client.delete(f"/users/{user_id}")
        self.assertEqual(deactivated.status_code, 200)
        with self.app.app_context():
            user = db.session.get(User, user_id)
            self.assertIsNotNone(user)
            self.assertFalse(user.is_active)
            self.assertNotEqual(user.password_hash, "new-password")

    def test_coordinator_cannot_manage_accounts(self):
        self.login("coordinator")
        self.assertEqual(self.client.post("/users", json=self.worker_payload()).status_code, 403)

    def test_account_role_and_area_rules_are_validated(self):
        self.login("supervisor")
        payload = self.worker_payload()
        payload["area_id"] = None
        self.assertEqual(self.client.post("/users", json=payload).status_code, 400)

        payload = self.worker_payload()
        payload["role"] = "coordinator"
        self.assertEqual(self.client.post("/users", json=payload).status_code, 400)

    def test_supervisor_cannot_deactivate_self(self):
        self.login("supervisor")
        me = self.client.get("/auth/me").get_json()
        self.assertEqual(self.client.delete(f"/users/{me['user_id']}").status_code, 400)


if __name__ == "__main__":
    unittest.main()
