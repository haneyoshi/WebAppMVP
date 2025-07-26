# models/snow_log.py

from app import db
from datetime import datetime

class SnowLog(db.Model):
    __tablename__ = 'snow_logs'

    snow_log_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    snow_log_location_id = db.Column(db.Integer, db.ForeignKey('snow_log_locations.snow_log_location_id'), nullable=False)

    action_taken = db.Column(db.Text, nullable=True)
    condition = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User')
    location = db.relationship('SnowLogLocation', back_populates='snow_logs')
