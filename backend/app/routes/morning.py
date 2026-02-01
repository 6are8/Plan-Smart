from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import date

from app.models import User, MorningSession, JournalEntry
from app.services.ai_service import AIService
from app.services.weather_service import WeatherService
from app.extensions import db

morning_bp = Blueprint('morning', __name__)


@morning_bp.route('/plan', methods=['GET'])
@jwt_required()
def get_morning_plan():
    try:
        username = get_jwt_identity()
        user = User.find_by_username(username=username)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        today = date.today()
        force_regenerate = request.args.get('force', 'false').lower() == 'true'

        existing_session = MorningSession.query.filter_by(
            user_id=user.id,
            date=today
        ).first()

        if existing_session and not force_regenerate:
            return jsonify({
                'plan': existing_session.plan_text,
                'weather': existing_session.weather,
                'sleep_duration': existing_session.sleep_duration,
                'generated_at': existing_session.created_at.isoformat(),
                'cached': True
            }), 200

        # Weather
        weather_info, weather_error = WeatherService.get_weather(user.city)
        weather_string = WeatherService.format_weather_string(weather_info) if weather_info else "Wetter nicht verfügbar"
        if weather_error:
            print(f"Weather API warning: {weather_error}")

        # Last entries mood 
        recent_entries = (JournalEntry.query
                          .filter_by(user_id=user.id)
                          .order_by(JournalEntry.date.desc())
                          .limit(3)
                          .all())

        last_entries_summary = None
        if recent_entries:
            entries_text = []
            for entry in recent_entries:
                mood_emoji = "😊" if entry.mood and entry.mood >= 4 else "😐" if entry.mood == 3 else "😔"
                entries_text.append(f"{entry.date.strftime('%d.%m.')}: {mood_emoji} Stimmung {entry.mood}/5")
            last_entries_summary = "\n".join(entries_text)

        # Pull "tomorrow plan" from latest journal entry (what_to_improve)
        latest_entry = (JournalEntry.query
                        .filter_by(user_id=user.id)
                        .order_by(JournalEntry.date.desc())
                        .first())
        tomorrow_plan_text = latest_entry.what_to_improve if latest_entry and latest_entry.what_to_improve else None

        # Sleep
        sleep_hours = request.args.get('sleep_hours', type=float)
        if not sleep_hours:
            sleep_hours = user.sleep_goal_hours

        # Generate plan with tomorrow_plan
        plan, error = AIService.generate_morning_plan(
            user_name=user.username,
            city=user.city,
            weather=weather_string,
            sleep_hours=sleep_hours,
            last_entries=last_entries_summary,
            tomorrow_plan=tomorrow_plan_text
        )

        if error:
            return jsonify({'error': f'Failed to generate plan: {error}'}), 500
        if not plan:
            return jsonify({'error': 'AI returned empty plan'}), 500

        # Save or update session
        if existing_session and force_regenerate:
            existing_session.plan_text = plan
            existing_session.weather = weather_string
            existing_session.sleep_duration = sleep_hours
            session = existing_session
        else:
            session = MorningSession(
                user_id=user.id,
                date=today,
                plan_text=plan,
                weather=weather_string,
                sleep_duration=sleep_hours
            )
            db.session.add(session)

        db.session.commit()

        return jsonify({
            'plan': plan,
            'weather': weather_string,
            'weather_details': weather_info,
            'sleep_duration': sleep_hours,
            'generated_at': session.created_at.isoformat(),
            'cached': False,
            'tomorrow_plan_used': bool(tomorrow_plan_text)
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error in get_morning_plan: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500