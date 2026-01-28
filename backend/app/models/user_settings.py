from app.extensions import db
from datetime import datetime, timezone

class UserSettings(db.Model):
    __tablename__ = "user_settings"

    user_id = db.Column(db.String(), db.ForeignKey("users.id"), primary_key=True)

    # HH:MM
    morning_time = db.Column(db.String(5), nullable=False, default="07:30")
    evening_time = db.Column(db.String(5), nullable=False, default="21:00")

    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "morning_time": self.morning_time,
            "evening_time": self.evening_time
        }
