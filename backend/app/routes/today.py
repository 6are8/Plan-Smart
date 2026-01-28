from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import date

from app.models import User
from app.models import MorningSession, JournalEntry, EveningPrompt  
from app.services.weather_service import WeatherService
from app.services.ai_service import AIService
from app.extensions import db

today_bp = Blueprint("today", __name__)


@today_bp.route("/today", methods=["GET"])
@jwt_required()
def get_today():
   
    try:
        username = get_jwt_identity()
        user = User.find_by_username(username=username)

        if not user:
            return jsonify({"error": "User not found"}), 404

        today = date.today()

        # Weather
        weather_info, weather_error = WeatherService.get_weather(user.city)
        weather_string = WeatherService.format_weather_string(weather_info) if weather_info else "Wetter nicht verfügbar"

        # Morning plan 
        session = MorningSession.query.filter_by(user_id=user.id, date=today).first()

        if not session:
            plan, error = AIService.generate_morning_plan(
                user_name=user.username,
                city=user.city,
                weather=weather_string,
                sleep_hours=user.sleep_goal_hours,
                last_entries=None
            )

            if error:
                plan = None  
            else:
                session = MorningSession(
                    user_id=user.id,
                    date=today,
                    plan_text=plan,
                    weather=weather_string,
                    sleep_duration=user.sleep_goal_hours
                )
                db.session.add(session)
                db.session.commit()

        # Evening prompt 
        evening_prompt = EveningPrompt.query.filter_by(user_id=user.id, date=today).first()

        # Quote placeholder
        quote = "„Kleine Schritte jeden Tag ergeben große Veränderungen.“"

        return jsonify({
            "date": today.isoformat(),
            "user": user.to_dict(),
            "weather": weather_string,
            "weather_details": weather_info,      
            "quote": quote,
            "plan": session.plan_text if session else None,
            "evening_prompt": evening_prompt.prompt_text if evening_prompt else None
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Server error: {str(e)}"}), 500
