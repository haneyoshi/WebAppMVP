from app import db
from app.time_utils import utc_now

class SupplyItem(db.Model):
    __tablename__ = 'supply_items'

    item_id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String, nullable=False)
    category = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    request_items = db.relationship('SupplyRequestItem', back_populates='item')
