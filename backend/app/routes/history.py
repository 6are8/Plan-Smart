from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import User, JournalEntry
from app.extensions import db

history_bp = Blueprint("history", __name__)


@history_bp.route("/history", methods=["GET"])
@jwt_required()
def get_history():
    
    try:
        username = get_jwt_identity()
        user = User.find_by_username(username=username)

        if not user:
            return jsonify({"error": "User not found"}), 404

        limit = request.args.get("limit", type=int, default=30)
        if limit < 1 or limit > 100:
            limit = 30

        entries = (JournalEntry.query
                   .filter_by(user_id=user.id)
                   .order_by(JournalEntry.date.desc())
                   .limit(limit)
                   .all())

        return jsonify({
            "count": len(entries),
            "entries": [e.to_dict() for e in entries]
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Server error: {str(e)}"}), 500
