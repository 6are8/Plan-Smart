from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import User, JournalEntry, MorningSession, EveningPrompt
from app.extensions import db

history_bp = Blueprint("history", __name__)


@history_bp.route("", methods=["GET"])
@jwt_required()
def get_history():
    """
    Returns aggregated history data.
    
    Frontend expects:
    {
        "morning_sessions": [...],
        "journal_entries": [...],  // ← Frontend uses this
        "evening_prompts": [...],
        "limit": 30
    }
    """
    try:
        username = get_jwt_identity()
        user = User.find_by_username(username=username)

        if not user:
            return jsonify({"error": "User not found"}), 404

        limit = request.args.get("limit", type=int, default=30)
        if limit < 1 or limit > 100:
            limit = 30

        # Fetch all 3 types of entries
        morning_sessions = (MorningSession.query
                           .filter_by(user_id=user.id)
                           .order_by(MorningSession.date.desc())
                           .limit(limit)
                           .all())

        journal_entries = (JournalEntry.query
                          .filter_by(user_id=user.id)
                          .order_by(JournalEntry.date.desc())
                          .limit(limit)
                          .all())

        evening_prompts = (EveningPrompt.query
                          .filter_by(user_id=user.id)
                          .order_by(EveningPrompt.date.desc())
                          .limit(limit)
                          .all())

        return jsonify({
            "morning_sessions": [s.to_dict() for s in morning_sessions],
            "journal_entries": [e.to_dict() for e in journal_entries],
            "evening_prompts": [p.to_dict() for p in evening_prompts],
            "limit": limit
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Server error: {str(e)}"}), 500