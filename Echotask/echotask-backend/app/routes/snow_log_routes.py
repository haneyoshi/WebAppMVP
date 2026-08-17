from flask import Blueprint, jsonify, request

from app import db
from app.models.area import Area
from app.models.snow_log import SnowLog
from app.models.snow_log_location import SnowLogLocation
from app.models.user import User
from app.auth import get_current_user, login_required, roles_required


snowlog_bp = Blueprint("snowlog", __name__)


def _parse_integer_query(name):
    value = request.args.get(name)
    if value is None:
        return None, None
    try:
        return int(value), None
    except ValueError:
        return None, (jsonify({"error": f"{name} must be an integer"}), 400)


def _serialize_location(location):
    return {
        "snow_log_location_id": location.snow_log_location_id,
        "location_name": location.location_name,
        "area_id": location.area_id,
        "area_name": location.area.area_name,
        "building_id": location.area.building_id,
        "building_name": location.area.building.building_name,
        "is_active": location.is_active,
    }


def _serialize_log(log):
    return {
        "snow_log_id": log.snow_log_id,
        "user_id": log.user_id,
        "user_name": log.user.name,
        "snow_log_location_id": log.snow_log_location_id,
        "location_name": log.location.location_name,
        "area_id": log.location.area_id,
        "area_name": log.location.area.area_name,
        "action_taken": log.action_taken,
        "condition": log.condition,
        "timestamp": log.timestamp.isoformat() if log.timestamp else None,
    }


@snowlog_bp.route("/snow-log-locations", methods=["GET"])
@login_required
def list_snow_log_locations():
    area_id, error = _parse_integer_query("area_id")
    if error:
        return error

    query = SnowLogLocation.query
    if area_id is not None:
        query = query.filter_by(area_id=area_id)
    locations = query.order_by(SnowLogLocation.location_name.asc()).all()
    return jsonify([_serialize_location(location) for location in locations])


@snowlog_bp.route("/snow-log-locations/<int:location_id>", methods=["GET"])
@login_required
def get_snow_log_location(location_id):
    location = db.session.get(SnowLogLocation, location_id)
    if not location:
        return jsonify({"error": "Snow-log location not found"}), 404
    return jsonify(_serialize_location(location))


@snowlog_bp.route("/snow-log-locations", methods=["POST"])
@roles_required("coordinator", "supervisor")
def create_snow_log_location():
    data = request.get_json(silent=True) or {}
    area_id = data.get("area_id")
    location_name = data.get("location_name")

    if not isinstance(area_id, int) or isinstance(area_id, bool):
        return jsonify({"error": "area_id must be an integer"}), 400
    if not isinstance(location_name, str) or not location_name.strip():
        return jsonify({"error": "location_name is required"}), 400
    if not db.session.get(Area, area_id):
        return jsonify({"error": "area_id not found"}), 404

    location = SnowLogLocation(area_id=area_id, location_name=location_name.strip())
    db.session.add(location)
    db.session.commit()
    return jsonify(_serialize_location(location)), 201


@snowlog_bp.route("/snow-log-locations/<int:location_id>", methods=["PATCH"])
@roles_required("coordinator", "supervisor")
def update_snow_log_location(location_id):
    location = db.session.get(SnowLogLocation, location_id)
    if not location:
        return jsonify({"error": "Snow-log location not found"}), 404
    data = request.get_json(silent=True) or {}
    if "location_name" in data:
        if not isinstance(data["location_name"], str) or not data["location_name"].strip():
            return jsonify({"error": "location_name must be a non-empty string"}), 400
        location.location_name = data["location_name"].strip()
    if "area_id" in data:
        area_id = data["area_id"]
        if not isinstance(area_id, int) or isinstance(area_id, bool):
            return jsonify({"error": "area_id must be an integer"}), 400
        if not db.session.get(Area, area_id):
            return jsonify({"error": "area_id not found"}), 404
        location.area_id = area_id
    if "is_active" in data:
        if not isinstance(data["is_active"], bool):
            return jsonify({"error": "is_active must be a boolean"}), 400
        location.is_active = data["is_active"]
    db.session.commit()
    return jsonify(_serialize_location(location))


@snowlog_bp.route("/snow-logs", methods=["GET"])
@roles_required("coordinator", "supervisor")
def list_snow_logs():
    query = SnowLog.query
    for field_name in ("user_id", "snow_log_location_id"):
        value, error = _parse_integer_query(field_name)
        if error:
            return error
        if value is not None:
            query = query.filter_by(**{field_name: value})

    logs = query.order_by(SnowLog.timestamp.desc(), SnowLog.snow_log_id.desc()).all()
    return jsonify([_serialize_log(log) for log in logs])


@snowlog_bp.route("/snow-logs/<int:snow_log_id>", methods=["GET"])
@roles_required("coordinator", "supervisor")
def get_snow_log(snow_log_id):
    log = db.session.get(SnowLog, snow_log_id)
    if not log:
        return jsonify({"error": "Snow log not found"}), 404
    return jsonify(_serialize_log(log))


@snowlog_bp.route("/snow-logs", methods=["POST"])
@roles_required("worker")
def create_snow_log():
    data = request.get_json(silent=True) or {}
    current_user = get_current_user()
    user_id = data.get("user_id", current_user.user_id)
    location_id = data.get("snow_log_location_id")

    if not isinstance(user_id, int) or isinstance(user_id, bool):
        return jsonify({"error": "user_id must be an integer"}), 400
    if user_id != current_user.user_id:
        return jsonify({"error": "Workers can submit snow logs only for themselves"}), 403
    if not isinstance(location_id, int) or isinstance(location_id, bool):
        return jsonify({"error": "snow_log_location_id must be an integer"}), 400

    text_values = {}
    for field_name in ("action_taken", "condition"):
        value = data.get(field_name)
        if value is not None and not isinstance(value, str):
            return jsonify({"error": f"{field_name} must be a string or null"}), 400
        text_values[field_name] = value.strip() if isinstance(value, str) else None

    location = db.session.get(SnowLogLocation, location_id)
    if not location:
        return jsonify({"error": "snow_log_location_id not found"}), 404
    if not location.is_active:
        return jsonify({"error": "Snow-log location is inactive"}), 400

    log = SnowLog(
        user_id=user_id,
        snow_log_location_id=location_id,
        **text_values,
    )
    db.session.add(log)
    db.session.commit()
    return jsonify(_serialize_log(log)), 201
