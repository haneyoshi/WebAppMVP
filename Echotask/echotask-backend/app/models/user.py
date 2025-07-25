from app import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False)  # worker, coordinator, supervisor
    area_id = db.Column(db.Integer, db.ForeignKey('areas.area_id'), nullable=True)
    # db.ForeignKey() — defines a foreign key column (this tells SQLAlchemy where the relationship starts).
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    area = db.relationship('Area', back_populates='users')
    #db.relationship() — sets up a Python-level link between models (this tells SQLAlchemy how to access related records).
