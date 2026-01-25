from app.extensions import db
from uuid import uuid4
from datetime import datetime, timezone, date as date_type
import json


class UserWeeklyProfile(db.Model):
    """
    Speichert wöchentliche Analysen des Benutzerverhaltens
    """
    __tablename__ = 'user_weekly_profiles'
    
    # Primary Key
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Foreign Key
    user_id = db.Column(db.String(), db.ForeignKey('users.id'), nullable=False)
    
    # Zeitraum der Analyse
    week_start_date = db.Column(db.Date, nullable=False)
    week_end_date = db.Column(db.Date, nullable=False)
    
    # Analysierte Features (JSON)
    features = db.Column(db.Text, nullable=False)  # JSON string
    
    # Metadaten
    analyzed_entries_count = db.Column(db.Integer, default=0)
    confidence_score = db.Column(db.Float)  # Optional: Wie sicher ist die Analyse
    
    # Audit
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), 
                          onupdate=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<UserWeeklyProfile user={self.user_id} week={self.week_start_date}>"
    
    def set_features(self, features_dict):
        """
        Speichert Features als JSON string
        """
        self.features = json.dumps(features_dict, ensure_ascii=False)
    
    def get_features(self):
        """
        Gibt Features als Dictionary zurück
        """
        if not self.features:
            return None
        try:
            return json.loads(self.features)
        except json.JSONDecodeError:
            return None
    
    @classmethod
    def get_latest_profile(cls, user_id):
        """
        Holt das neueste Profil für einen Benutzer
        """
        return cls.query.filter_by(user_id=user_id)\
            .order_by(cls.week_end_date.desc())\
            .first()
    
    @classmethod
    def get_profile_for_week(cls, user_id, week_start):
        """
        Holt das Profil für eine bestimmte Woche
        """
        return cls.query.filter_by(
            user_id=user_id,
            week_start_date=week_start
        ).first()
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'week_start_date': self.week_start_date.isoformat(),
            'week_end_date': self.week_end_date.isoformat(),
            'features': self.get_features(),
            'analyzed_entries_count': self.analyzed_entries_count,
            'confidence_score': self.confidence_score,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }