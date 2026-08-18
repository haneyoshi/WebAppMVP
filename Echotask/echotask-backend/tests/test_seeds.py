from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from app import create_app, db
from app.models import (
    Area,
    Assignment,
    AttendanceRecord,
    Building,
    Event,
    SnowLog,
    SnowLogLocation,
    SupplyItem,
    SupplyRequest,
    SupplyRequestItem,
    User,
)
from app.time_utils import utc_now


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

    def _portfolio_app(self):
        temporary_directory = TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        portfolio_path = (
            Path(temporary_directory.name) / "instance" / "echotask-portfolio.db"
        )
        portfolio_path.parent.mkdir()
        app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{portfolio_path.as_posix()}",
        })

        def dispose_app():
            with app.app_context():
                db.session.remove()
                db.engine.dispose()

        self.addCleanup(dispose_app)
        runner = app.test_cli_runner()
        result = runner.invoke(args=["seed-core-data"])
        self.assertEqual(result.exit_code, 0, result.output)
        result = runner.invoke(args=[
            "seed-supplies", "--csv-path", "Supply_Item_List.csv"
        ])
        self.assertEqual(result.exit_code, 0, result.output)
        return app, runner, portfolio_path.resolve()

    def test_core_data_seed_loads_canonical_accounts_and_snow_locations(self):
        result = self.app.test_cli_runner().invoke(args=["seed-core-data"])

        self.assertEqual(result.exit_code, 0, result.output)
        with self.app.app_context():
            self.assertEqual(Building.query.count(), 10)
            self.assertEqual(Area.query.count(), 22)
            self.assertEqual(User.query.count(), 24)
            self.assertEqual(
                [building.building_name for building in Building.query.order_by(Building.building_id)],
                [
                    "Physical Plant", "Agriculture Building", "Tache Hall",
                    "Art Lab", "Tier Building", "Isbister Building",
                    "Fletcher Argue", "Elizabeth Dafoe Library",
                    "Administration Building", "Drake",
                ],
            )
            self.assertEqual(
                [area.area_name for area in Area.query.order_by(Area.area_id)],
                [
                    "Physical Plant Main", "Plant Science Upper",
                    "Plant Science Lower and Art Barn", "Tache West Lower",
                    "Tache West Upper", "Tache East Lower", "Tache East Upper",
                    "Art Lab Upper and Basement", "Art Lab Lower", "Tier Lower",
                    "Tier Upper", "Isbister Lower", "Isbister Upper",
                    "Fletcher Argue Main", "Library 1st Floor",
                    "Library 2nd Floor", "Library 3rd Floor",
                    "Administration Main", "Drake Basement", "Drake First Floor",
                    "Drake Second Floor", "Drake Upper Floors",
                ],
            )
            self.assertEqual(
                [user.name for user in User.query.filter_by(role="worker").order_by(User.user_id)],
                [
                    "Bryan", "Dora", "Alex", "Gabriel", "Jennifer", "Natalie",
                    "Alexia", "Diane", "Pam", "Emely", "Priamo", "Ken", "Yang",
                    "Moo", "Patricia", "Ein", "Glend", "Christ", "Yoa", "Rosana",
                    "Mit", "John",
                ],
            )
            self.assertEqual(
                [(user.email, user.role) for user in User.query.order_by(User.user_id)],
                [(f"user{i}@example.com", "worker") for i in range(1, 23)] + [
                    ("bob@example.com", "coordinator"),
                    ("sara@example.com", "supervisor"),
                ],
            )
            user = db.session.get(User, 1)
            self.assertNotEqual(user.password_hash, "demo")
            self.assertTrue(user.check_password("demo"))
            self.assertEqual(user.area_id, 1)
            self.assertTrue(all(user.check_password("demo") for user in User.query.all()))
            self.assertEqual(
                [
                    (location.area_id, location.location_name, location.is_active)
                    for location in SnowLogLocation.query.order_by(
                        SnowLogLocation.snow_log_location_id
                    )
                ],
                [
                    (1, "Physical Plant Entrances and Walkways", True),
                    (2, "Plant Science Staff Entrance Walkway", True),
                    (3, "Art Barn Loading Area", True),
                ],
            )

        login = self.client.post("/auth/login", json={
            "email": "user1@example.com", "password": "demo"
        })
        self.assertEqual(login.status_code, 200)
        supervisor_login = self.client.post("/auth/login", json={
            "email": "sara@example.com", "password": "demo"
        })
        self.assertEqual(supervisor_login.status_code, 200)
        self.assertEqual(supervisor_login.get_json()["role"], "supervisor")

    def test_core_data_seed_is_repeatable_and_resets_core_data(self):
        runner = self.app.test_cli_runner()
        first_result = runner.invoke(args=["seed-core-data"])
        self.assertEqual(first_result.exit_code, 0, first_result.output)

        with self.app.app_context():
            db.session.add(SnowLogLocation(
                area_id=1,
                location_name="Temporary Location",
                is_active=False,
            ))
            db.session.add(SupplyItem(
                item_name="Existing Supply Item",
                category="Test Supplies",
            ))
            temporary_user = User(
                name="Temporary Worker",
                email="temporary@example.com",
                role="worker",
                area_id=None,
            )
            temporary_user.set_password("temporary")
            db.session.add(temporary_user)
            db.session.commit()

        second_result = runner.invoke(args=["seed-core-data"])
        self.assertEqual(second_result.exit_code, 0, second_result.output)

        with self.app.app_context():
            self.assertEqual(Building.query.count(), 10)
            self.assertEqual(Area.query.count(), 22)
            self.assertEqual(User.query.count(), 24)
            self.assertEqual(SnowLogLocation.query.count(), 3)
            self.assertEqual(SupplyItem.query.count(), 1)
            self.assertIsNone(User.query.filter_by(email="temporary@example.com").first())
            self.assertIsNone(
                SnowLogLocation.query.filter_by(location_name="Temporary Location").first()
            )

    def test_portfolio_demo_day_refuses_non_portfolio_database(self):
        result = self.app.test_cli_runner().invoke(
            args=["seed-portfolio-demo-day"]
        )

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("resolved database is not", result.output)

    def test_portfolio_preflight_failure_preserves_operational_data(self):
        app, runner, portfolio_path = self._portfolio_app()
        with app.app_context():
            bob = User.query.filter_by(name="Bob Coordinator").one()
            bryan = User.query.filter_by(name="Bryan").one()
            db.session.add(AttendanceRecord(
                user_id=bryan.user_id,
                attendance_date=date.today(),
                present=True,
                status="Working",
                marked_by_user_id=bob.user_id,
            ))
            SupplyItem.query.filter_by(item_name="Demo Hand Soap").delete()
            db.session.commit()

        with patch("seeds.PORTFOLIO_DATABASE_PATH", portfolio_path):
            result = runner.invoke(args=["seed-portfolio-demo-day"])

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("missing supply items: Demo Hand Soap", result.output)
        with app.app_context():
            self.assertEqual(AttendanceRecord.query.count(), 1)

    def test_portfolio_demo_day_is_exact_relative_and_repeatable(self):
        app, runner, portfolio_path = self._portfolio_app()
        with app.app_context():
            canonical_before = {
                "buildings": [(row.building_id, row.building_name) for row in Building.query.all()],
                "areas": [
                    (row.area_id, row.area_name, row.description, row.building_id)
                    for row in Area.query.all()
                ],
                "users": [
                    (
                        row.user_id, row.name, row.email, row.role, row.area_id,
                        row.password_hash, row.is_active,
                    )
                    for row in User.query.all()
                ],
                "locations": [
                    (
                        row.snow_log_location_id, row.area_id,
                        row.location_name, row.is_active,
                    )
                    for row in SnowLogLocation.query.all()
                ],
                "supplies": [
                    (row.item_id, row.item_name, row.category)
                    for row in SupplyItem.query.all()
                ],
            }

        before = utc_now()
        with patch("seeds.PORTFOLIO_DATABASE_PATH", portfolio_path):
            first = runner.invoke(args=["seed-portfolio-demo-day"])
        after = utc_now()
        self.assertEqual(first.exit_code, 0, first.output)

        with app.app_context():
            self.assertEqual(AttendanceRecord.query.count(), 22)
            self.assertEqual(Assignment.query.count(), 1)
            self.assertEqual(Event.query.count(), 1)
            self.assertEqual(SupplyRequest.query.count(), 2)
            self.assertEqual(SupplyRequestItem.query.count(), 4)
            self.assertEqual(SnowLog.query.count(), 3)

            attendance = AttendanceRecord.query.all()
            self.assertEqual(Counter(row.status for row in attendance), {
                "Working": 19,
                "Away": 3,
            })
            self.assertEqual({row.attendance_date for row in attendance}, {date.today()})
            self.assertTrue(all(row.absence_reason is None for row in attendance))
            bob = User.query.filter_by(name="Bob Coordinator").one()
            self.assertTrue(all(row.marked_by_user_id == bob.user_id for row in attendance))
            away_names = {row.user.name for row in attendance if row.status == "Away"}
            self.assertEqual(away_names, {
                "Gabriel", "Emely", "Christ",
            })

            bryan = User.query.filter_by(name="Bryan").one()
            bryan_attendance = AttendanceRecord.query.filter_by(
                user_id=bryan.user_id
            ).one()
            self.assertEqual(bryan_attendance.status, "Working")
            assignment = Assignment.query.one()
            self.assertEqual(assignment.assignment_date, date.today())
            self.assertEqual(assignment.assignment_type, "Coverage")
            self.assertEqual(assignment.location_task, "Tache West Lower coverage")
            self.assertEqual(assignment.note, "Morning coverage")
            self.assertEqual(assignment.destination_area.area_name, "Tache West Lower")
            self.assertEqual([worker.name for worker in assignment.workers], ["Bryan"])
            self.assertEqual(assignment.created_by_user_id, bob.user_id)

            event = Event.query.one()
            self.assertEqual(event.building.building_name, "Tache Hall")
            self.assertEqual(event.title, "Tache Hall Floor Care Coordination")
            self.assertEqual(event.created_by_user_id, bob.user_id)
            self.assertTrue(before + timedelta(minutes=15) <= event.start_time <= after + timedelta(minutes=15))
            self.assertTrue(before + timedelta(minutes=75) <= event.end_time <= after + timedelta(minutes=75))

            requests_by_status = {
                request.status: request for request in SupplyRequest.query.all()
            }
            submitted = requests_by_status["Submitted"]
            self.assertEqual((submitted.user.name, submitted.area.area_name), (
                "Jennifer", "Tache West Upper",
            ))
            self.assertEqual(
                {line.item.item_name: line.quantity for line in submitted.items},
                {"Demo Floor Cleaner": 2, "Demo Microfiber Cloth": 6},
            )
            completed = requests_by_status["Completed"]
            self.assertEqual((completed.user.name, completed.area.area_name), (
                "Dora", "Plant Science Upper",
            ))
            self.assertEqual(
                {line.item.item_name: line.quantity for line in completed.items},
                {"Demo Paper Towels": 4, "Demo Hand Soap": 2},
            )

            logs_by_worker = {log.user.name: log for log in SnowLog.query.all()}
            self.assertEqual(set(logs_by_worker), {
                "Bryan", "Dora", "Alex",
            })
            self.assertEqual(
                logs_by_worker["Bryan"].location.location_name,
                "Physical Plant Entrances and Walkways",
            )
            self.assertEqual(
                logs_by_worker["Dora"].location.location_name,
                "Plant Science Staff Entrance Walkway",
            )
            self.assertEqual(
                logs_by_worker["Alex"].location.location_name,
                "Art Barn Loading Area",
            )
            expected_minutes = {"Bryan": 90, "Dora": 60, "Alex": 30}
            for worker_name, minutes in expected_minutes.items():
                timestamp = logs_by_worker[worker_name].timestamp
                self.assertTrue(
                    before - timedelta(minutes=minutes) <= timestamp <=
                    after - timedelta(minutes=minutes)
                )

            canonical_after = {
                "buildings": [(row.building_id, row.building_name) for row in Building.query.all()],
                "areas": [
                    (row.area_id, row.area_name, row.description, row.building_id)
                    for row in Area.query.all()
                ],
                "users": [
                    (
                        row.user_id, row.name, row.email, row.role, row.area_id,
                        row.password_hash, row.is_active,
                    )
                    for row in User.query.all()
                ],
                "locations": [
                    (
                        row.snow_log_location_id, row.area_id,
                        row.location_name, row.is_active,
                    )
                    for row in SnowLogLocation.query.all()
                ],
                "supplies": [
                    (row.item_id, row.item_name, row.category)
                    for row in SupplyItem.query.all()
                ],
            }
            self.assertEqual(canonical_after, canonical_before)

        client = app.test_client()
        login = client.post("/auth/login", json={
            "email": "bob@example.com", "password": "demo",
        })
        self.assertEqual(login.status_code, 200)
        availability = client.get(
            f"/workers/availability?date={date.today().isoformat()}"
        )
        self.assertEqual(availability.status_code, 200)
        self.assertEqual(Counter(row["status"] for row in availability.get_json()), {
            "Working": 18,
            "Away": 3,
            "Assigned elsewhere": 1,
        })

        with patch("seeds.PORTFOLIO_DATABASE_PATH", portfolio_path):
            second = runner.invoke(args=["seed-portfolio-demo-day"])
        self.assertEqual(second.exit_code, 0, second.output)
        with app.app_context():
            self.assertEqual(AttendanceRecord.query.count(), 22)
            self.assertEqual(Assignment.query.count(), 1)
            self.assertEqual(Event.query.count(), 1)
            self.assertEqual(SupplyRequest.query.count(), 2)
            self.assertEqual(SupplyRequestItem.query.count(), 4)
            self.assertEqual(SnowLog.query.count(), 3)


if __name__ == "__main__":
    unittest.main()
