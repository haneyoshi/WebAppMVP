# Join table between supply request and items

from app import db

class SupplyRequestItem(db.Model):
    __tablename__ = 'supply_request_items'

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('supply_requests.request_id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('supply_items.item_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    request = db.relationship('SupplyRequest', back_populates='items')
    item = db.relationship('SupplyItem', back_populates='request_items')
