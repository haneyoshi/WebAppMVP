from datetime import date

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from app import db
from app.auth import get_current_user, login_required, roles_required
from app.models.attendance_record import AttendanceRecord
from app.models.user import User


attendance_bp = Blueprint("attendance", __name__, url_prefix="/attendance")
ATTENDANCE_STATUSES = {"Working", "Away", "Assigned elsewhere"}


def _serialize_attendance(record, include_private=False):
    result = {
        "attendance_record_id": record.attendance_record_id,
        "user_id": record.user_id,
        "user_name": record.user.name,
        "attendance_date": record.attendance_date.isoformat(),
        "status": record.status,
        "marked_by_user_id": record.marked_by_user_id,
        "marked_by_name": record.marked_by.name if record.marked_by else None,
        "marked_at": record.marked_at.isoformat() if record.marked_at else None,
    }
    if include_private:
        result["absence_reason"] = record.absence_reason
    return result


def _parse_filters(query):
    attendance_date = request.args.get("date")
    if attendance_date:
        try:
            query = query.filter_by(attendance_date=date.fromisoformat(attendance_date))
        except ValueError:
            return None, (jsonify({"error": "date must use YYYY-MM-DD format"}), 400)

    user_id = request.args.get("user_id")
    if user_id is not None:
        try:
            query = query.filter_by(user_id=int(user_id))
        except ValueError:
            return None, (jsonify({"error": "user_id must be an integer"}), 400)
    return query, None


def _official_values(data):
    user_id = data.get("user_id")
    status = data.get("status")
    absence_reason = data.get("absence_reason")
    attendance_date = data.get("attendance_date", date.today().isoformat())

    if not isinstance(user_id, int) or isinstance(user_id, bool):
        return None, (jsonify({"error": "user_id must be an integer"}), 400)
    if status not in ATTENDANCE_STATUSES:
        return None, (jsonify({"error": "status must be Working, Away, or Assigned elsewhere"}), 400)
    if absence_reason is not None and not isinstance(absence_reason, str):
        return None, (jsonify({"error": "absence_reason must be a string or null"}), 400)
    try:
        attendance_date = date.fromisoformat(attendance_date)
    except (TypeError, ValueError):
        return None, (jsonify({"error": "attendance_date must use YYYY-MM-DD format"}), 400)
    if not db.session.get(User, user_id):
        return None, (jsonify({"error": "user_id not found"}), 404)

    return {
        "user_id": user_id,
        "attendance_date": attendance_date,
        "status": status,
        "present": status != "Away",
        "absence_reason": absence_reason.strip() if isinstance(absence_reason, str) else None,
    }, None


@attendance_bp.route("", methods=["GET"])
@login_required
def get_attendance():
    current_user = get_current_user()
    query = AttendanceRecord.query
    if current_user.role == "worker":
        query = query.filter_by(user_id=current_user.user_id)
    query, error = _parse_filters(query)
    if error:
        return error

    records = query.order_by(
        AttendanceRecord.attendance_date.desc(),
        AttendanceRecord.attendance_record_id.desc(),
    ).all()
    return jsonify([_serialize_attendance(record, include_private=True) for record in records])


@attendance_bp.route("/<int:attendance_record_id>", methods=["GET"])
@login_required
def get_attendance_record(attendance_record_id):
    record = db.session.get(AttendanceRecord, attendance_record_id)
    if not record:
        return jsonify({"error": "Attendance record not found"}), 404
    current_user = get_current_user()
    if current_user.role == "worker" and record.user_id != current_user.user_id:
        return jsonify({"error": "Forbidden"}), 403
    return jsonify(_serialize_attendance(record, include_private=True))


@attendance_bp.route("/check-in", methods=["POST"])
@roles_required("worker")
def check_in():
    current_user = get_current_user()
    record = AttendanceRecord(
        user_id=current_user.user_id,
        attendance_date=date.today(),
        present=True,
        status="Working",
        marked_by_user_id=current_user.user_id,
    )
    db.session.add(record)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Already checked in."}), 409
    return jsonify(_serialize_attendance(record, include_private=True)), 201


@attendance_bp.route("", methods=["POST"])
@roles_required("coordinator", "supervisor")
def mark_official_attendance():
    values, error = _official_values(request.get_json(silent=True) or {})
    if error:
        return error
    record = AttendanceRecord(**values, marked_by_user_id=get_current_user().user_id)
    db.session.add(record)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Attendance already exists for this user and date"}), 409
    return jsonify(_serialize_attendance(record, include_private=True)), 201


@attendance_bp.route("/<int:attendance_record_id>", methods=["PATCH"])
@roles_required("coordinator", "supervisor")
def correct_official_attendance(attendance_record_id):
    record = db.session.get(AttendanceRecord, attendance_record_id)
    if not record:
        return jsonify({"error": "Attendance record not found"}), 404
    data = request.get_json(silent=True) or {}
    data["user_id"] = record.user_id
    data["attendance_date"] = record.attendance_date.isoformat()
    values, error = _official_values(data)
    if error:
        return error
    record.status = values["status"]
    record.present = values["present"]
    record.absence_reason = values["absence_reason"]
    record.marked_by_user_id = get_current_user().user_id
    db.session.commit()
    return jsonify(_serialize_attendance(record, include_private=True))
