# echotask-backend/seeds.py

from datetime import date, timedelta

from flask.cli import with_appcontext
import click, csv, os
from pathlib import Path
from app.time_utils import utc_now

from app import db
from app.models.user import User
from app.models.area import Area
from app.models.building import Building
from app.models.supply_item import SupplyItem
from app.models.supply_request import SupplyRequest
from app.models.supply_request_item import SupplyRequestItem
from app.models.snow_log_location import SnowLogLocation


PORTFOLIO_DATABASE_PATH = (
    Path(__file__).resolve().parent / "instance" / "echotask-portfolio.db"
).resolve()

PORTFOLIO_SUPPLY_ITEMS = {
    "Demo Floor Cleaner",
    "Demo Microfiber Cloth",
    "Demo Paper Towels",
    "Demo Hand Soap",
}

# ***** To run seeds.py *****
# flask db upgrade     or your migration init step
# Canonical fresh-demo reset:
# flask seed-core-data
# flask seed-supplies --csv-path Supply_Item_List.csv



# ---- 1) Supplies from CSV (Category,Product) -> supply_items.item_name
@click.command("seed-supplies")
# ->Decorator, "Click" syntax (Click is a Python library used by Flask for terminal commands)
# ->It turns the function below into a terminal command(in this case, "flask seed-supplies").

@click.option("--csv-path", default="supply_Item_List.csv", show_default=True,
              help="Path to CSV with headers Category,Product")
# ->optional argument for the terminal command
@with_appcontext
# -> the most important line => when this command runs, Flask will load the app context so your code can use "db", "model queries", and "app config (like database URI)"
# -> in short, it connects this command to your Flask app environment.


def seed_supplies(csv_path):
    # -> receive the argument
    if not os.path.exists(csv_path):
        click.echo(f"[ERR] CSV not found: {csv_path}")
        # -> prints a message to terminal (like print(), but click-style)
        raise SystemExit(1)
        # -> stops immediately with “error exit code = 1”.

    created = skipped = 0
    with open(csv_path, newline="", encoding="utf-8") as f:
        # ->with open(...) as f: means Python will automatically close the file after this block.
        reader = csv.DictReader(f)
        # -> This makes each row a dict => {"Category": "PAPER PRODUCTS", "Product": "SWISH CLEAN & GREEN® HAND TOWEL..."}
        for row in reader:
            name = (row.get("Product") or "").strip()
            category = (row.get("Category") or "").strip()
            if not name or not category:
                skipped += 1
                continue
                # -> skip and go next row
            if SupplyItem.query.filter_by(item_name=name).first():
            # -> Avoid duplicates
                skipped += 1
                continue
            db.session.add(SupplyItem(
                item_name=name,
                category=category,
                created_at=utc_now(),
            ))
            created += 1
    db.session.commit()
    click.echo(f"[OK] Supplies import complete. created={created}, skipped={skipped}")

# ---- 2) Tiny smoke test: make one request using the first 2 items
@click.command("seed-sample-request")
@with_appcontext
def seed_sample_request():
    worker = User.query.filter_by(role="worker").first()
    area = Area.query.first()
    items = SupplyItem.query.order_by(SupplyItem.item_name.asc()).limit(2).all()
    if not (worker and area and len(items) >= 1):
        click.echo("[ERR] Need at least 1 worker, 1 area, and 1 supply_item. Run the documented demo seed sequence first.")
        raise SystemExit(1)

    req = SupplyRequest(user_id=worker.user_id, area_id=area.area_id, request_date=utc_now())
    db.session.add(req); db.session.flush()
    for it in items:
        db.session.add(SupplyRequestItem(request_id=req.request_id, item_id=it.item_id, quantity=1))
    db.session.commit()
    click.echo(f"[OK] Created sample request supply_request_id={req.request_id}")


def _require_portfolio_database():
    database_name = db.engine.url.database
    if not database_name or db.engine.url.get_backend_name() != "sqlite":
        raise click.ClickException(
            "seed-portfolio-demo-day requires the SQLite portfolio database"
        )

    resolved_database = Path(database_name).resolve()
    if resolved_database != PORTFOLIO_DATABASE_PATH:
        raise click.ClickException(
            "Refusing to refresh demo data: resolved database is not "
            f"{PORTFOLIO_DATABASE_PATH}"
        )
    return resolved_database


def _require_exact_rows(model, expected_by_id, value_getter, entity_name):
    actual_by_id = {
        row_id: value_getter(row)
        for row in model.query.all()
        for row_id in [getattr(row, next(iter(model.__table__.primary_key.columns)).name)]
    }
    if actual_by_id != expected_by_id:
        raise click.ClickException(
            f"Portfolio preflight failed: canonical {entity_name} do not match"
        )


def _preflight_portfolio_demo_data():
    backend_dir = Path(__file__).resolve().parent
    with (backend_dir / "data" / "buildings.csv").open(
        newline="", encoding="utf-8"
    ) as source:
        expected_buildings = {
            int(row["building_id"]): row["building_name"]
            for row in csv.DictReader(source)
        }
    _require_exact_rows(
        Building,
        expected_buildings,
        lambda building: building.building_name,
        "buildings",
    )

    with (backend_dir / "data" / "areas.csv").open(
        newline="", encoding="utf-8"
    ) as source:
        area_rows = list(csv.DictReader(source))
    expected_areas = {
        int(row["area_id"]): (
            row["area_name"],
            row["description"],
            int(row["building_id"]),
            int(row["assigned_user_id"]),
        )
        for row in area_rows
    }
    _require_exact_rows(
        Area,
        expected_areas,
        lambda area: (
            area.area_name,
            area.description,
            area.building_id,
            area.user.user_id if area.user else None,
        ),
        "areas",
    )

    area_by_user = {
        int(row["assigned_user_id"]): int(row["area_id"])
        for row in area_rows
        if row.get("assigned_user_id")
    }
    with (backend_dir / "data" / "users.csv").open(
        newline="", encoding="utf-8"
    ) as source:
        expected_users = {
            int(row["user_id"]): (
                row["user_name"],
                f"user{int(row['user_id'])}@example.com",
                row["role"],
                area_by_user[int(row["user_id"])],
            )
            for row in csv.DictReader(source)
        }
    expected_users.update({
        23: ("Bob Coordinator", "bob@example.com", "coordinator", None),
        24: ("Sara Supervisor", "sara@example.com", "supervisor", None),
    })
    _require_exact_rows(
        User,
        expected_users,
        lambda user: (user.name, user.email, user.role, user.area_id),
        "users",
    )

    expected_locations = {
        1: (1, "Physical Plant Entrances and Walkways", True),
        2: (2, "Plant Science Staff Entrance Walkway", True),
        3: (3, "Art Barn Loading Area", True),
    }
    _require_exact_rows(
        SnowLogLocation,
        expected_locations,
        lambda location: (location.area_id, location.location_name, location.is_active),
        "Snow Log locations",
    )

    items_by_name = {
        item.item_name: item for item in SupplyItem.query.filter(
            SupplyItem.item_name.in_(PORTFOLIO_SUPPLY_ITEMS)
        ).all()
    }
    missing_items = sorted(PORTFOLIO_SUPPLY_ITEMS - items_by_name.keys())
    if missing_items:
        raise click.ClickException(
            "Portfolio preflight failed: missing supply items: "
            + ", ".join(missing_items)
        )
    return items_by_name


@click.command("seed-portfolio-demo-day")
@with_appcontext
def seed_portfolio_demo_day():
    resolved_database = _require_portfolio_database()
    items_by_name = _preflight_portfolio_demo_data()

    from app.models import (
        Assignment,
        AttendanceRecord,
        Event,
        SnowLog,
        SupplyRequest,
        assignment_workers,
    )

    now = utc_now()
    today = date.today()
    users_by_name = {user.name: user for user in User.query.all()}
    areas_by_name = {area.area_name: area for area in Area.query.all()}
    buildings_by_name = {
        building.building_name: building for building in Building.query.all()
    }
    locations_by_name = {
        location.location_name: location for location in SnowLogLocation.query.all()
    }

    try:
        SupplyRequestItem.query.delete()
        SupplyRequest.query.delete()
        db.session.execute(assignment_workers.delete())
        Assignment.query.delete()
        Event.query.delete()
        AttendanceRecord.query.delete()
        SnowLog.query.delete()

        bob = users_by_name["Bob Coordinator"]
        away_names = {"Gabriel", "Emely", "Christ"}
        workers = User.query.filter_by(role="worker").order_by(User.user_id).all()
        db.session.add_all([
            AttendanceRecord(
                user_id=worker.user_id,
                attendance_date=today,
                present=worker.name not in away_names,
                status="Away" if worker.name in away_names else "Working",
                absence_reason=None,
                marked_by_user_id=bob.user_id,
                marked_at=now,
            )
            for worker in workers
        ])

        assignment = Assignment(
            assignment_date=today,
            assignment_type="Coverage",
            location_task="Tache West Lower coverage",
            note="Morning coverage",
            destination_area_id=areas_by_name["Tache West Lower"].area_id,
            created_by_user_id=bob.user_id,
            created_at=now,
        )
        assignment.workers = [users_by_name["Bryan"]]
        db.session.add(assignment)

        db.session.add(Event(
            building_id=buildings_by_name["Tache Hall"].building_id,
            title="Tache Hall Floor Care Coordination",
            description=(
                "Coordinate evening floor-care access and temporary area coverage."
            ),
            start_time=now + timedelta(minutes=15),
            end_time=now + timedelta(minutes=75),
            created_by_user_id=bob.user_id,
        ))

        request_specs = [
            (
                "Jennifer",
                "Tache West Upper",
                "Submitted",
                now - timedelta(minutes=45),
                (("Demo Floor Cleaner", 2), ("Demo Microfiber Cloth", 6)),
            ),
            (
                "Dora",
                "Plant Science Upper",
                "Completed",
                now - timedelta(hours=2),
                (("Demo Paper Towels", 4), ("Demo Hand Soap", 2)),
            ),
        ]
        for worker_name, area_name, status, request_date, item_specs in request_specs:
            supply_request = SupplyRequest(
                user_id=users_by_name[worker_name].user_id,
                area_id=areas_by_name[area_name].area_id,
                request_date=request_date,
                status=status,
            )
            for item_name, quantity in item_specs:
                supply_request.items.append(SupplyRequestItem(
                    item_id=items_by_name[item_name].item_id,
                    quantity=quantity,
                ))
            db.session.add(supply_request)

        snow_log_specs = [
            (
                "Bryan",
                "Physical Plant Entrances and Walkways",
                "Cleared entrances and applied ice melt.",
                "Light snow with isolated icy patches.",
                90,
            ),
            (
                "Dora",
                "Plant Science Staff Entrance Walkway",
                "Shovelled walkway and treated steps.",
                "Walkway clear and passable.",
                60,
            ),
            (
                "Alex",
                "Art Barn Loading Area",
                "Cleared loading access and applied sand.",
                "Packed snow removed; surface secure.",
                30,
            ),
        ]
        for worker_name, location_name, action, condition, minutes_ago in snow_log_specs:
            db.session.add(SnowLog(
                user_id=users_by_name[worker_name].user_id,
                snow_log_location_id=locations_by_name[location_name].snow_log_location_id,
                action_taken=action,
                condition=condition,
                timestamp=now - timedelta(minutes=minutes_ago),
            ))

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    click.echo(f"[OK] Portfolio demo day refreshed: {resolved_database}")
    click.echo(
        "[VERIFY] attendance=22, assignments=1, events=1, "
        "supply_requests=2, snow_logs=3"
    )

@click.command("seed-core-data")
@with_appcontext
def seed_core_data():
    load_core_data()


def load_core_data():
    backend_dir = Path(__file__).resolve().parent
    data_folder = backend_dir / "data"

    buildings_path = data_folder / "buildings.csv"
    users_path = data_folder / "users.csv"
    areas_path = data_folder / "areas.csv"

    for path in [buildings_path, users_path, areas_path]:
        if not path.exists():
            click.echo(f"[ERR] Missing file: {path}")
            raise SystemExit(1)

    from app.models import (
        Assignment,
        AttendanceRecord,
        Event,
        SnowLog,
        SnowLogLocation,
        SupplyRequest,
        SupplyRequestItem,
        assignment_workers,
    )

    db.create_all()

    click.echo("[INFO] Clearing existing data...")
    SupplyRequestItem.query.delete()
    SupplyRequest.query.delete()
    db.session.execute(assignment_workers.delete())
    Assignment.query.delete()
    Event.query.delete()
    AttendanceRecord.query.delete()
    SnowLog.query.delete()
    SnowLogLocation.query.delete()
    User.query.delete()
    Area.query.delete()
    Building.query.delete()
    db.session.commit()

    click.echo("[INFO] Loading buildings...")
    with buildings_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            db.session.add(Building(
                building_id=int(row["building_id"]),
                building_name=row["building_name"],
                created_at=utc_now()
            ))
    db.session.commit()

    click.echo("[INFO] Loading areas...")
    with areas_path.open(newline="", encoding="utf-8") as f:
        area_rows = list(csv.DictReader(f))
        for row in area_rows:
            db.session.add(Area(
                area_id=int(row["area_id"]),
                area_name=row["area_name"],
                description=row["description"],
                building_id=int(row["building_id"]),
                created_at=utc_now()
            ))
    db.session.commit()

    click.echo("[INFO] Loading users and assigning areas...")
    area_by_user = {
        int(row["assigned_user_id"]): int(row["area_id"])
        for row in area_rows
        if row.get("assigned_user_id")
    }

    with users_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            user_id = int(row["user_id"])
            user = User(
                user_id=user_id,
                name=row["user_name"],
                email=f"user{user_id}@example.com",
                role=row["role"],
                area_id=area_by_user.get(user_id),
                created_at=utc_now()
            )
            user.set_password("demo")
            db.session.add(user)
    for name, email, role in (
        ("Bob Coordinator", "bob@example.com", "coordinator"),
        ("Sara Supervisor", "sara@example.com", "supervisor"),
    ):
        user = User(name=name, email=email, role=role, area_id=None, created_at=utc_now())
        user.set_password("demo")
        db.session.add(user)
    db.session.commit()

    click.echo("[INFO] Loading active Snow Log locations...")
    for area_id, location_name in (
        (1, "Physical Plant Entrances and Walkways"),
        (2, "Plant Science Staff Entrance Walkway"),
        (3, "Art Barn Loading Area"),
    ):
        db.session.add(SnowLogLocation(
            area_id=area_id,
            location_name=location_name,
            is_active=True,
        ))
    db.session.commit()

    click.echo("[OK] Core data loaded successfully!")
    click.echo(
        "[VERIFY] "
        f"buildings={Building.query.count()}, "
        f"areas={Area.query.count()}, "
        f"users={User.query.count()}, "
        f"snow_log_locations={SnowLogLocation.query.count()}"
    )

    first_user = User.query.order_by(User.user_id).first()
    first_area = Area.query.order_by(Area.area_id).first()
    if first_user and first_area:
        click.echo(
            "[VERIFY] "
            f"first_user={first_user.user_id}:{first_user.name}, "
            f"first_area={first_area.area_id}:{first_area.area_name}"
        )

def register_cli(app):
    app.cli.add_command(seed_supplies)
    app.cli.add_command(seed_sample_request)
    app.cli.add_command(seed_core_data)
    app.cli.add_command(seed_portfolio_demo_day)
