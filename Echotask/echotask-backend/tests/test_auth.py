import unittest

from app import create_app, db
from app.models import User


class AuthenticationApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        })
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            user = User(name="Worker", email="worker@example.com", role="worker")
            user.set_password("demo")
            db.session.add(user)
            inactive = User(
                name="Inactive", email="inactive@example.com", role="worker", is_active=False
            )
            inactive.set_password("demo")
            db.session.add(inactive)
            db.session.commit()
            self.user_id = user.user_id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    def test_login_sets_session_and_password_is_hashed(self):
        response = self.client.post("/auth/login", json={
            "email": "worker@example.com",
            "password": "demo",
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["user_id"], self.user_id)
        self.assertEqual(self.client.get("/auth/me").status_code, 200)
        with self.app.app_context():
            self.assertNotEqual(db.session.get(User, self.user_id).password_hash, "demo")

    def test_invalid_credentials_and_inactive_account_are_rejected(self):
        self.assertEqual(self.client.post("/auth/login", json={
            "email": "worker@example.com", "password": "wrong"
        }).status_code, 401)
        self.assertEqual(self.client.post("/auth/login", json={
            "email": "inactive@example.com", "password": "demo"
        }).status_code, 401)

    def test_logout_clears_session(self):
        self.client.post("/auth/login", json={
            "email": "worker@example.com", "password": "demo"
        })
        self.assertEqual(self.client.post("/auth/logout").status_code, 200)
        self.assertEqual(self.client.get("/auth/me").status_code, 401)

    def test_me_requires_authentication(self):
        self.assertEqual(self.client.get("/auth/me").status_code, 401)

    def test_health_check_is_public_and_errors_are_json(self):
        self.assertEqual(self.client.get("/ping").status_code, 200)
        self.assertEqual(self.client.get("/missing").get_json(), {"error": "Not found"})
        self.assertEqual(
            self.client.get("/auth/login").get_json(), {"error": "Method not allowed"}
        )


if __name__ == "__main__":
    unittest.main()
