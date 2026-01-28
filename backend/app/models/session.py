from app.extensions import db
from uuid import uuid4
from datetime import datetime, timezone, date as date_type


class MorningSession(db.Model):
    __tablename__ = 'morning_sessions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(db.String(), db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date_type.today)
    
    plan_text = db.Column(db.Text, nullable=False)
    
    # Context
    weather = db.Column(db.String(100))
    sleep_duration = db.Column(db.Float)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<MorningSession user={self.user_id} date={self.date}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'date': self.date.isoformat(),
            'plan_text': self.plan_text,
            'weather': self.weather,
            'sleep_duration': self.sleep_duration,
            'created_at': self.created_at.isoformat()
        }


class EveningPrompt(db.Model):

    __tablename__ = 'evening_prompts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(db.String(), db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date_type.today)
    
    prompt_text = db.Column(db.Text, nullable=False)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<EveningPrompt user={self.user_id} date={self.date}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'date': self.date.isoformat(),
            'prompt_text': self.prompt_text,
            'created_at': self.created_at.isoformat()
        }