import unittest
from datetime import datetime

from app import create_app, db
from app.models import Area, Building, SnowLog, SnowLogLocation, User


class SnowLogApiTestCase(unittest.TestCase):
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
            user = User(
                name="Worker",
                email="worker@example.com",
                role="worker",
                area_id=area.area_id,
            )
            user.set_password("demo")
            coordinator = User(name="Coordinator", email="coordinator@example.com", role="coordinator")
            coordinator.set_password("demo")
            location = SnowLogLocation(area_id=area.area_id, location_name="North Entrance")
            db.session.add_all([user, coordinator, location])
            db.session.commit()
            self.area_id = area.area_id
            self.user_id = user.user_id
            self.location_id = location.snow_log_location_id
        self.login("worker@example.com")

    def login(self, email):
        self.client.post("/auth/login", json={"email": email, "password": "demo"})

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    def test_create_and_list_snow_log(self):
        response = self.client.post("/snow-logs", json={
            "user_id": self.user_id,
            "snow_log_location_id": self.location_id,
            "action_taken": "  Salted walkway  ",
            "condition": "Icy",
        })

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["action_taken"], "Salted walkway")
        self.assertEqual(response.get_json()["area_name"], "Test Area")
        self.assertTrue(response.get_json()["timestamp"].endswith("Z"))

        self.login("coordinator@example.com")
        listed = self.client.get(f"/snow-logs?user_id={self.user_id}")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(len(listed.get_json()), 1)
        self.assertTrue(listed.get_json()[0]["timestamp"].endswith("Z"))

    def test_snow_log_timestamp_is_explicit_utc_in_detail_and_history(self):
        with self.app.app_context():
            log = SnowLog(
                user_id=self.user_id,
                snow_log_location_id=self.location_id,
                timestamp=datetime(2026, 1, 15, 18, 45, 30),
            )
            db.session.add(log)
            db.session.commit()
            log_id = log.snow_log_id

        self.login("coordinator@example.com")
        detail = self.client.get(f"/snow-logs/{log_id}")
        history = self.client.get("/snow-logs")

        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.get_json()["timestamp"], "2026-01-15T18:45:30Z")
        self.assertEqual(history.status_code, 200)
        self.assertEqual(history.get_json()[0]["timestamp"], "2026-01-15T18:45:30Z")

    def test_create_location_and_filter_by_area(self):
        self.login("coordinator@example.com")
        response = self.client.post("/snow-log-locations", json={
            "area_id": self.area_id,
            "location_name": " South Entrance ",
        })

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["location_name"], "South Entrance")
        listed = self.client.get(f"/snow-log-locations?area_id={self.area_id}")
        self.assertEqual(len(listed.get_json()), 2)

    def test_snow_log_validates_foreign_keys_and_text(self):
        response = self.client.post("/snow-logs", json={
            "user_id": 999,
            "snow_log_location_id": self.location_id,
        })
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json(), {"error": "Workers can submit snow logs only for themselves"})

        response = self.client.post("/snow-logs", json={
            "user_id": self.user_id,
            "snow_log_location_id": self.location_id,
            "condition": 42,
        })
        self.assertEqual(response.status_code, 400)
        with self.app.app_context():
            self.assertEqual(SnowLog.query.count(), 0)

    def test_location_validates_area_and_name(self):
        self.login("coordinator@example.com")
        self.assertEqual(self.client.post("/snow-log-locations", json={
            "area_id": 999,
            "location_name": "Entrance",
        }).status_code, 404)
        self.assertEqual(self.client.post("/snow-log-locations", json={
            "area_id": self.area_id,
            "location_name": " ",
        }).status_code, 400)

    def test_invalid_filters_and_missing_records(self):
        self.login("coordinator@example.com")
        self.assertEqual(self.client.get("/snow-logs?user_id=nope").status_code, 400)
        self.assertEqual(self.client.get("/snow-log-locations?area_id=nope").status_code, 400)
        self.assertEqual(self.client.get("/snow-logs/999").status_code, 404)
        self.assertEqual(self.client.get("/snow-log-locations/999").status_code, 404)

    def test_worker_cannot_view_all_logs_or_manage_locations(self):
        self.assertEqual(self.client.get("/snow-logs").status_code, 403)
        self.assertEqual(self.client.post("/snow-log-locations", json={
            "area_id": self.area_id, "location_name": "Other"
        }).status_code, 403)

    def test_coordinator_can_edit_and_deactivate_location(self):
        self.login("coordinator@example.com")
        response = self.client.patch(f"/snow-log-locations/{self.location_id}", json={
            "location_name": "Updated Entrance", "is_active": False
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.get_json()["is_active"])

        self.login("worker@example.com")
        response = self.client.post("/snow-logs", json={
            "snow_log_location_id": self.location_id,
            "condition": "Clear",
        })
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
