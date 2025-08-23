from app import db
from datetime import datetime

class Area(db.Model):
    __tablename__ = 'areas'

    area_id = db.Column(db.Integer, primary_key=True)
    area_name = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)
    building_id = db.Column(db.Integer, db.ForeignKey('buildings.building_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    building = db.relationship('Building', back_populates='areas')
    user = db.relationship('User', uselist=False)
    snow_log_locations = db.relationship('SnowLogLocation', back_populates='area', cascade='all, delete-orphan')

