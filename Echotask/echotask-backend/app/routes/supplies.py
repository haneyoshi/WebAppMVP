from flask import Blueprint

supplies_bp = Blueprint('supplies',__name__)

@supplies_bp.route("/supplies")
def supplies_home():
    return "Supplies Request Page"