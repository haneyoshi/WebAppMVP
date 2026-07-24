from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from app import db
from app.auth import get_current_user, login_required, roles_required
from app.models.area import Area
from app.models.user import User


user_bp = Blueprint("user", __name__, url_prefix="/users")
USER_ROLES = {"worker", "coordinator", "supervisor"}


def _serialize_user(user):
    result = {
        "user_id": user.user_id,
        "name": user.name,
        "role": user.role,
        "is_active": user.is_active,
        "area_id": user.area_id,
        "area_name": user.area.area_name if user.area else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }
    viewer = get_current_user()
    if viewer and (viewer.role == "supervisor" or viewer.user_id == user.user_id):
        result["email"] = user.email
    return result


def _validate_account_data(data, partial=False):
    values = {}
    for field_name in ("name", "email"):
        if field_name in data or not partial:
            value = data.get(field_name)
            if not isinstance(value, str) or not value.strip():
                return None, (jsonify({"error": f"{field_name} is required"}), 400)
            values[field_name] = value.strip().lower() if field_name == "email" else value.strip()

    if "role" in data or not partial:
        role = data.get("role")
        if role not in USER_ROLES:
            return None, (jsonify({"error": "role must be worker, coordinator, or supervisor"}), 400)
        values["role"] = role

    if "area_id" in data or not partial:
        area_id = data.get("area_id")
        if area_id is not None and (
            not isinstance(area_id, int) or isinstance(area_id, bool)
        ):
            return None, (jsonify({"error": "area_id must be an integer or null"}), 400)
        if area_id is not None and not db.session.get(Area, area_id):
            return None, (jsonify({"error": "area_id not found"}), 404)
        values["area_id"] = area_id

    if "password" in data or not partial:
        password = data.get("password")
        if not isinstance(password, str) or not password:
            return None, (jsonify({"error": "password is required"}), 400)
        values["password"] = password

    if "is_active" in data:
        if not isinstance(data["is_active"], bool):
            return None, (jsonify({"error": "is_active must be a boolean"}), 400)
        values["is_active"] = data["is_active"]
    return values, None


@user_bp.route("", methods=["GET"])
@login_required
def get_users():
    query = User.query
    if get_current_user().role != "supervisor":
        query = query.filter_by(role="worker", is_active=True)
    users = query.order_by(User.name.asc()).all()
    return jsonify([_serialize_user(user) for user in users])


@user_bp.route("/<int:user_id>", methods=["GET"])
@login_required
def get_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    viewer = get_current_user()
    if viewer.role != "supervisor" and (
        user.user_id != viewer.user_id and (user.role != "worker" or not user.is_active)
    ):
        return jsonify({"error": "Forbidden"}), 403
    return jsonify(_serialize_user(user))


@user_bp.route("", methods=["POST"])
@roles_required("supervisor")
def create_user():
    values, error = _validate_account_data(request.get_json(silent=True) or {})
    if error:
        return error
    if values["role"] == "worker" and values["area_id"] is None:
        return jsonify({"error": "Worker accounts require an area_id"}), 400
    if values["role"] != "worker" and values["area_id"] is not None:
        return jsonify({"error": "Only worker accounts may have an area_id"}), 400
    password = values.pop("password")
    user = User(**values)
    user.set_password(password)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Email or area is already assigned"}), 409
    return jsonify(_serialize_user(user)), 201


@user_bp.route("/<int:user_id>", methods=["PATCH"])
@roles_required("supervisor")
def update_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    values, error = _validate_account_data(request.get_json(silent=True) or {}, partial=True)
    if error:
        return error
    final_role = values.get("role", user.role)
    final_area_id = values.get("area_id", user.area_id)
    if final_role == "worker" and final_area_id is None:
        return jsonify({"error": "Worker accounts require an area_id"}), 400
    if final_role != "worker" and final_area_id is not None:
        return jsonify({"error": "Only worker accounts may have an area_id"}), 400
    if values.get("is_active") is False and user.user_id == get_current_user().user_id:
        return jsonify({"error": "Supervisors cannot deactivate their own account"}), 400
    password = values.pop("password", None)
    for field_name, value in values.items():
        setattr(user, field_name, value)
    if password is not None:
        user.set_password(password)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Email or area is already assigned"}), 409
    return jsonify(_serialize_user(user))


@user_bp.route("/<int:user_id>", methods=["DELETE"])
@roles_required("supervisor")
def deactivate_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    if user.user_id == get_current_user().user_id:
        return jsonify({"error": "Supervisors cannot deactivate their own account"}), 400
    user.is_active = False
    db.session.commit()
    return jsonify({"message": "User deactivated", "user_id": user.user_id})
