from functools import wraps

from flask import g, jsonify, session

from app import db
from app.models.user import User


def get_current_user():
    if "current_user" not in g:
        user_id = session.get("user_id")
        g.current_user = db.session.get(User, user_id) if user_id else None
        if g.current_user and not g.current_user.is_active:
            session.clear()
            g.current_user = None
    return g.current_user


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not get_current_user():
            return jsonify({"error": "Authentication required"}), 401
        return view(*args, **kwargs)
    return wrapped_view


def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({"error": "Authentication required"}), 401
            if user.role not in roles:
                return jsonify({"error": "Forbidden"}), 403
            return view(*args, **kwargs)
        return wrapped_view
    return decorator
