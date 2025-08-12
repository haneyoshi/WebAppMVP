from flask import Blueprint, request, jsonify
from app import db
from models.user import User
from models.area import Area  # Optional: for enriching area info

user_bp = Blueprint('user', __name__, url_prefix='/users')


# GET /users - Fetch all users
@user_bp.route('/', methods=['GET'])
def get_users():
    users = User.query.all()
    result = []
    for user in users:
        result.append({
            "user_id": user.user_id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "area_id": user.area_id,
            "created_at": user.created_at.isoformat()
        })
    return jsonify(result)


# POST /users - Create new user
@user_bp.route('/', methods=['POST'])
def create_user():
    data = request.get_json()
    
    name = data.get('name')
    email = data.get('email')
    password_hash = data.get('password_hash')  # For now, just assume it's hashed
    role = data.get('role')
    area_id = data.get('area_id')

    if not all([name, email, password_hash, role]):
        return jsonify({"error": "Missing required fields"}), 400

    new_user = User(
        name=name,
        email=email,
        password_hash=password_hash,
        role=role,
        area_id=area_id
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User created successfully", "user_id": new_user.user_id}), 201


# DELETE /users/<int:user_id> - Delete user by ID
@user_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": f"User {user_id} deleted successfully"}), 200
