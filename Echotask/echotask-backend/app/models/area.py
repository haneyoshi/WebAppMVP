from app import db
from app.time_utils import utc_now

class Area(db.Model):
    __tablename__ = 'areas'

    area_id = db.Column(db.Integer, primary_key=True)
    area_name = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)
    building_id = db.Column(db.Integer, db.ForeignKey('buildings.building_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    building = db.relationship('Building', back_populates='areas')
    # back_populates='areas' tells SQLAlchemy that the Building model has a relationship attribute named areas that corresponds to this relationship.
    
    user = db.relationship('User',back_populates='area', uselist=False)
    snow_log_locations = db.relationship('SnowLogLocation', back_populates='area', cascade='all, delete-orphan')
    supply_requests = db.relationship('SupplyRequest', back_populates='area')

