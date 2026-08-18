from datetime import date

from flask import Blueprint, jsonify, request

from app import db
from app.auth import get_current_user, login_required, roles_required
from app.models.assignment import Assignment
from app.models.area import Area
from app.models.user import User


assignments_bp = Blueprint("assignments", __name__, url_prefix="/assignments")


def _serialize_assignment(assignment):
    return {
        "assignment_id": assignment.assignment_id,
        "assignment_date": assignment.assignment_date.isoformat(),
        "assignment_type": assignment.assignment_type,
        "location_task": assignment.location_task,
        "note": assignment.note,
        "destination_area_id": assignment.destination_area_id,
        "destination_area_name": (
            assignment.destination_area.area_name if assignment.destination_area else None
        ),
        "destination_building_id": (
            assignment.destination_area.building_id if assignment.destination_area else None
        ),
        "destination_building_name": (
            assignment.destination_area.building.building_name
            if assignment.destination_area else None
        ),
        "worker_ids": [worker.user_id for worker in assignment.workers],
        "workers": [
            {"user_id": worker.user_id, "name": worker.name}
            for worker in sorted(assignment.workers, key=lambda worker: worker.name)
        ],
        "created_by_user_id": assignment.created_by_user_id,
        "created_by_name": assignment.created_by.name,
    }


def _assignment_values(data):
    assignment_date = data.get("assignment_date")
    assignment_type = data.get("assignment_type")
    location_task = data.get("location_task")
    note = data.get("note")
    worker_ids = data.get("worker_ids")
    destination_area_id = data.get("destination_area_id")

    try:
        assignment_date = date.fromisoformat(assignment_date)
    except (TypeError, ValueError):
        return None, (jsonify({"error": "assignment_date must use YYYY-MM-DD format"}), 400)
    if not isinstance(assignment_type, str) or not assignment_type.strip():
        return None, (jsonify({"error": "assignment_type is required"}), 400)
    if not isinstance(location_task, str) or not location_task.strip():
        return None, (jsonify({"error": "location_task is required"}), 400)
    if note is not None and not isinstance(note, str):
        return None, (jsonify({"error": "note must be a string or null"}), 400)
    if not isinstance(worker_ids, list) or not worker_ids:
        return None, (jsonify({"error": "worker_ids must be a non-empty list"}), 400)
    if any(not isinstance(user_id, int) or isinstance(user_id, bool) for user_id in worker_ids):
        return None, (jsonify({"error": "worker_ids must contain integers"}), 400)
    if len(set(worker_ids)) != len(worker_ids):
        return None, (jsonify({"error": "worker_ids must not contain duplicates"}), 400)
    if destination_area_id is not None and (
        not isinstance(destination_area_id, int) or isinstance(destination_area_id, bool)
    ):
        return None, (jsonify({"error": "destination_area_id must be an integer or null"}), 400)

    destination_area = None
    if destination_area_id is not None:
        destination_area = db.session.get(Area, destination_area_id)
        if not destination_area:
            return None, (jsonify({"error": f"destination_area_id {destination_area_id} not found"}), 404)

    workers = User.query.filter(User.user_id.in_(worker_ids)).all()
    workers_by_id = {worker.user_id: worker for worker in workers}
    missing_ids = [user_id for user_id in worker_ids if user_id not in workers_by_id]
    if missing_ids:
        return None, (jsonify({"error": f"worker_id {missing_ids[0]} not found"}), 404)
    if any(worker.role != "worker" or not worker.is_active for worker in workers):
        return None, (jsonify({"error": "Assignments require active worker accounts"}), 400)

    return {
        "assignment_date": assignment_date,
        "assignment_type": assignment_type.strip(),
        "location_task": location_task.strip(),
        "note": note.strip() if isinstance(note, str) else None,
        "destination_area": destination_area,
        "workers": [workers_by_id[user_id] for user_id in worker_ids],
    }, None


@assignments_bp.route("", methods=["GET"])
@login_required
def list_assignments():
    query = Assignment.query
    assignment_date = request.args.get("date")
    if assignment_date:
        try:
            query = query.filter_by(assignment_date=date.fromisoformat(assignment_date))
        except ValueError:
            return jsonify({"error": "date must use YYYY-MM-DD format"}), 400

    worker_id = request.args.get("worker_id")
    if worker_id is not None:
        try:
            worker_id = int(worker_id)
        except ValueError:
            return jsonify({"error": "worker_id must be an integer"}), 400
        query = query.filter(Assignment.workers.any(user_id=worker_id))

    assignments = query.order_by(
        Assignment.assignment_date.desc(), Assignment.assignment_id.desc()
    ).all()
    return jsonify([_serialize_assignment(assignment) for assignment in assignments])


@assignments_bp.route("/<int:assignment_id>", methods=["GET"])
@login_required
def get_assignment(assignment_id):
    assignment = db.session.get(Assignment, assignment_id)
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404
    return jsonify(_serialize_assignment(assignment))


@assignments_bp.route("", methods=["POST"])
@roles_required("coordinator", "supervisor")
def create_assignment():
    values, error = _assignment_values(request.get_json(silent=True) or {})
    if error:
        return error
    workers = values.pop("workers")
    assignment = Assignment(**values, created_by_user_id=get_current_user().user_id)
    assignment.workers = workers
    db.session.add(assignment)
    db.session.commit()
    return jsonify(_serialize_assignment(assignment)), 201


@assignments_bp.route("/<int:assignment_id>", methods=["PUT"])
@roles_required("coordinator", "supervisor")
def update_assignment(assignment_id):
    assignment = db.session.get(Assignment, assignment_id)
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404
    values, error = _assignment_values(request.get_json(silent=True) or {})
    if error:
        return error
    assignment.workers = values.pop("workers")
    for field_name, value in values.items():
        setattr(assignment, field_name, value)
    db.session.commit()
    return jsonify(_serialize_assignment(assignment))
