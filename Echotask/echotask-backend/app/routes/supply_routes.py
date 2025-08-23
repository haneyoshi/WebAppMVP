from flask import Blueprint, request, jsonify
from app import db
from datetime import datetime
import csv
import os

# ==== IMPORT MODELS ====
from models.user import User
from models.area import Area
from models.supply_item import SupplyItem
from models.supply_request import SupplyRequest
from models.supply_request_item import SupplyRequestItem

supply_bp = Blueprint("supply", __name__, url_prefix="/supplies")


# GET /supplies/items : list all supply items
@supply_bp.route("/items", methods=["GET"])
def list_items():
    items = SupplyItem.query.order_by(SupplyItem.item_name.asc()).all()
    return jsonify([
        {
            "item_id": i.item_id if hasattr(i, "item_id") else i.item_id,
            "item_name": i.item_name,
            "item_description": getattr(i, "item_description", None),
            "created_at": i.created_at.isoformat() if getattr(i, "created_at", None) else None,
        }
        for i in items
    ])


# POST /supplies/items/import : import items from CSV (one-time seed)
# Expected CSV columns: item_name,item_description
@supply_bp.route("/items/import", methods=["POST"])
def import_items_from_csv():
    # CSV is at project root: echotask-backend/supply_Item_List.csv (same level as /app)
    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "supply_Item_List.csv")
    if not os.path.exists(csv_path):
        return jsonify({"error": f"CSV not found at {csv_path}"}), 400

    created, skipped = 0, 0
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("item_name") or "").strip()
            desc = (row.get("item_description") or "").strip()
            if not name:
                skipped += 1
                continue

            # unique on item_name per your DBML
            existing = SupplyItem.query.filter_by(item_name=name).first()
            if existing:
                skipped += 1
                continue

            item = SupplyItem(item_name=name, item_description=desc, created_at=datetime.utcnow())
            db.session.add(item)
            created += 1

    db.session.commit()
    return jsonify({"message": "Import complete", "created": created, "skipped": skipped})


# ---------------------------
# REQUESTS
# ---------------------------

# POST /supplies/requests : create a supply request with line items
# JSON body:
# {
#   "submitted_by_user_id": 12,
#   "area_id": 5,
#   "items": [
#       {"item_id": 3, "quantity": 2},
#       {"item_id": 9, "quantity": 1}
#   ]
# }
@supply_bp.route("/requests", methods=["POST"])
def create_supply_request():
    data = request.get_json(silent=True) or {}
    submitted_by_user_id = data.get("submitted_by_user_id")
    area_id = data.get("area_id")
    items = data.get("items", [])

    if not submitted_by_user_id or not area_id or not items:
        return jsonify({"error": "submitted_by_user_id, area_id and items are required"}), 400

    # Basic existence checks (lightweight for MVP)
    if not User.query.get(submitted_by_user_id):
        return jsonify({"error": "submitted_by_user_id not found"}), 404
    if not Area.query.get(area_id):
        return jsonify({"error": "area_id not found"}), 404

    req = SupplyRequest(
        submitted_by_user_id=submitted_by_user_id,
        area_id=area_id,
        submitted_at=datetime.utcnow(),
    )
    db.session.add(req)
    db.session.flush()  # get request id before adding items

    # add line items
    for it in items:
        item_id = it.get("item_id")
        qty = it.get("quantity")
        if not item_id or not isinstance(qty, int) or qty <= 0:
            return jsonify({"error": f"Invalid line item: {it}"}), 400
        if not SupplyItem.query.get(item_id):
            return jsonify({"error": f"item_id {item_id} not found"}), 404

        line = SupplyRequestItem(
            supply_request_id=getattr(req, "supply_request_id", getattr(req, "request_id", None)),
            item_id=item_id,
            quantity=qty,
        )
        db.session.add(line)

    db.session.commit()

    return jsonify({
        "message": "Supply request submitted",
        "supply_request_id": getattr(req, "supply_request_id", getattr(req, "request_id", None)),
    }), 201


# GET /supplies/requests : list all requests with nested items (manager view)
@supply_bp.route("/requests", methods=["GET"])
def list_supply_requests():
    requests_q = SupplyRequest.query.order_by(SupplyRequest.submitted_at.desc()).all()

    # preload lookups to reduce queries (simple in-memory maps)
    users_by_id = {u.user_id: u for u in User.query.all()}
    areas_by_id = {a.area_id: a for a in Area.query.all()}
    items_by_id = {i.item_id if hasattr(i, "item_id") else i.item_id: i for i in SupplyItem.query.all()}

    results = []
    for r in requests_q:
        rid = getattr(r, "supply_request_id", getattr(r, "request_id", None))
        # r.items relationship may be named differently; if not present, query manually:
        line_items = getattr(r, "items", None)
        if line_items is None:
            line_items = SupplyRequestItem.query.filter_by(supply_request_id=rid).all()

        results.append({
            "supply_request_id": rid,
            "submitted_by_user_id": r.submitted_by_user_id,
            "submitted_by_name": getattr(users_by_id.get(r.submitted_by_user_id), "name", None),
            "area_id": r.area_id,
            "area_name": getattr(areas_by_id.get(r.area_id), "area_name", None),
            "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None,
            "items": [
                {
                    "item_id": li.item_id,
                    "item_name": getattr(items_by_id.get(li.item_id), "item_name", None),
                    "quantity": li.quantity,
                } for li in line_items
            ]
        })

    return jsonify(results)


# GET /supplies/requests/summary/items : totals per item (simple procurement view)
@supply_bp.route("/requests/summary/items", methods=["GET"])
def summary_by_item():
    # naive aggregation in Python (fine for MVP)
    lines = SupplyRequestItem.query.all()
    totals = {}
    for li in lines:
        totals[li.item_id] = totals.get(li.item_id, 0) + int(li.quantity or 0)

    # map item names
    items_by_id = {i.item_id if hasattr(i, "item_id") else i.item_id: i for i in SupplyItem.query.all()}

    out = []
    for item_id, qty in sorted(totals.items(), key=lambda x: x[0]):
        item_name = getattr(items_by_id.get(item_id), "item_name", None)
        out.append({"item_id": item_id, "item_name": item_name, "total_quantity": qty})

    return jsonify(out)
