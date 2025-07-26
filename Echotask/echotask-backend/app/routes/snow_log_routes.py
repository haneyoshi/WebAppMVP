from flask import Blueprint

snowlog_bp = Blueprint('snowlog',__name__)

@snowlog_bp.route("/snowlog")
def snowlog_home():
    return "Snow Log Page"