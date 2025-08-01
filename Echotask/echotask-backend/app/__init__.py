# Main app factory, creates the Flask app, connects the database, registers the routes

from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from .routes import register_routes

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    # A flask object, meaning, "app" is the Flask object (your running web server)
    # "__name__" is always a special built-in variable in Python.
    # passing __name__ to Flask, so it knows who is running
    app.config.from_object(Config)
    # Tell Flask to load a bunch of settings from the congig class (defined in config.py)
    # settings including: Database URL, Secret Key, other options(UPLOAD_FOLDER, SESSION_COOKIE_SECURE, etc.)
    
    db.init_app(app)
    # connects the Flask app to that database object
    register_routes(app)

    # Import and register Blueprints here
    from app.routes.test_routes import home_bp
    app.register_blueprint(home_bp)
    from app.routes.supply_routes import supplies_bp
    app.register_blueprint(supplies_bp)
    from app.routes.attendance_routes import attendance_bp
    app.register_blueprint(attendance_bp)
    from app.routes.snow_log_routes import snowlog_bp
    app.register_blueprint(snowlog_bp)

    return app
