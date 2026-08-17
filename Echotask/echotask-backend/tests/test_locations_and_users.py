import unittest

from app import create_app, db
from app.models import Area, Building, User


class LocationAndUserApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        })
        self.client = self.app.test_client()

        with self.app.app_context():
            first_building = Building(building_name="Alpha Building")
            second_building = Building(building_name="Beta Building")
            db.create_all()
            db.session.add_all([first_building, second_building])
            db.session.flush()
            assigned_area = Area(
                area_name="Assigned Area",
                building_id=first_building.building_id,
                description="Main floor",
            )
            other_area = Area(
                area_name="Other Area",
                building_id=second_building.building_id,
            )
            db.session.add_all([assigned_area, other_area])
            db.session.flush()
            user = User(
                name="Worker One",
                email="worker@example.com",
                role="worker",
                area_id=assigned_area.area_id,
            )
            user.set_password("demo")
            db.session.add(user)
            db.session.commit()
            self.first_building_id = first_building.building_id
            self.assigned_area_id = assigned_area.area_id
            self.user_id = user.user_id
        self.client.post("/auth/login", json={
            "email": "worker@example.com", "password": "demo"
        })

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    def test_list_buildings_includes_area_counts(self):
        response = self.client.get("/buildings")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()[0]["building_name"], "Alpha Building")
        self.assertEqual(response.get_json()[0]["area_count"], 1)

    def test_get_building_includes_nested_areas(self):
        response = self.client.get(f"/buildings/{self.first_building_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["areas"][0]["area_id"], self.assigned_area_id)
        self.assertEqual(response.get_json()["areas"][0]["assigned_user_id"], self.user_id)

    def test_filter_areas_by_building(self):
        response = self.client.get(f"/areas?building_id={self.first_building_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()), 1)
        self.assertEqual(response.get_json()[0]["area_name"], "Assigned Area")

    def test_area_filter_rejects_invalid_building_id(self):
        response = self.client.get("/areas?building_id=not-a-number")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {"error": "building_id must be an integer"})

    def test_get_user_includes_area_details_without_password(self):
        response = self.client.get(f"/users/{self.user_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["area_name"], "Assigned Area")
        self.assertNotIn("password_hash", response.get_json())

    def test_missing_location_and_user_return_404(self):
        self.assertEqual(self.client.get("/buildings/999").status_code, 404)
        self.assertEqual(self.client.get("/areas/999").status_code, 404)
        self.assertEqual(self.client.get("/users/999").status_code, 404)

    def test_location_endpoints_require_authentication(self):
        self.client.post("/auth/logout")
        self.assertEqual(self.client.get("/buildings").status_code, 401)
        self.assertEqual(self.client.get("/areas").status_code, 401)


if __name__ == "__main__":
    unittest.main()
