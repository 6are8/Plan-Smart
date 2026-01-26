from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import JournalEntry, User
from app.services.ai_service import AIService
from app.extensions import db
from datetime import date

journal_bp = Blueprint('journal', __name__)


@journal_bp.route('/', methods=['POST'])
@jwt_required()
def create_journal_entry():
    try:
        # User aus JWT holen
        username = get_jwt_identity()
        user = User.find_by_username(username=username)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()

        # Validierung
        required_fields = ['mood', 'what_went_well', 'what_to_improve', 'how_i_feel']
        if not data or not all(k in data for k in required_fields):
            return jsonify({
                'error': 'Missing required fields',
                'required': required_fields
            }), 400

        # Mood validieren
        mood = data.get('mood')
        if not isinstance(mood, int) or mood < 1 or mood > 5:
            return jsonify({'error': 'Mood must be between 1 and 5'}), 400

        # Zusammenfassungstext für KI
        entry_text = f"""
        Was lief gut: {data['what_went_well']}
        Was kann verbessert werden: {data['what_to_improve']}
        Gefühle: {data['how_i_feel']}
        """

        # KI-Analyse
        ai_summary = None
        emotion_detected = None

        try:
            summary, error = AIService.analyze_journal_entry(entry_text)
            if not error and summary:
                ai_summary = summary
        except Exception as e:
            print(f"AI Analysis failed: {e}")

        # Emotion Detection
        try:
            emotion_detected = AIService.detect_emotion_simple(data['how_i_feel'])
        except Exception as e:
            print(f"Emotion detection failed: {e}")
            emotion_detected = "unknown"

        # Eintrag erstellen
        entry = JournalEntry(
            user_id=user.id,
            date=date.today(),
            mood=mood,
            what_went_well=data["what_went_well"],
            what_to_improve=data["what_to_improve"],
            how_i_feel=data["how_i_feel"],
            ai_summary=ai_summary,
            emotion_detected=emotion_detected,
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
        
        # Query parameter
        limit = request.args.get('limit', type=int, default=30)
        offset = request.args.get('offset', type=int, default=0)
        
        # Validierung
        if limit < 1 or limit > 100:
            limit = 30
        if offset < 0:
            offset = 0
        
        # Einträge abrufen
        entries = JournalEntry.query.filter_by(user_id=user.id)\
            .order_by(JournalEntry.date.desc())\
            .limit(limit)\
            .offset(offset)\
            .all()
        
        # Gesamtzahl
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
        
        # Update erlaubte Felder
        updated = False
        
        if 'mood' in data:
            if not isinstance(data['mood'], int) or data['mood'] < 1 or data['mood'] > 5:
                return jsonify({'error': 'Mood must be between 1 and 5'}), 400
            entry.mood = data['mood']
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
            
            # Re-detect emotion
            try:
                entry.emotion_detected = AIService.detect_emotion_simple(data['how_i_feel'])
            except:
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


@journal_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_journal_stats():
    try:
        username = get_jwt_identity()
        user = User.find_by_username(username=username)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        entries = JournalEntry.query.filter_by(user_id=user.id).all()
        
        if not entries:
            return jsonify({
                'total_entries': 0,
                'average_mood': None,
                'emotions': {}
            }), 200
        
        # Durchschnittliche Stimmung
        moods = [e.mood for e in entries if e.mood is not None]
        avg_mood = sum(moods) / len(moods) if moods else None
        
        # Emotionen zählen
        emotions = {}
        for entry in entries:
            if entry.emotion_detected:
                emotions[entry.emotion_detected] = emotions.get(entry.emotion_detected, 0) + 1
        
        return jsonify({
            'total_entries': len(entries),
            'average_mood': round(avg_mood, 2) if avg_mood else None,
            'emotions': emotions,
            'latest_entry_date': entries[0].date.isoformat() if entries else None
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500
