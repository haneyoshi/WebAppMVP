from flask import Blueprint, request, jsonify
from app import db
import csv
from pathlib import Path

# ==== IMPORT MODELS ====
from app.models.user import User
from app.models.area import Area
from app.models.supply_item import SupplyItem
from app.models.supply_request import SupplyRequest
from app.models.supply_request_item import SupplyRequestItem
from app.auth import get_current_user, login_required, roles_required

supplies_bp = Blueprint("supply", __name__, url_prefix="/supplies")


# GET /supplies/items : list all supply items
@supplies_bp.route("/items", methods=["GET"])
@login_required
def list_items():
    items = SupplyItem.query.order_by(SupplyItem.item_name.asc()).all()
    return jsonify([
        {
            "item_id": i.item_id,
            "item_name": i.item_name,
            "category": i.category,
            "created_at": i.created_at.isoformat() if i.created_at else None,
        }
        for i in items
    ])


# POST /supplies/items/import : import items from CSV (one-time seed)
# Expected CSV columns: Category,Product
@supplies_bp.route("/items/import", methods=["POST"])
@roles_required("supervisor")
def import_items_from_csv():
    # CSV is at project root: echotask-backend/supply_Item_List.csv (same level as /app)
    csv_path = Path(__file__).resolve().parents[2] / "Supply_Item_List.csv"
    if not csv_path.exists():
        return jsonify({"error": f"CSV not found at {csv_path}"}), 400

    created, skipped = 0, 0
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("Product") or "").strip()
            category = (row.get("Category") or "").strip()
            if not name or not category:
                skipped += 1
                continue

            # unique on item_name per your DBML
            existing = SupplyItem.query.filter_by(item_name=name).first()
            if existing:
                skipped += 1
                continue

            item = SupplyItem(item_name=name, category=category)
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
@supplies_bp.route("/requests", methods=["POST"])
@roles_required("worker")
def create_supply_request():
    data = request.get_json(silent=True) or {}
    current_user = get_current_user()
    submitted_by_user_id = data.get("submitted_by_user_id", current_user.user_id)
    area_id = data.get("area_id")
    items = data.get("items", [])

    if not isinstance(submitted_by_user_id, int) or isinstance(submitted_by_user_id, bool):
        return jsonify({"error": "submitted_by_user_id must be an integer"}), 400
    if submitted_by_user_id != current_user.user_id:
        return jsonify({"error": "Workers can submit requests only for themselves"}), 403
    if not isinstance(area_id, int) or isinstance(area_id, bool):
        return jsonify({"error": "area_id must be an integer"}), 400
    if not isinstance(items, list) or not items:
        return jsonify({"error": "submitted_by_user_id, area_id and items are required"}), 400

    # Basic existence checks (lightweight for MVP)
    if not db.session.get(Area, area_id):
        return jsonify({"error": "area_id not found"}), 404
    if current_user.area_id != area_id:
        return jsonify({"error": "Workers can submit requests only for their own area"}), 403

    validated_items = []
    for it in items:
        if not isinstance(it, dict):
            return jsonify({"error": "Each line item must be an object"}), 400
        item_id = it.get("item_id")
        qty = it.get("quantity")
        if not isinstance(item_id, int) or isinstance(item_id, bool):
            return jsonify({"error": "item_id must be an integer"}), 400
        if not isinstance(qty, int) or isinstance(qty, bool) or qty <= 0:
            return jsonify({"error": "quantity must be a positive integer"}), 400
        if not db.session.get(SupplyItem, item_id):
            return jsonify({"error": f"item_id {item_id} not found"}), 404
        validated_items.append((item_id, qty))

    req = SupplyRequest(user_id=submitted_by_user_id, area_id=area_id)
    db.session.add(req)
    db.session.flush()

    for item_id, qty in validated_items:
        line = SupplyRequestItem(
            request_id=req.request_id,
            item_id=item_id,
            quantity=qty,
        )
        db.session.add(line)

    db.session.commit()

    return jsonify({
        "message": "Supply request submitted",
        "supply_request_id": req.request_id,
    }), 201


# GET /supplies/requests : list all requests with nested items (manager view)
@supplies_bp.route("/requests", methods=["GET"])
@login_required
def list_supply_requests():
    query = SupplyRequest.query
    current_user = get_current_user()
    if current_user.role == "worker":
        query = query.filter_by(area_id=current_user.area_id)
    requests_q = query.order_by(SupplyRequest.request_date.desc()).all()

    # preload lookups to reduce queries (simple in-memory maps)
    users_by_id = {u.user_id: u for u in User.query.all()}
    areas_by_id = {a.area_id: a for a in Area.query.all()}
    items_by_id = {i.item_id: i for i in SupplyItem.query.all()}

    results = []
    for r in requests_q:
        rid = r.request_id
        line_items = r.items

        results.append({
            "supply_request_id": rid,
            "submitted_by_user_id": r.user_id,
            "submitted_by_name": getattr(users_by_id.get(r.user_id), "name", None),
            "area_id": r.area_id,
            "area_name": getattr(areas_by_id.get(r.area_id), "area_name", None),
            "submitted_at": r.request_date.isoformat() if r.request_date else None,
            "status": r.status,
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
@supplies_bp.route("/requests/summary/items", methods=["GET"])
@roles_required("supervisor")
def summary_by_item():
    # naive aggregation in Python (fine for MVP)
    lines = SupplyRequestItem.query.all()
    totals = {}
    for li in lines:
        totals[li.item_id] = totals.get(li.item_id, 0) + int(li.quantity or 0)

    # map item names
    items_by_id = {i.item_id: i for i in SupplyItem.query.all()}

    out = []
    for item_id, qty in sorted(totals.items(), key=lambda x: x[0]):
        item_name = getattr(items_by_id.get(item_id), "item_name", None)
        out.append({"item_id": item_id, "item_name": item_name, "total_quantity": qty})

    return jsonify(out)


@supplies_bp.route("/requests/<int:request_id>/status", methods=["PATCH"])
@roles_required("supervisor")
def update_supply_request_status(request_id):
    supply_request = db.session.get(SupplyRequest, request_id)
    if not supply_request:
        return jsonify({"error": "Supply request not found"}), 404
    status = (request.get_json(silent=True) or {}).get("status")
    if status not in {"Submitted", "Completed"}:
        return jsonify({"error": "status must be Submitted or Completed"}), 400
    supply_request.status = status
    db.session.commit()
    return jsonify({"supply_request_id": request_id, "status": status})
