from flask import Blueprint, jsonify, request

from app import db
from app.models.area import Area
from app.models.building import Building
from app.auth import login_required


locations_bp = Blueprint("locations", __name__)


def _serialize_area(area):
    return {
        "area_id": area.area_id,
        "area_name": area.area_name,
        "description": area.description,
        "building_id": area.building_id,
        "building_name": area.building.building_name,
        "assigned_user_id": area.user.user_id if area.user else None,
    }


@locations_bp.route("/buildings", methods=["GET"])
@login_required
def list_buildings():
    buildings = Building.query.order_by(Building.building_name.asc()).all()
    return jsonify([
        {
            "building_id": building.building_id,
            "building_name": building.building_name,
            "area_count": len(building.areas),
        }
        for building in buildings
    ])


@locations_bp.route("/buildings/<int:building_id>", methods=["GET"])
@login_required
def get_building(building_id):
    building = db.session.get(Building, building_id)
    if not building:
        return jsonify({"error": "Building not found"}), 404

    return jsonify({
        "building_id": building.building_id,
        "building_name": building.building_name,
        "areas": [_serialize_area(area) for area in sorted(
            building.areas, key=lambda area: area.area_name
        )],
    })


@locations_bp.route("/areas", methods=["GET"])
@login_required
def list_areas():
    query = Area.query
    building_id = request.args.get("building_id")
    if building_id is not None:
        try:
            building_id = int(building_id)
        except ValueError:
            return jsonify({"error": "building_id must be an integer"}), 400
        query = query.filter_by(building_id=building_id)

    return jsonify([
        _serialize_area(area)
        for area in query.order_by(Area.area_name.asc()).all()
    ])


@locations_bp.route("/areas/<int:area_id>", methods=["GET"])
@login_required
def get_area(area_id):
    area = db.session.get(Area, area_id)
    if not area:
        return jsonify({"error": "Area not found"}), 404
    return jsonify(_serialize_area(area))
