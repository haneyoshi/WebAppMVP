# models/event.py

from app import db

class Event(db.Model):
    __tablename__ = 'events'

    event_id = db.Column(db.Integer, primary_key=True)
    building_id = db.Column(db.Integer, db.ForeignKey('buildings.building_id'), nullable=False)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)

    building = db.relationship('Building')
    created_by = db.relationship('User')
