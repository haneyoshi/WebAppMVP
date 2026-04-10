from app import db
from datetime import datetime

class Building(db.Model):
    __tablename__ = 'buildings'

    building_id = db.Column(db.Integer, primary_key=True)
    building_name = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    areas = db.relationship('Area', back_populates='building', cascade="all, delete-orphan")
    # the value of back_populates points to the attribute name in the related model that defines the other side of the relationship. In this case, it points to the building attribute in the Area model.
    #'Area' is the Model class name.