# echotask-backend/seeds.py

from flask.cli import with_appcontext
import click, csv, os
from datetime import datetime

from app import db
from app.models.user import User
from app.models.area import Area
from app.models.building import Building
from app.models.supply_item import SupplyItem
from app.models.supply_request import SupplyRequest
from app.models.supply_request_item import SupplyRequestItem

# ***** To run seeds.py *****
# flask db upgrade     or your migration init step
# flask seed-core-demo
# flask seed-supplies --csv-path supply_Item_List.csv
# flask seed-sample-request



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
            if not name:
                skipped += 1
                continue
                # -> skip and go next row
            if SupplyItem.query.filter_by(item_name=name).first():
            # -> Avoid duplicates
                skipped += 1
                continue
            db.session.add(SupplyItem(
                item_name=name,
                item_description=None,
                created_at=datetime.utcnow(),
            ))
            created += 1
    db.session.commit()
    click.echo(f"[OK] Supplies import complete. created={created}, skipped={skipped}")

# ---- 2) Minimal core demo data so routes work out-of-the-box
@click.command("seed-core-demo")
@with_appcontext
def seed_core_demo():
    # Buildings / Areas
    b = Building(building_name="Demo Building", created_at=datetime.utcnow())
    db.session.add(b); db.session.flush()
    a = Area(area_name="Main Lobby", building_id=b.building_id, description="Front lobby", created_at=datetime.utcnow())
    db.session.add(a); db.session.flush()

    # Users (worker, coordinator, supervisor)
    u_worker = User(name="Alice Worker", email="alice@example.com", password_hash="demo", role="worker", area_id=a.area_id, created_at=datetime.utcnow())
    u_coord  = User(name="Bob Coordinator", email="bob@example.com", password_hash="demo", role="coordinator", area_id=None, created_at=datetime.utcnow())
    u_super  = User(name="Sara Supervisor", email="sara@example.com", password_hash="demo", role="supervisor", area_id=None, created_at=datetime.utcnow())
    db.session.add_all([u_worker, u_coord, u_super])
    db.session.commit()
    click.echo(f"[OK] Core demo seeded. building_id={b.building_id}, area_id={a.area_id}, users={[u_worker.user_id, u_coord.user_id, u_super.user_id]}")

# ---- 3) Tiny smoke test: make one request using the first 2 items
@click.command("seed-sample-request")
@with_appcontext
def seed_sample_request():
    worker = User.query.filter_by(role="worker").first()
    area = Area.query.first()
    items = SupplyItem.query.order_by(SupplyItem.item_name.asc()).limit(2).all()
    if not (worker and area and len(items) >= 1):
        click.echo("[ERR] Need at least 1 worker, 1 area, and 1 supply_item. Run: flask seed-core-demo && flask seed-supplies")
        raise SystemExit(1)

    req = SupplyRequest(submitted_by_user_id=worker.user_id, area_id=area.area_id, submitted_at=datetime.utcnow())
    db.session.add(req); db.session.flush()
    for it in items:
        db.session.add(SupplyRequestItem(supply_request_id=req.supply_request_id, supply_item_id=it.supply_item_id, quantity=1))
    db.session.commit()
    click.echo(f"[OK] Created sample request supply_request_id={req.supply_request_id}")

def register_cli(app):
    app.cli.add_command(seed_supplies)
    app.cli.add_command(seed_core_demo)
    app.cli.add_command(seed_sample_request)


