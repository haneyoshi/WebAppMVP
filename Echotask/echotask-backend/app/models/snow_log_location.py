# models/snow_log_location.py

from app import db

class SnowLogLocation(db.Model):
    __tablename__ = 'snow_log_locations'

    snow_log_location_id = db.Column(db.Integer, primary_key=True)
    area_id = db.Column(db.Integer, db.ForeignKey('areas.area_id'), nullable=False)
    location_name = db.Column(db.String, nullable=False)

    area = db.relationship('Area', back_populates='snow_log_locations')
    snow_logs = db.relationship('SnowLog', back_populates='location', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<SnowLogLocation {self.location_name} in Area {self.area_id}>"
