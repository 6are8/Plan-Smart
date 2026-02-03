import traceback
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import date


from app.models import User, MorningSession, JournalEntry, EveningPrompt, UserSettings
from app.services.weather_service import WeatherService
from app.services.ai_service import AIService
from app.extensions import db

today_bp = Blueprint("today", __name__)


@today_bp.route("", methods=["GET"])
@jwt_required()
def get_today():
    """
    Returns today's data in the format frontend expects:

    {
        "date": "2026-01-29",
        "user": {...},
        "morning_plan": {...} | null,
        "evening_prompt": {...} | null,
        "journal_entry": {...} | null
    }
    """
    try:
        username = get_jwt_identity()
        user = User.find_by_username(username=username)

        if not user:
            return jsonify({"error": "User not found"}), 404

        today_date = date.today()

        # Ensure settings exist
        settings = UserSettings.query.filter_by(user_id=user.id).first()
        if not settings:
            settings = UserSettings(user_id=user.id)
            db.session.add(settings)
            db.session.commit()

        # Morning plan session
        morning_session = MorningSession.query.filter_by(
            user_id=user.id, date=today_date
        ).first()

        if not morning_session:
            # Auto-generate morning plan if missing
            weather_info, weather_error = WeatherService.get_weather(user.city)
            weather_string = (
                WeatherService.format_weather_string(weather_info)
                if weather_info
                else "Wetter nicht verfügbar"
            )

            # Get latest tomorrow-plan from journal
            latest_entry = (
                JournalEntry.query.filter_by(user_id=user.id)
                .order_by(JournalEntry.date.desc())
                .first()
            )
            tomorrow_plan_text = (
                latest_entry.what_to_improve
                if latest_entry and latest_entry.what_to_improve
                else None
            )

            # Get last 3 entries for mood context
            recent_entries = (
                JournalEntry.query.filter_by(user_id=user.id)
                .order_by(JournalEntry.date.desc())
                .limit(3)
                .all()
            )

            last_entries_summary = None
            if recent_entries:
                entries_text = []
                for entry in recent_entries:
                    try:
                        mood_value = entry.mood

                        # ROBUST: Handle different mood types
                        if mood_value is None:
                            mood_emoji = "😐"
                        elif isinstance(mood_value, str):
                            # String mood (new system)
                            mood_map = {
                                "Excited": "⚡",
                                "Happy": "😄",
                                "Calm": "😌",
                                "Focused": "🎯",
                                "Tired": "😴",
                                "Sad": "😢",
                                "Stressed": "😖",
                                "Angry": "😠",
                            }
                            mood_emoji = mood_map.get(mood_value, "😐")
                        elif isinstance(mood_value, (int, float)):
                            # Numeric mood (old system)
                            mood_emoji = (
                                "😊"
                                if mood_value >= 4
                                else "😐" if mood_value == 3 else "😔"
                            )
                        else:
                            mood_emoji = "😐"

                        entries_text.append(
                            f"{entry.date.strftime('%d.%m.')}: {mood_emoji}"
                        )

                    except Exception as e:
                        print(f"⚠️ Error processing entry mood: {e}")
                        entries_text.append(f"{entry.date.strftime('%d.%m.')}: 😐")

                last_entries_summary = "\n".join(entries_text)

            plan, error = AIService.generate_morning_plan(
                user_name=user.username,
                city=user.city,
                weather=weather_string,
                sleep_hours=user.sleep_goal_hours,
                last_entries=last_entries_summary,
                tomorrow_plan=tomorrow_plan_text,
            )

            if not error and plan:
                morning_session = MorningSession(
                    user_id=user.id,
                    date=today_date,
                    plan_text=plan,
                    weather=weather_string,
                    sleep_duration=user.sleep_goal_hours,
                )
                db.session.add(morning_session)
                db.session.commit()

        # Evening prompt
        evening_prompt = EveningPrompt.query.filter_by(
            user_id=user.id, date=today_date
        ).first()

        if not evening_prompt:
            # Auto-generate evening prompt if missing
            today_plan = morning_session.plan_text if morning_session else None

            prompt, error = AIService.generate_evening_reflection_prompt(
                user_name=user.username, today_plan=today_plan
            )

            if not error and prompt:
                evening_prompt = EveningPrompt(
                    user_id=user.id, date=today_date, prompt_text=prompt
                )
                db.session.add(evening_prompt)
                db.session.commit()

        # Journal entry for today
        journal_entry = JournalEntry.query.filter_by(
            user_id=user.id, date=today_date
        ).first()

        # Return in format frontend expects
        return (
            jsonify(
                {
                    "date": today_date.isoformat(),
                    "user": user.to_dict(),
                    "morning_plan": (
                        morning_session.to_dict() if morning_session else None
                    ),
                    "evening_prompt": (
                        evening_prompt.to_dict() if evening_prompt else None
                    ),
                    "journal_entry": journal_entry.to_dict() if journal_entry else None,
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        print(f"Error in get_today: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500