from .user_routes import user_bp
from .attendance_routes import attendance_bp
from .snow_log_routes import snowlog_bp
from .supply_routes import supplies_bp
from .test_routes import test_bp

def register_routes(app):
    app.register_blueprint(user_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(snowlog_bp)
    app.register_blueprint(supplies_bp)
    app.register_blueprint(test_bp)


# this puts all routes together into a whole and gives them to Flask
