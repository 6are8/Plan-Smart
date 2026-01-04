from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


class SchedulerService:
    def __init__(self, app=None):
        self.scheduler = BackgroundScheduler()
        self.app = app
        
    def init_app(self, app):
        self.app = app
        self.add_jobs()
        
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("✅ Scheduler started successfully")
    
    def add_jobs(self):

        # Morning Plans 
        self.scheduler.add_job(
            func=self.generate_morning_plans,
            trigger=CronTrigger(hour=6, minute=0),
            id='generate_morning_plans',
            name='Generate Morning Plans (06:00)',
            replace_existing=True
        )
        
        # Evening Data 
        self.scheduler.add_job(
            func=self.prepare_evening_data,
            trigger=CronTrigger(hour=20, minute=0),
            id='prepare_evening_data',
            name='Prepare Evening Data (20:00)',
            replace_existing=True
        )
        
        logger.info("✅ All scheduled jobs added")
    
    def generate_morning_plans(self):
        logger.info("🌅 Generating morning plans at 06:00")
        
        with self.app.app_context():
            from app.models import User, MorningSession, JournalEntry
            from app.services.ai_service import AIService
            from app.services.weather_service import WeatherService
            from app.extensions import db
            
            users = User.query.all()
            logger.info(f"Processing morning plans for {len(users)} users")
            
            success_count = 0
            error_count = 0
            
            for user in users:
                try:
                    today = date.today()
                    
                    # Prüfen ob Plan existiert
                    existing = MorningSession.query.filter_by(
                        user_id=user.id, 
                        date=today
                    ).first()
                    
                    if existing:
                        logger.info(f"User {user.username}: Plan already exists, skipping")
                        continue
                    
                    # Wetter holen
                    weather_info, weather_error = WeatherService.get_weather(user.city)
                    weather_string = WeatherService.format_weather_string(weather_info)
                    
                    if weather_error:
                        logger.warning(f"User {user.username}: Weather API error - {weather_error}")
                    
                    # Letzte Tagebucheinträge
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
                    
                    # Plan generieren
                    plan, error = AIService.generate_morning_plan(
                        user_name=user.username,
                        city=user.city,
                        weather=weather_string,
                        sleep_hours=user.sleep_goal_hours,
                        last_entries=last_entries_summary
                    )
                    
                    if error:
                        logger.error(f"User {user.username}: Failed to generate plan - {error}")
                        error_count += 1
                        continue
                    
                    if not plan:
                        logger.error(f"User {user.username}: AI returned empty plan")
                        error_count += 1
                        continue
                    
                    # Session speichern
                    session = MorningSession(
                        user_id=user.id,
                        date=today,
                        plan_text=plan,
                        weather=weather_string,
                        sleep_duration=user.sleep_goal_hours
                    )
                    db.session.add(session)
                    db.session.commit()
                    
                    success_count += 1
                    logger.info(f"✅ User {user.username}: Morning plan generated")
                    
                except Exception as e:
                    logger.error(f"User {user.username}: Morning plan generation error - {str(e)}")
                    db.session.rollback()
                    error_count += 1
                    continue
            
            logger.info(f"Morning plans generation completed: {success_count} success, {error_count} errors")
    
    def prepare_evening_data(self):
        logger.info("🌙 Preparing evening reflection data at 20:00")
        
        with self.app.app_context():
            from app.models import User, MorningSession, EveningPrompt
            from app.services.ai_service import AIService
            from app.extensions import db
            
            users = User.query.all()
            logger.info(f"Preparing evening data for {len(users)} users")
            
            success_count = 0
            
            for user in users:
                try:
                    today = date.today()
                    
                    # Prüfen ob existiert
                    existing = EveningPrompt.query.filter_by(
                        user_id=user.id,
                        date=today
                    ).first()
                    
                    if existing:
                        logger.info(f"User {user.username}: Evening prompt already exists")
                        continue
                    
                    # Heutiger Morning Plan holen
                    morning_session = MorningSession.query.filter_by(
                        user_id=user.id,
                        date=today
                    ).first()
                    
                    today_plan = morning_session.plan_text if morning_session else None
                    
                    # Reflexions-Prompt generieren
                    prompt, error = AIService.generate_evening_reflection_prompt(
                        user_name=user.username,
                        today_plan=today_plan
                    )
                    
                    if error:
                        prompt = f"Hallo {user.username}! 🌙\n\nWie war dein Tag heute? Zeit für eine kurze Reflexion!"
                    
                    # Evening Prompt speichern
                    evening_prompt = EveningPrompt(
                        user_id=user.id,
                        date=today,
                        prompt_text=prompt
                    )
                    db.session.add(evening_prompt)
                    db.session.commit()
                    
                    success_count += 1
                    logger.info(f"✅ User {user.username}: Evening prompt prepared")
                    
                except Exception as e:
                    logger.error(f"User {user.username}: Evening data preparation error - {str(e)}")
                    db.session.rollback()
                    continue
            
            logger.info(f"Evening data preparation completed: {success_count} prompts created")
    
    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler shut down")

scheduler_service = SchedulerService()