from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import date

from app.models import JournalEntry, User
from app.services.ai_service import AIService
from app.extensions import db

journal_bp = Blueprint('journal', __name__)


@journal_bp.route('/', methods=['POST'])
@jwt_required()
def create_journal_entry():
    try:
        username = get_jwt_identity()
        user = User.find_by_username(username=username)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()

        required_fields = ['mood', 'what_went_well', 'what_to_improve', 'how_i_feel']
        if not data or not all(k in data for k in required_fields):
            return jsonify({
                'error': 'Missing required fields',
                'required': required_fields
            }), 400

        mood = data.get("mood")
        valid_moods = [
            "Excited",
            "Happy",
            "Calm",
            "Focused",
            "Tired",
            "Sad",
            "Stressed",
            "Angry",
        ]

        if not isinstance(mood, str) or mood not in valid_moods:
            return (
                jsonify({"error": "Mood must be one of: " + ", ".join(valid_moods)}),
                400,
            )

        entry_text = f"""
PAST (heute, bereits passiert):
- What went well: {data['what_went_well']}

FUTURE (Plan / Verbesserung für morgen oder die Zukunft, noch NICHT passiert):
- What to improve / Tomorrow plan: {data['what_to_improve']}

CURRENT (jetzt):
- How I feel right now: {data['how_i_feel']}
""".strip()

        ai_summary = None
        emotion_detected = None

        try:
            summary, error = AIService.analyze_journal_entry(entry_text)
            if not error and summary:
                ai_summary = summary
        except Exception as e:
            print(f"AI Analysis failed: {e}")

        try:
            emotion_detected = AIService.detect_emotion_simple(data['how_i_feel'])
        except Exception as e:
            print(f"Emotion detection failed: {e}")
            emotion_detected = "unknown"

        entry = JournalEntry(
            user_id=user.id,
            date=date.today(),
            mood=mood,
            what_went_well=data['what_went_well'],
            what_to_improve=data['what_to_improve'],
            how_i_feel=data['how_i_feel'],
            ai_summary=ai_summary,
            emotion_detected=emotion_detected
        )

        db.session.add(entry)
        db.session.commit()

        return jsonify({
            'message': 'Journal entry created successfully',
            'entry': entry.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@journal_bp.route('/history', methods=['GET'])
@jwt_required()
def get_journal_history():
    try:
        username = get_jwt_identity()
        user = User.find_by_username(username=username)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        limit = request.args.get('limit', type=int, default=30)
        offset = request.args.get('offset', type=int, default=0)

        if limit < 1 or limit > 100:
            limit = 30
        if offset < 0:
            offset = 0

        entries = (JournalEntry.query
                   .filter_by(user_id=user.id)
                   .order_by(JournalEntry.date.desc())
                   .limit(limit)
                   .offset(offset)
                   .all())

        total_count = JournalEntry.query.filter_by(user_id=user.id).count()

        return jsonify({
            'entries': [entry.to_dict() for entry in entries],
            'count': len(entries),
            'total': total_count,
            'limit': limit,
            'offset': offset
        }), 200

    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@journal_bp.route('/<entry_id>', methods=['GET'])
@jwt_required()
def get_journal_entry(entry_id):
    try:
        username = get_jwt_identity()
        user = User.find_by_username(username=username)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        entry = JournalEntry.query.filter_by(id=entry_id, user_id=user.id).first()
        if not entry:
            return jsonify({'error': 'Journal entry not found'}), 404

        return jsonify({'entry': entry.to_dict()}), 200

    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@journal_bp.route('/<entry_id>', methods=['PUT'])
@jwt_required()
def update_journal_entry(entry_id):
    try:
        username = get_jwt_identity()
        user = User.find_by_username(username=username)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        entry = JournalEntry.query.filter_by(id=entry_id, user_id=user.id).first()
        if not entry:
            return jsonify({'error': 'Journal entry not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        updated = False

        if "mood" in data:
            valid_moods = [
                "Excited",
                "Happy",
                "Calm",
                "Focused",
                "Tired",
                "Sad",
                "Stressed",
                "Angry",
            ]
            if not isinstance(data["mood"], str) or data["mood"] not in valid_moods:
                return (
                    jsonify(
                        {"error": "Mood must be one of: " + ", ".join(valid_moods)}
                    ),
                    400,
                )
            entry.mood = data["mood"]
            updated = True

        if 'what_went_well' in data:
            entry.what_went_well = data['what_went_well']
            updated = True

        if 'what_to_improve' in data:
            entry.what_to_improve = data['what_to_improve']
            updated = True

        if 'how_i_feel' in data:
            entry.how_i_feel = data['how_i_feel']
            updated = True
            try:
                entry.emotion_detected = AIService.detect_emotion_simple(data['how_i_feel'])
            except Exception:
                pass

        if not updated:
            return jsonify({'error': 'No valid fields to update'}), 400

        db.session.commit()

        return jsonify({
            'message': 'Journal entry updated successfully',
            'entry': entry.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@journal_bp.route('/<entry_id>', methods=['DELETE'])
@jwt_required()
def delete_journal_entry(entry_id):
    try:
        username = get_jwt_identity()
        user = User.find_by_username(username=username)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        entry = JournalEntry.query.filter_by(id=entry_id, user_id=user.id).first()
        if not entry:
            return jsonify({'error': 'Journal entry not found'}), 404

        db.session.delete(entry)
        db.session.commit()

        return jsonify({
            'message': 'Journal entry deleted successfully',
            'deleted_id': entry_id
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@journal_bp.route("/suggestions", methods=["GET"])
@jwt_required()
def get_task_suggestions():
    """
    Gibt intelligente Aufgabenvorschläge für morgen zurück,
    basierend auf AI-Musteranalyse der letzten 3 Wochen.
    """
    try:
        from app.services.pattern_service import SmartPatternService
        from app import models

        username = get_jwt_identity()
        user = User.find_by_username(username=username)

        if not user:
            return jsonify({"error": "Benutzer nicht gefunden"}), 404

        # Rufe den intelligenten Service auf
        suggestions = SmartPatternService.get_suggestions_for_tomorrow(user.id, models)

        return (
            jsonify(
                {
                    "suggestions": suggestions,
                    "count": len(suggestions),
                    "generated_at": date.today().isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        print(f"Fehler beim Abrufen der Vorschläge: {str(e)}")
        return jsonify({"error": f"Server-Fehler: {str(e)}"}), 500
