from flask import Blueprint, jsonify, request, session

from app.auth import get_current_user, login_required
from app.models.user import User


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _serialize_identity(user):
    return {
        "user_id": user.user_id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "area_id": user.area_id,
        "is_active": user.is_active,
    }


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")
    if not isinstance(email, str) or not email.strip():
        return jsonify({"error": "email is required"}), 400
    if not isinstance(password, str) or not password:
        return jsonify({"error": "password is required"}), 400

    user = User.query.filter_by(email=email.strip().lower()).first()
    if not user or not user.is_active or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    session.clear()
    session["user_id"] = user.user_id
    return jsonify(_serialize_identity(user))


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})


@auth_bp.route("/me", methods=["GET"])
@login_required
def current_identity():
    return jsonify(_serialize_identity(get_current_user()))
