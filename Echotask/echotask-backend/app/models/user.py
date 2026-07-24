from app import db
from werkzeug.security import check_password_hash, generate_password_hash
from app.time_utils import utc_now

class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False)  # worker, coordinator, supervisor
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    area_id = db.Column(db.Integer, db.ForeignKey('areas.area_id'), unique=True, nullable=True)
    # db.ForeignKey() — defines a foreign key column (this tells SQLAlchemy where the relationship starts).
    created_at = db.Column(db.DateTime, default=utc_now)

    area = db.relationship('Area', back_populates='user', uselist=False)
    #db.relationship() — sets up a Python-level link between models (this tells SQLAlchemy how to access related records).
    snow_logs = db.relationship('SnowLog', back_populates='user', foreign_keys='SnowLog.user_id')
    marked_attendance = db.relationship('AttendanceRecord', foreign_keys='AttendanceRecord.marked_by_user_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

