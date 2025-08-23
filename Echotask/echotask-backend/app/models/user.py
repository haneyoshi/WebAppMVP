from app import db
from datetime import datetime
#from werkzeug.security import generate_password_hash, check_password_hash
#password security method(for later)

# def set_password(self, password):
#     self.password_hash = generate_password_hash(password)

# def check_password(self, password):
#     return check_password_hash(self.password_hash, password)

class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False)  # worker, coordinator, supervisor
    area_id = db.Column(db.Integer, db.ForeignKey('areas.area_id'), unique=True, nullable=True)
    # db.ForeignKey() — defines a foreign key column (this tells SQLAlchemy where the relationship starts).
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    area = db.relationship('Area', uselist=False)
    #db.relationship() — sets up a Python-level link between models (this tells SQLAlchemy how to access related records).
    snow_logs = db.relationship('SnowLog', back_populates='user', foreign_keys='SnowLog.user_id')
    marked_attendance = db.relationship('AttendanceRecord', foreign_keys='AttendanceRecord.marked_by_user_id')

