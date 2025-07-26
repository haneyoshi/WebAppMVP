from flask import Blueprint

test_bp = Blueprint('test', __name__)

@test_bp.route("/ping")
def ping():
    return {"message": "EchoTask API is running!"}
