from app import db
from datetime import datetime

class SupplyRequest(db.Model):
    __tablename__ = 'supply_requests'

    request_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String, default='pending')  # pending, approved, fulfilled, etc.

    user = db.relationship('User')
    # We're only setting up a simple one-way relationship from SupplyRequest to the User
    # Essentially,We’re saying: "Each request has one user, and I want to access that user using request.user; User has no field associate with any items"
    items = db.relationship('SupplyRequestItem', back_populates='request', cascade="all, delete-orphan")
    # This tells SQLAlchemy what to do with child objects when their parent is deleted or modified.
    # That means, If a SupplyRequestItem is removed from its parent SupplyRequest, it should be deleted from the DB too. In other words, it can't exist on its own.
