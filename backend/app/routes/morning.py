from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, MorningSession, JournalEntry
from app.services.ai_service import AIService
from app.services.weather_service import WeatherService
from app.services.weekly_analysis_service import WeeklyAnalysisService
from app.extensions import db
from datetime import date

morning_bp = Blueprint('morning', __name__)


@morning_bp.route('/plan', methods=['GET'])
@jwt_required()
def get_morning_plan():
    """
    Generiert personalisierten Morgenplan
    NEU: Integriert wöchentliches Profil für bessere Personalisierung
    """
    try:
        username = get_jwt_identity()
        user = User.find_by_username(username=username)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        today = date.today()
        
        force_regenerate = request.args.get('force', 'false').lower() == 'true'
        
        # Prüfen ob Plan existiert
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
                'cached': True,
                'personalized': False  # Alter Plan, ohne Profil
            }), 200
        
        # Neuen Plan generieren
        print(f"Generating new morning plan for {user.username}...")
        
        # 1. Wetter holen
        weather_info, weather_error = WeatherService.get_weather(user.city)
        weather_string = WeatherService.format_weather_string(weather_info) if weather_info else "Wetter nicht verfügbar"
        
        if weather_error:
            print(f"Weather API warning: {weather_error}")
        
        # 2. Letzte Tagebucheinträge
        recent_entries = JournalEntry.query.filter_by(user_id=user.id)\
            .order_by(JournalEntry.date.desc())\
            .limit(3)\
            .all()
        
        last_entries_summary = None
        if recent_entries:
            entries_text = []
            for entry in recent_entries:
                mood_emoji = "😊" if entry.mood and entry.mood >= 4 else "😐" if entry.mood == 3 else "😔"
                entries_text.append(
                    f"{entry.date.strftime('%d.%m.')}: {mood_emoji} Stimmung {entry.mood}/5"
                )
            last_entries_summary = "\n".join(entries_text)
        
        # 3. Schlaf-Daten
        sleep_hours = request.args.get('sleep_hours', type=float)
        if not sleep_hours:
            sleep_hours = user.sleep_goal_hours
        
        # *** NEU: Weekly Profile holen ***
        weekly_profile_features = WeeklyAnalysisService.get_user_latest_profile(user.id)
        
        profile_used = False
        if weekly_profile_features:
            print(f"✅ Using weekly profile for personalization")
            profile_used = True
        else:
            print("ℹ️ No weekly profile available")
        
        # 4. Plan generieren (mit Weekly Profile)
        plan, error = AIService.generate_morning_plan(
            user_name=user.username,
            city=user.city,
            weather=weather_string,
            sleep_hours=sleep_hours,
            last_entries=last_entries_summary,
            weekly_profile=weekly_profile_features  # NEU!
        )
        
        if error:
            return jsonify({'error': f'Failed to generate plan: {error}'}), 500
        
        if not plan:
            return jsonify({'error': 'AI returned empty plan'}), 500
        
        # 5. Session speichern oder updaten
        if existing_session and force_regenerate:
            existing_session.plan_text = plan
            existing_session.weather = weather_string
            existing_session.sleep_duration = sleep_hours
            session = existing_session
        else:
            # Neue Session
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
            'personalized': profile_used,  # NEU: Zeigt an ob Profil verwendet wurde
            'profile_summary': WeeklyAnalysisService.format_profile_summary(weekly_profile_features) if weekly_profile_features else None
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in get_morning_plan: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@morning_bp.route('/history', methods=['GET'])
@jwt_required()
def get_morning_history():
    """
    Holt Historie der Morgenpläne
    """
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
        
        sessions = MorningSession.query.filter_by(user_id=user.id)\
            .order_by(MorningSession.date.desc())\
            .limit(limit)\
            .offset(offset)\
            .all()
        
        total_count = MorningSession.query.filter_by(user_id=user.id).count()
        
        return jsonify({
            'sessions': [session.to_dict() for session in sessions],
            'count': len(sessions),
            'total': total_count,
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@morning_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_morning_stats():
    """
    Statistiken über Morgenpläne
    """
    try:
        username = get_jwt_identity()
        user = User.find_by_username(username=username)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        sessions = MorningSession.query.filter_by(user_id=user.id).all()
        
        if not sessions:
            return jsonify({
                'total_sessions': 0,
                'average_sleep': None,
                'streak': 0
            }), 200
        
        # Durchschnittlicher Schlaf
        sleep_durations = [s.sleep_duration for s in sessions if s.sleep_duration is not None]
        avg_sleep = sum(sleep_durations) / len(sleep_durations) if sleep_durations else None
        
        # Streak berechnen
        from datetime import timedelta
        sorted_sessions = sorted(sessions, key=lambda x: x.date, reverse=True)
        streak = 0
        current_date = date.today()
        
        for session in sorted_sessions:
            if session.date == current_date:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break
        
        return jsonify({
            'total_sessions': len(sessions),
            'average_sleep': round(avg_sleep, 1) if avg_sleep else None,
            'streak': streak,
            'latest_session_date': sorted_sessions[0].date.isoformat() if sorted_sessions else None
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500