from datetime import date

from flask import Blueprint, jsonify, request

from app.auth import login_required
from app.models.assignment import Assignment
from app.models.attendance_record import AttendanceRecord
from app.models.user import User


availability_bp = Blueprint("availability", __name__, url_prefix="/workers/availability")


@availability_bp.route("", methods=["GET"])
@login_required
def worker_availability():
    requested_date = request.args.get("date", date.today().isoformat())
    try:
        requested_date = date.fromisoformat(requested_date)
    except ValueError:
        return jsonify({"error": "date must use YYYY-MM-DD format"}), 400

    workers = User.query.filter_by(role="worker", is_active=True).order_by(User.name).all()
    attendance = {
        record.user_id: record
        for record in AttendanceRecord.query.filter_by(attendance_date=requested_date).all()
    }
    assignments_by_worker = {worker.user_id: [] for worker in workers}
    assignments = Assignment.query.filter_by(assignment_date=requested_date).all()
    for assignment in assignments:
        summary = {
            "assignment_id": assignment.assignment_id,
            "assignment_type": assignment.assignment_type,
            "location_task": assignment.location_task,
            "note": assignment.note,
        }
        for worker in assignment.workers:
            if worker.user_id in assignments_by_worker:
                assignments_by_worker[worker.user_id].append(summary)

    output = []
    for worker in workers:
        worker_assignments = assignments_by_worker[worker.user_id]
        record = attendance.get(worker.user_id)
        status = "Assigned elsewhere" if worker_assignments else (
            record.status if record else "Away"
        )
        output.append({
            "user_id": worker.user_id,
            "name": worker.name,
            "status": status,
            "regular_area_id": worker.area_id,
            "regular_area_name": worker.area.area_name if worker.area else None,
            "assignments": worker_assignments,
        })
    return jsonify(output)
