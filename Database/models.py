from extensions import db
from uuid import uuid4
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, datetime, timezone


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(), primary_key=True, default=lambda: str(uuid4()))
    username = db.Column(db.String(), nullable=False, unique=True)
    city = db.Column(db.String(100), nullable=False)  
    password = db.Column(db.Text())

    journal_entries = db.relationship(
    'JournalEntry',
    backref='user',
    lazy=True,
    cascade="all, delete-orphan"
)


    def __repr__(self):
        return f"<User {self.username}>"
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).first()
    
    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()    


class TokenBlocklist(db.Model):
    __tablename__ = 'token_blocklist'
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(), nullable=False, index=True)
    created_at = db.Column(db.DateTime(), default=datetime.utcnow)

    def __repr__(self):
        return f"<TokenBlocklist {self.jti}>" 
    
    def save(self):
        db.session.add(self)
        db.session.commit()




class JournalEntry(db.Model):
    __tablename__ = 'journal_entries'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.String(),
        db.ForeignKey('users.id'),
        nullable=False
    )

    date = db.Column(db.Date, nullable=False)

    mood = db.Column(db.Integer)  # 1–5

    morning_plan = db.Column(db.Text)
    evening_reflection = db.Column(db.Text)

    ai_summary = db.Column(db.Text)
    emotion_detected = db.Column(db.String(50))

    sleep_duration = db.Column(db.Float)        
    weather = db.Column(db.String(100)) 

    created_at = db.Column(db.DateTime(), default=lambda: datetime.now(timezone.utc))


    def __repr__(self):
        return f"<JournalEntry user={self.user_id} date={self.date}>"


    @classmethod
    def get_or_create_today(cls, user_id):
        today = date.today()
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


    def get_journal_history(self, limit=10):
        return (
            JournalEntry.query
            .filter_by(user_id=self.user_id)
            .order_by(JournalEntry.date.desc())
            .limit(limit)
            .all()
        )
    
    def set_sleep_duration(self, hours: float):
        self.sleep_duration = hours
        db.session.commit()


    def set_weather(self, weather: str):
        self.weather = weather
        db.session.commit()


