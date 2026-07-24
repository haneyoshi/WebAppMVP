from app import db
from app.time_utils import utc_now


assignment_workers = db.Table(
    "assignment_workers",
    db.Column(
        "assignment_id",
        db.Integer,
        db.ForeignKey("assignments.assignment_id"),
        primary_key=True,
    ),
    db.Column(
        "user_id",
        db.Integer,
        db.ForeignKey("users.user_id"),
        primary_key=True,
    ),
)


class Assignment(db.Model):
    __tablename__ = "assignments"

    assignment_id = db.Column(db.Integer, primary_key=True)
    assignment_date = db.Column(db.Date, nullable=False)
    assignment_type = db.Column(db.String, nullable=False)
    location_task = db.Column(db.String, nullable=False)
    note = db.Column(db.Text, nullable=True)
    created_by_user_id = db.Column(
        db.Integer, db.ForeignKey("users.user_id"), nullable=False
    )
    created_at = db.Column(db.DateTime, default=utc_now)

    created_by = db.relationship("User", foreign_keys=[created_by_user_id])
    workers = db.relationship("User", secondary=assignment_workers)
