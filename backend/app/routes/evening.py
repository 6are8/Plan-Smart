from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, MorningSession, EveningPrompt
from app.services.ai_service import AIService
from app.extensions import db
from datetime import date

evening_bp = Blueprint('evening', __name__)


@evening_bp.route('/prompt', methods=['GET'])
@jwt_required()
def get_evening_prompt():
    try:
        username = get_jwt_identity()
        user = User.find_by_username(username=username)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        today = date.today()
        
        # Prüfen ob Prompt existiert
        existing_prompt = EveningPrompt.query.filter_by(
            user_id=user.id,
            date=today
        ).first()
        
        if existing_prompt:
            return jsonify({
                'prompt': existing_prompt.prompt_text,
                'date': existing_prompt.date.isoformat(),
                'generated_at': existing_prompt.created_at.isoformat(),
                'pre_generated': True
            }), 200
        
        # Morning Plan holen
        morning_session = MorningSession.query.filter_by(
            user_id=user.id,
            date=today
        ).first()
        
        today_plan = morning_session.plan_text if morning_session else None
        
        # Prompt generieren
        prompt, error = AIService.generate_evening_reflection_prompt(
            user_name=user.username,
            today_plan=today_plan
        )
        
        if error:
            prompt = f"Hallo {user.username}! 🌙\n\nZeit für Reflexion!"
        
        # Speichern
        evening_prompt = EveningPrompt(
            user_id=user.id,
            date=today,
            prompt_text=prompt
        )
        db.session.add(evening_prompt)
        db.session.commit()
        
        return jsonify({
            'prompt': prompt,
            'date': today.isoformat(),
            'generated_at': evening_prompt.created_at.isoformat(),
            'pre_generated': False
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@evening_bp.route('/history', methods=['GET'])
@jwt_required()
def get_evening_history():
    try:
        username = get_jwt_identity()
        user = User.find_by_username(username=username)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        limit = request.args.get('limit', type=int, default=30)
        
        prompts = EveningPrompt.query.filter_by(user_id=user.id)\
            .order_by(EveningPrompt.date.desc())\
            .limit(limit)\
            .all()
        
        return jsonify({
            'prompts': [prompt.to_dict() for prompt in prompts],
            'count': len(prompts)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500