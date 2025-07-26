from .user_routes import user_bp
from .attendance_routes import attendance_bp
from .snow_log_routes import snow_log_bp
from .event_routes import event_bp

def register_routes(app):
    app.register_blueprint(user_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(snow_log_bp)
    app.register_blueprint(event_bp)


# this puts all routes together into a whole and gives them to Flask