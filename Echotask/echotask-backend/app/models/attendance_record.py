# models/attendance_record.py

from app import db
from datetime import datetime

class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_records'

    attendance_record_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    attendance_date = db.Column(db.Date, nullable=False)
    present = db.Column(db.Boolean, nullable=False)
    marked_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    marked_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id])
    marked_by = db.relationship('User', foreign_keys=[marked_by_user_id])

    # SQLAlchemy automatically does the JOIN in the background by using "db.relationship"

    __table_args__ = (
        db.UniqueConstraint('user_id', 'attendance_date', name='uq_user_attendance_date'),
        # Each user can only have one attendance record per day.
    )
