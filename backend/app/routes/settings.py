from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import User
from app.extensions import db

settings_bp = Blueprint("settings", __name__)

@settings_bp.route("", methods=["GET"])
@jwt_required()
def get_settings():
    try:
        username = get_jwt_identity()
        user = User.find_by_username(username=username)

        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify({
            "user": {
                "username": user.username,
                "city": user.city,
                "sleep_goal_hours": user.sleep_goal_hours
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@settings_bp.route("/city", methods=["POST"])
@jwt_required()
def update_city():
    try:
        data = request.get_json(silent=True) or {}
        city = (data.get("city") or "").strip()

        if not city:
            return jsonify({"error": "City is required"}), 400

        username = get_jwt_identity()
        user = User.find_by_username(username=username)

        if not user:
            return jsonify({"error": "User not found"}), 404

        user.city = city
        db.session.commit()

        return jsonify({
            "message": "City updated",
            "user": {"username": user.username, "city": user.city, "sleep_goal_hours": user.sleep_goal_hours}
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@settings_bp.route("/notifications", methods=["POST"])
@jwt_required()
def update_notifications():
    """
    Attend par exemple:
    {
      "morning_time": "07:30",
      "evening_time": "21:00"
    }
    """
    try:
        data = request.get_json(silent=True) or {}
        morning_time = (data.get("morning_time") or "").strip()
        evening_time = (data.get("evening_time") or "").strip()

        if not morning_time or not evening_time:
            return jsonify({"error": "morning_time and evening_time are required"}), 400

        username = get_jwt_identity()
        user = User.find_by_username(username=username)

        if not user:
            return jsonify({"error": "User not found"}), 404

        user.morning_time = morning_time
        user.evening_time = evening_time

        db.session.commit()

        return jsonify({
            "message": "Notification times updated",
            "user": {
                "username": user.username,
                "city": user.city,
                "sleep_goal_hours": user.sleep_goal_hours,
                "morning_time": getattr(user, "morning_time", None),
                "evening_time": getattr(user, "evening_time", None),
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Server error: {str(e)}"}), 500
