from app.extensions import db
from uuid import uuid4
from datetime import datetime, timezone, date as date_type


class JournalEntry(db.Model):

    __tablename__ = 'journal_entries'

    # Primary Key
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))

    # Foreign Key
    user_id = db.Column(db.String(), db.ForeignKey('users.id'), nullable=False)

    # Date & Mood
    date = db.Column(db.Date, nullable=False, default=date_type.today)
    mood = db.Column(db.String(50))

    # Strukturierte Reflexion
    what_went_well = db.Column(db.Text)
    what_to_improve = db.Column(db.Text)
    how_i_feel = db.Column(db.Text)

    morning_plan = db.Column(db.Text)
    evening_reflection = db.Column(db.Text)

    # Ki
    ai_summary = db.Column(db.Text)
    emotion_detected = db.Column(db.String(50))

    # Context
    sleep_duration = db.Column(db.Float)
    weather = db.Column(db.String(100))

    # Audit
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<JournalEntry user={self.user_id} date={self.date}>"

    @classmethod
    def get_or_create_today(cls, user_id):
        today = date_type.today()
        entry = cls.query.filter_by(user_id=user_id, date=today).first()

        if entry:
            return entry

        entry = cls(user_id=user_id, date=today)
        db.session.add(entry)
        db.session.commit()
        return entry

    def update_reflection(self, mood, reflection):
        self.mood = mood
        self.evening_reflection = reflection
        db.session.commit()

    def set_morning_plan(self, plan):
        self.morning_plan = plan
        db.session.commit()

    def set_sleep_duration(self, hours):
        self.sleep_duration = hours
        db.session.commit()

    def set_weather(self, weather):
        self.weather = weather
        db.session.commit()

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'date': self.date.isoformat(),
            'mood': self.mood,
            'what_went_well': self.what_went_well,
            'what_to_improve': self.what_to_improve,
            'how_i_feel': self.how_i_feel,
            'morning_plan': self.morning_plan,
            'evening_reflection': self.evening_reflection,
            'ai_summary': self.ai_summary,
            'emotion_detected': self.emotion_detected,
            'sleep_duration': self.sleep_duration,
            'weather': self.weather,
            'created_at': self.created_at.isoformat()
        }
