import click
from flask.cli import with_appcontext
from sqlalchemy import inspect, text

from app import db
from app.models.user import User


def _column_names(table_name):
    return {column["name"] for column in inspect(db.engine).get_columns(table_name)}


@click.command("upgrade-schema")
@with_appcontext
def upgrade_schema():
    """Upgrade the pre-authentication SQLite MVP schema without deleting records."""
    if db.engine.dialect.name != "sqlite":
        raise click.ClickException("upgrade-schema currently supports only the SQLite MVP database")

    tables = set(inspect(db.engine).get_table_names())
    if "supply_requests" in tables and "area_id" not in _column_names("supply_requests"):
        request_count = db.session.execute(
            text("SELECT COUNT(1) FROM supply_requests")
        ).scalar_one()
        if request_count:
            raise click.ClickException(
                "Legacy supply requests need an explicit historical area backfill before upgrading"
            )
        db.session.execute(text(
            "ALTER TABLE supply_requests ADD COLUMN area_id INTEGER REFERENCES areas(area_id)"
        ))

    additive_columns = {
        "users": [
            ("is_active", "BOOLEAN NOT NULL DEFAULT 1"),
        ],
        "attendance_records": [
            ("status", "VARCHAR NOT NULL DEFAULT 'Working'"),
            ("absence_reason", "TEXT"),
        ],
        "snow_log_locations": [
            ("is_active", "BOOLEAN NOT NULL DEFAULT 1"),
        ],
        "assignments": [
            ("destination_area_id", "INTEGER REFERENCES areas(area_id)"),
        ],
    }
    for table_name, columns in additive_columns.items():
        if table_name not in tables:
            continue
        existing_columns = _column_names(table_name)
        for column_name, definition in columns:
            if column_name not in existing_columns:
                db.session.execute(text(
                    f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}"
                ))

    if "supply_requests" in tables:
        db.session.execute(text(
            "UPDATE supply_requests SET status = 'Submitted' "
            "WHERE status IS NULL OR lower(status) = 'pending'"
        ))
    db.session.commit()

    db.create_all()

    legacy_users = User.query.filter_by(password_hash="demo").all()
    for user in legacy_users:
        user.set_password("demo")
    db.session.commit()
    click.echo(
        f"[OK] Schema upgraded; hashed {len(legacy_users)} legacy demo password(s)."
    )


def register_schema_commands(app):
    app.cli.add_command(upgrade_schema)
