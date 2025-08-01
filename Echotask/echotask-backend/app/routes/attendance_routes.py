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
            "id": record.attendance_record_id,
            "user_id": record.user_id,
            "date": record.attendance_date.isoformat(),
            "present": record.present,
            "marked_by": record.marked_by_user_id,
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
    present = data.get("present")
    marked_by = data.get("marked_by_user_id")

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
