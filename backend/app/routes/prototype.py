from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import date

from app.models import User, MorningSession, JournalEntry, EveningPrompt
from app.extensions import db

prototype_bp = Blueprint("prototype", __name__)

@prototype_bp.route("/today", methods=["GET"])
@jwt_required()
def today():
    username = get_jwt_identity()
    user = User.find_by_username(username=username)
    if not user:
        return jsonify({"error": "User not found"}), 404

    today_date = date.today()

    morning = MorningSession.query.filter_by(user_id=user.id, date=today_date).first()
    evening = EveningPrompt.query.filter_by(user_id=user.id, date=today_date).first()
    journal = JournalEntry.query.filter_by(user_id=user.id, date=today_date).first()

    return jsonify({
        "date": today_date.isoformat(),
        "user": user.to_dict(),
        "morning_plan": morning.to_dict() if morning else None,
        "evening_prompt": evening.to_dict() if evening else None,
        "journal_entry": journal.to_dict() if journal else None
    }), 200


@prototype_bp.route("/history", methods=["GET"])
@jwt_required()
def history():
    username = get_jwt_identity()
    user = User.find_by_username(username=username)
    if not user:
        return jsonify({"error": "User not found"}), 404

    limit = request.args.get("limit", type=int, default=10)

    morning_sessions = (MorningSession.query.filter_by(user_id=user.id)
                        .order_by(MorningSession.date.desc()).limit(limit).all())
    journal_entries = (JournalEntry.query.filter_by(user_id=user.id)
                       .order_by(JournalEntry.date.desc()).limit(limit).all())
    evening_prompts = (EveningPrompt.query.filter_by(user_id=user.id)
                       .order_by(EveningPrompt.date.desc()).limit(limit).all())

    return jsonify({
        "limit": limit,
        "morning_sessions": [s.to_dict() for s in morning_sessions],
        "journal_entries": [e.to_dict() for e in journal_entries],
        "evening_prompts": [p.to_dict() for p in evening_prompts]
    }), 200


@prototype_bp.route("/settings", methods=["GET"])
@jwt_required()
def settings():
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
