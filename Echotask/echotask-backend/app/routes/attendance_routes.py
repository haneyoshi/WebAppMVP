from flask import Blueprint, request, jsonify
from app.models.attendance_record import AttendanceRecord
from app import db
# db = SQLAlchemy() from app/__init__.py
#   -> reusing that same SQLAlchemy instance — the one that's already connected to your app.
from datetime import datetime

attendance_bp = Blueprint('attendance', __name__)

# GET: Fetch all attendance records
@attendance_bp.route("/attendance", methods=["GET"])
def get_attendance():
    records = AttendanceRecord.query.all()
    # "query", a SQLAlchemy feature that lets you search that table.
    # "all" fetches all rows from the table.
    result = []
    for record in records:
        result.append({
            "attendance_record_id": record.attendance_record_id,
            "user_id": record.user_id,
            "user_name": record.user.name,
            # !! altough attendance model doesn't have "user name" attribute. Becasue of "db.relationship()", this model record can access the name attribute in user model
            "attendance_date": record.attendance_date.isoformat(),
            "marked_by_user_id": record.marked_by_user_id,
            "marked_by_name": record.marked_by.name if record.marked_by else None,
            "marked_at": record.marked_at.isoformat()
        })
    return jsonify(result)
    # jsonify() converts it(csv) to JSON

# POST: Submit a new attendance record
@attendance_bp.route("/attendance", methods=["POST"])
def mark_attendance():
    data = request.get_json()
    # this grabs the JSON sent from frontend
    user_id = data.get("user_id")
    # pull values manually
    present = data.get("present")
    marked_by = data.get("marked_by_user_id")

    #now create new record and assign each attribue
    new_record = AttendanceRecord(
        user_id=user_id,
        attendance_date=datetime.utcnow().date(),
        present=present,
        marked_by_user_id=marked_by,
        marked_at=datetime.utcnow()
    )
    db.session.add(new_record)
    db.session.commit()

    return jsonify({"message": "Attendance marked successfully"}), 201
