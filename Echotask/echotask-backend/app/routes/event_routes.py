from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from app import db
from app.models.building import Building
from app.models.event import Event
from app.models.user import User
from app.auth import get_current_user, login_required, roles_required


events_bp = Blueprint("events", __name__, url_prefix="/events")


def _parse_datetime(value, field_name):
    if not isinstance(value, str) or not value.strip():
        return None, f"{field_name} is required and must be an ISO-8601 datetime"
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None, f"{field_name} must be an ISO-8601 datetime"
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None, f"{field_name} must include a timezone offset"
    return parsed.astimezone(timezone.utc).replace(tzinfo=None), None


def _serialize_utc_datetime(value):
    return value.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def _serialize_event(event):
    return {
        "event_id": event.event_id,
        "building_id": event.building_id,
        "building_name": event.building.building_name,
        "title": event.title,
        "description": event.description,
        "start_time": _serialize_utc_datetime(event.start_time),
        "end_time": _serialize_utc_datetime(event.end_time),
        "created_by_user_id": event.created_by_user_id,
        "created_by_name": event.created_by.name,
    }


@events_bp.route("", methods=["GET"])
@login_required
def list_events():
    query = Event.query
    building_id = request.args.get("building_id")
    if building_id is not None:
        try:
            building_id = int(building_id)
        except ValueError:
            return jsonify({"error": "building_id must be an integer"}), 400
        query = query.filter_by(building_id=building_id)

    events = query.order_by(Event.start_time.asc(), Event.event_id.asc()).all()
    return jsonify([_serialize_event(event) for event in events])


@events_bp.route("/<int:event_id>", methods=["GET"])
@login_required
def get_event(event_id):
    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404
    return jsonify(_serialize_event(event))


@events_bp.route("", methods=["POST"])
@roles_required("coordinator", "supervisor")
def create_event():
    data = request.get_json(silent=True) or {}
    building_id = data.get("building_id")
    current_user = get_current_user()
    created_by_user_id = data.get("created_by_user_id", current_user.user_id)
    title = data.get("title")
    description = data.get("description")

    if not isinstance(building_id, int) or isinstance(building_id, bool):
        return jsonify({"error": "building_id must be an integer"}), 400
    if not isinstance(created_by_user_id, int) or isinstance(created_by_user_id, bool):
        return jsonify({"error": "created_by_user_id must be an integer"}), 400
    if created_by_user_id != current_user.user_id:
        return jsonify({"error": "Events can be created only as the authenticated user"}), 403
    if not isinstance(title, str) or not title.strip():
        return jsonify({"error": "title is required"}), 400
    if description is not None and not isinstance(description, str):
        return jsonify({"error": "description must be a string or null"}), 400

    start_time, error = _parse_datetime(data.get("start_time"), "start_time")
    if error:
        return jsonify({"error": error}), 400
    end_time, error = _parse_datetime(data.get("end_time"), "end_time")
    if error:
        return jsonify({"error": error}), 400
    if end_time <= start_time:
        return jsonify({"error": "end_time must be after start_time"}), 400

    if not db.session.get(Building, building_id):
        return jsonify({"error": "building_id not found"}), 404
    if not db.session.get(User, created_by_user_id):
        return jsonify({"error": "created_by_user_id not found"}), 404

    event = Event(
        building_id=building_id,
        title=title.strip(),
        description=description.strip() if isinstance(description, str) else None,
        start_time=start_time,
        end_time=end_time,
        created_by_user_id=created_by_user_id,
    )
    db.session.add(event)
    db.session.commit()
    return jsonify(_serialize_event(event)), 201


def _update_event_values(event, data):
    if "building_id" in data:
        building_id = data["building_id"]
        if not isinstance(building_id, int) or isinstance(building_id, bool):
            return jsonify({"error": "building_id must be an integer"}), 400
        if not db.session.get(Building, building_id):
            return jsonify({"error": "building_id not found"}), 404
        event.building_id = building_id
    if "title" in data:
        if not isinstance(data["title"], str) or not data["title"].strip():
            return jsonify({"error": "title must be a non-empty string"}), 400
        event.title = data["title"].strip()
    if "description" in data:
        if data["description"] is not None and not isinstance(data["description"], str):
            return jsonify({"error": "description must be a string or null"}), 400
        event.description = data["description"].strip() if isinstance(data["description"], str) else None
    start_time = event.start_time
    end_time = event.end_time
    if "start_time" in data:
        start_time, error = _parse_datetime(data["start_time"], "start_time")
        if error:
            return jsonify({"error": error}), 400
    if "end_time" in data:
        end_time, error = _parse_datetime(data["end_time"], "end_time")
        if error:
            return jsonify({"error": error}), 400
    if end_time <= start_time:
        return jsonify({"error": "end_time must be after start_time"}), 400
    event.start_time = start_time
    event.end_time = end_time
    return None


@events_bp.route("/<int:event_id>", methods=["PATCH"])
@roles_required("coordinator", "supervisor")
def update_event(event_id):
    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404
    error_response = _update_event_values(event, request.get_json(silent=True) or {})
    if error_response:
        return error_response
    db.session.commit()
    return jsonify(_serialize_event(event))


@events_bp.route("/<int:event_id>", methods=["DELETE"])
@roles_required("coordinator", "supervisor")
def delete_event(event_id):
    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404
    db.session.delete(event)
    db.session.commit()
    return jsonify({"message": "Event deleted", "event_id": event_id})
