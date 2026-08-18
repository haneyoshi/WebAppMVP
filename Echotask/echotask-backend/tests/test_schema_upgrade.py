import sqlite3
import tempfile
import unittest
from pathlib import Path

from sqlalchemy import inspect, text

from app import create_app, db
from app.models import User


class SchemaUpgradeTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "legacy.db"
        connection = sqlite3.connect(self.db_path)
        connection.executescript("""
            CREATE TABLE buildings (
                building_id INTEGER PRIMARY KEY,
                building_name VARCHAR NOT NULL,
                created_at DATETIME
            );
            CREATE TABLE areas (
                area_id INTEGER PRIMARY KEY,
                area_name VARCHAR NOT NULL,
                description TEXT,
                building_id INTEGER NOT NULL REFERENCES buildings(building_id),
                created_at DATETIME
            );
            CREATE TABLE users (
                user_id INTEGER PRIMARY KEY,
                name VARCHAR NOT NULL,
                email VARCHAR NOT NULL UNIQUE,
                password_hash VARCHAR NOT NULL,
                role VARCHAR NOT NULL,
                area_id INTEGER UNIQUE REFERENCES areas(area_id),
                created_at DATETIME
            );
            CREATE TABLE supply_requests (
                request_id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(user_id),
                request_date DATETIME,
                status VARCHAR
            );
            CREATE TABLE assignments (
                assignment_id INTEGER PRIMARY KEY,
                assignment_date DATE NOT NULL,
                assignment_type VARCHAR NOT NULL,
                location_task VARCHAR NOT NULL,
                note TEXT,
                created_by_user_id INTEGER NOT NULL REFERENCES users(user_id),
                created_at DATETIME
            );
            INSERT INTO buildings VALUES (1, 'Building', NULL);
            INSERT INTO areas VALUES (1, 'Area', NULL, 1, NULL);
            INSERT INTO users VALUES (
                1, 'Worker', 'worker@example.com', 'demo', 'worker', 1, NULL
            );
            INSERT INTO assignments VALUES (
                1, '2026-08-17', 'Coverage', 'North entrance', NULL, 1, NULL
            );
        """)
        connection.commit()
        connection.close()
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{self.db_path.as_posix()}",
        })

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()
        self.temp_dir.cleanup()

    def test_upgrade_adds_schema_and_hashes_only_legacy_demo_password(self):
        result = self.app.test_cli_runner().invoke(args=["upgrade-schema"])

        self.assertEqual(result.exit_code, 0, result.output)
        with self.app.app_context():
            inspector = inspect(db.engine)
            self.assertIn("is_active", {
                column["name"] for column in inspector.get_columns("users")
            })
            self.assertIn("area_id", {
                column["name"] for column in inspector.get_columns("supply_requests")
            })
            self.assertIn("assignments", inspector.get_table_names())
            self.assertIn("destination_area_id", {
                column["name"] for column in inspector.get_columns("assignments")
            })
            destination_area_id = db.session.execute(
                text("SELECT destination_area_id FROM assignments WHERE assignment_id = 1")
            ).scalar_one()
            self.assertIsNone(destination_area_id)
            user = db.session.get(User, 1)
            self.assertNotEqual(user.password_hash, "demo")
            self.assertTrue(user.check_password("demo"))


if __name__ == "__main__":
    unittest.main()
