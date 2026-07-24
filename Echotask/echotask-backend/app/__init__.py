# Main app factory, creates the Flask app, connects the database, registers the routes

from flask import Flask, jsonify
from config import Config
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app(test_config=None):
    app = Flask(__name__, static_folder=None)
    # A flask object, meaning, "app" is the Flask object (your running web server)
    # "__name__" is always a special built-in variable in Python.
    # passing __name__ to Flask, so it knows who is running
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    # Tell Flask to load a bunch of settings from the congig class (defined in config.py)
    # settings including: Database URL, Secret Key, other options(UPLOAD_FOLDER, SESSION_COOKIE_SECURE, etc.)
    
    db.init_app(app)
    # connects the Flask app to that database object

    from .routes import register_routes
    register_routes(app)

    # Register seed commands (terminal commands)
    from seeds import register_cli
    register_cli(app)
    from schema_upgrade import register_schema_commands
    register_schema_commands(app)

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(_error):
        return jsonify({"error": "Method not allowed"}), 405

    return app
