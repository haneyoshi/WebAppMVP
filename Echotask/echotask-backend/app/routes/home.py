from flask import Blueprint

home_bp = Blueprint('home',__name__)
# Each Blueprint = Separate feature module
# Each Blueprint = Focused routes

@home_bp.route("/")
#  this is is a special command called a "decorator" in Python.
    # It registers a connection between a URL and a function (hello()).
    # by defaut, "/" means homepage or root
def hello():
    return "Hello from EchoTask Blueprint!"