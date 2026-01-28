from app.extensions import db
from uuid import uuid4
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone


class User(db.Model):
   
    __tablename__ = 'users'
    
    # Primary Key
    id = db.Column(db.String(), primary_key=True, default=lambda: str(uuid4()))
    
    # Authentication
    username = db.Column(db.String(), nullable=False, unique=True)
    password = db.Column(db.Text(), nullable=False)
    
    # Profile
    city = db.Column(db.String(100), nullable=False)
    sleep_goal_hours = db.Column(db.Float, default=8.0)
    
    # Audit
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    journal_entries = db.relationship(
        'JournalEntry',
        backref='user',
        lazy=True,
        cascade="all, delete-orphan"
    )
    
    morning_sessions = db.relationship(
        'MorningSession',
        backref='user',
        lazy=True,
        cascade="all, delete-orphan"
    )
    
    evening_prompts = db.relationship(
        'EveningPrompt',
        backref='user',
        lazy=True,
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<User {self.username}>"
    
    # Password
    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    # Utility 
    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).first()
    
    def save(self):
        db.session.add(self)
        db.session.commit()
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()
    
    # Serialization
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'city': self.city,
            'sleep_goal_hours': self.sleep_goal_hours,
            'created_at': self.created_at.isoformat()
        }