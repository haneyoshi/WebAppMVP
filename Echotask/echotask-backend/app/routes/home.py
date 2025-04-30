from flask import Blueprint

home_bp = Blueprint('home',__name__)
# Each Blueprint = Separate feature module
# Each Blueprint = Focused routes

@home_bp.route("/")
#  this is is a special command called a "decorator" in Python.
    # It registers a connection between a URL and a function (hello()).
def hello():
    return "Hello from EchoTask Blueprint!"

@home_bp.route("/about")
def about():
    return "About EchoTask"

@home_bp.route("/contact")
def contact():
    return "Contact EchoTask"