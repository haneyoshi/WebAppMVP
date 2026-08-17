import unittest

from app import create_app, db
from app.models import Area, Building, User


class SeedCommandTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        })
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    def test_core_data_seed_hashes_demo_passwords_and_loads_relationships(self):
        result = self.app.test_cli_runner().invoke(args=["seed-core-data"])

        self.assertEqual(result.exit_code, 0, result.output)
        with self.app.app_context():
            self.assertEqual(Building.query.count(), 10)
            self.assertEqual(Area.query.count(), 22)
            self.assertEqual(User.query.count(), 24)
            user = db.session.get(User, 1)
            self.assertNotEqual(user.password_hash, "demo")
            self.assertTrue(user.check_password("demo"))
            self.assertEqual(user.area_id, 1)

        login = self.client.post("/auth/login", json={
            "email": "user1@example.com", "password": "demo"
        })
        self.assertEqual(login.status_code, 200)
        supervisor_login = self.client.post("/auth/login", json={
            "email": "sara@example.com", "password": "demo"
        })
        self.assertEqual(supervisor_login.status_code, 200)
        self.assertEqual(supervisor_login.get_json()["role"], "supervisor")


if __name__ == "__main__":
    unittest.main()
