import unittest

from app import create_app, db
from app.models import Area, Building, SupplyItem, SupplyRequest, User


class SupplyRequestApiTestCase(unittest.TestCase):
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
            first_area = Area(area_name="First Area", building_id=building.building_id)
            second_area = Area(area_name="Second Area", building_id=building.building_id)
            db.session.add_all([first_area, second_area])
            db.session.flush()
            user = User(
                name="Test Worker",
                email="worker@example.com",
                role="worker",
                area_id=first_area.area_id,
            )
            user.set_password("demo")
            coordinator = User(name="Coordinator", email="coordinator@example.com", role="coordinator")
            coordinator.set_password("demo")
            supervisor = User(name="Supervisor", email="supervisor@example.com", role="supervisor")
            supervisor.set_password("demo")
            item = SupplyItem(item_name="Paper Towels", category="Paper")
            db.session.add_all([user, coordinator, supervisor, item])
            db.session.commit()
            self.user_id = user.user_id
            self.first_area_id = first_area.area_id
            self.second_area_id = second_area.area_id
            self.item_id = item.item_id
        self.login("worker@example.com")

    def login(self, email):
        return self.client.post("/auth/login", json={"email": email, "password": "demo"})

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    def test_create_request_persists_submitted_area(self):
        response = self.client.post(
            "/supplies/requests",
            json={
                "submitted_by_user_id": self.user_id,
                "area_id": self.first_area_id,
                "items": [{"item_id": self.item_id, "quantity": 2}],
            },
        )

        self.assertEqual(response.status_code, 201)
        request_id = response.get_json()["supply_request_id"]

        with self.app.app_context():
            supply_request = db.session.get(SupplyRequest, request_id)
            self.assertEqual(supply_request.area_id, self.first_area_id)
            user = db.session.get(User, self.user_id)
            user.area_id = self.second_area_id
            db.session.commit()

        self.login("coordinator@example.com")
        listed_request = self.client.get("/supplies/requests").get_json()[0]
        self.assertEqual(listed_request["area_id"], self.first_area_id)
        self.assertEqual(listed_request["area_name"], "First Area")

    def test_create_request_rejects_unknown_area(self):
        response = self.client.post(
            "/supplies/requests",
            json={
                "submitted_by_user_id": self.user_id,
                "area_id": 999,
                "items": [{"item_id": self.item_id, "quantity": 1}],
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json(), {"error": "area_id not found"})
        with self.app.app_context():
            self.assertEqual(SupplyRequest.query.count(), 0)

    def test_create_request_validates_all_items_before_writing(self):
        response = self.client.post(
            "/supplies/requests",
            json={
                "submitted_by_user_id": self.user_id,
                "area_id": self.first_area_id,
                "items": [
                    {"item_id": self.item_id, "quantity": 1},
                    {"item_id": self.item_id, "quantity": 0},
                ],
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {"error": "quantity must be a positive integer"})
        with self.app.app_context():
            self.assertEqual(SupplyRequest.query.count(), 0)

    def test_create_request_rejects_boolean_quantity(self):
        response = self.client.post(
            "/supplies/requests",
            json={
                "submitted_by_user_id": self.user_id,
                "area_id": self.first_area_id,
                "items": [{"item_id": self.item_id, "quantity": True}],
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {"error": "quantity must be a positive integer"})

    def test_list_items_uses_model_category_field(self):
        response = self.client.get("/supplies/items")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()[0]["category"], "Paper")

    def test_sample_request_seed_uses_persisted_area(self):
        self.client.post("/auth/logout")
        result = self.app.test_cli_runner().invoke(args=["seed-sample-request"])

        self.assertEqual(result.exit_code, 0, result.output)
        with self.app.app_context():
            supply_request = SupplyRequest.query.one()
            self.assertEqual(supply_request.user_id, self.user_id)
            self.assertEqual(supply_request.area_id, self.first_area_id)
            self.assertEqual(len(supply_request.items), 1)

    def test_worker_cannot_submit_for_another_area_or_user(self):
        response = self.client.post("/supplies/requests", json={
            "area_id": self.second_area_id,
            "items": [{"item_id": self.item_id, "quantity": 1}],
        })
        self.assertEqual(response.status_code, 403)

        response = self.client.post("/supplies/requests", json={
            "submitted_by_user_id": 999,
            "area_id": self.first_area_id,
            "items": [{"item_id": self.item_id, "quantity": 1}],
        })
        self.assertEqual(response.status_code, 403)

    def test_supervisor_processes_request_and_summary_is_restricted(self):
        created = self.client.post("/supplies/requests", json={
            "area_id": self.first_area_id,
            "items": [{"item_id": self.item_id, "quantity": 3}],
        }).get_json()
        self.assertEqual(self.client.get("/supplies/requests/summary/items").status_code, 403)

        self.login("supervisor@example.com")
        response = self.client.patch(
            f"/supplies/requests/{created['supply_request_id']}/status",
            json={"status": "Completed"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "Completed")
        self.assertEqual(self.client.get("/supplies/requests/summary/items").status_code, 200)

    def test_supply_endpoints_require_authentication(self):
        self.client.post("/auth/logout")
        self.assertEqual(self.client.get("/supplies/items").status_code, 401)
        self.assertEqual(self.client.get("/supplies/requests").status_code, 401)


if __name__ == "__main__":
    unittest.main()
