from .user_routes import user_bp
from .attendance_routes import attendance_bp
from .snow_log_routes import snowlog_bp
from .supply_routes import supplies_bp
from .test_routes import test_bp
from .location_routes import locations_bp
from .event_routes import events_bp
from .auth_routes import auth_bp
from .assignment_routes import assignments_bp
from .availability_routes import availability_bp

def register_routes(app):
    app.register_blueprint(user_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(snowlog_bp)
    app.register_blueprint(supplies_bp)
    app.register_blueprint(test_bp)
    app.register_blueprint(locations_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(assignments_bp)
    app.register_blueprint(availability_bp)


# this puts all routes together into a whole and gives them to Flask
