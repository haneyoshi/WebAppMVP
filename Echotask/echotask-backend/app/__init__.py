from flask import Flask
from config import Config

def create_app():
    app = Flask(__name__)
    # A flask object, meaning, "app" is the Flask object (your running web server)
    # "__name__" is always a special built-in variable in Python.
    # passing __name__ to Flask, so it knows who is running
    app.config.from_object(Config)
    # Tell Flask to load a bunch of settings from the congig class (defined in config.py)
    # settings including: Database URL, Secret Key, other options(UPLOAD_FOLDER, SESSION_COOKIE_SECURE, etc.)


    # Import and register Blueprints here
    from app.routes.home import home_bp
    app.register_blueprint(home_bp)

    return app
