import unittest

from app import create_app, db
from app.models import Building, Event, User


class EventApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        })
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            building = Building(building_name="Event Building")
            creator = User(
                name="Coordinator",
                email="coordinator@example.com",
                role="coordinator",
            )
            creator.set_password("demo")
            worker = User(name="Worker", email="worker@example.com", role="worker")
            worker.set_password("demo")
            db.session.add_all([building, creator, worker])
            db.session.commit()
            self.building_id = building.building_id
            self.creator_id = creator.user_id
        self.login("coordinator@example.com")

    def login(self, email):
        self.client.post("/auth/login", json={"email": email, "password": "demo"})

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    def _valid_payload(self):
        return {
            "building_id": self.building_id,
            "title": "Staff Meeting",
            "description": "Weekly coordination",
            "start_time": "2026-08-01T09:00:00-05:00",
            "end_time": "2026-08-01T10:00:00-05:00",
            "created_by_user_id": self.creator_id,
        }

    def test_create_get_and_filter_events(self):
        response = self.client.post("/events", json=self._valid_payload())

        self.assertEqual(response.status_code, 201)
        body = response.get_json()
        self.assertEqual(body["title"], "Staff Meeting")
        self.assertEqual(body["start_time"], "2026-08-01T14:00:00")

        event_id = body["event_id"]
        self.assertEqual(self.client.get(f"/events/{event_id}").status_code, 200)
        listed = self.client.get(f"/events?building_id={self.building_id}")
        self.assertEqual(len(listed.get_json()), 1)

    def test_event_rejects_invalid_time_range(self):
        payload = self._valid_payload()
        payload["end_time"] = payload["start_time"]

        response = self.client.post("/events", json=payload)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {"error": "end_time must be after start_time"})
        with self.app.app_context():
            self.assertEqual(Event.query.count(), 0)

    def test_event_validates_datetime_and_required_text(self):
        payload = self._valid_payload()
        payload["start_time"] = "not-a-date"
        self.assertEqual(self.client.post("/events", json=payload).status_code, 400)

        payload = self._valid_payload()
        payload["title"] = " "
        self.assertEqual(self.client.post("/events", json=payload).status_code, 400)

    def test_event_validates_foreign_keys(self):
        payload = self._valid_payload()
        payload["building_id"] = 999
        self.assertEqual(self.client.post("/events", json=payload).status_code, 404)

        payload = self._valid_payload()
        payload["created_by_user_id"] = 999
        self.assertEqual(self.client.post("/events", json=payload).status_code, 403)

    def test_event_invalid_filter_and_missing_record(self):
        self.assertEqual(self.client.get("/events?building_id=nope").status_code, 400)
        self.assertEqual(self.client.get("/events/999").status_code, 404)

    def test_coordinator_can_edit_and_delete_event(self):
        event_id = self.client.post("/events", json=self._valid_payload()).get_json()["event_id"]
        updated = self.client.patch(f"/events/{event_id}", json={"title": "Updated"})
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.get_json()["title"], "Updated")
        self.assertEqual(self.client.delete(f"/events/{event_id}").status_code, 200)
        self.assertEqual(self.client.get(f"/events/{event_id}").status_code, 404)

    def test_worker_can_view_but_not_manage_events(self):
        self.login("worker@example.com")
        self.assertEqual(self.client.get("/events").status_code, 200)
        self.assertEqual(self.client.post("/events", json=self._valid_payload()).status_code, 403)

    def test_events_require_authentication(self):
        self.client.post("/auth/logout")
        self.assertEqual(self.client.get("/events").status_code, 401)


if __name__ == "__main__":
    unittest.main()
