from app.routes.auth import auth_bp
from app.routes.journal import journal_bp
from app.routes.morning import morning_bp
from app.routes.evening import evening_bp
from app.routes.scheduler import scheduler_bp

__all__ = [
    'auth_bp',
    'journal_bp',
    'morning_bp',
    'evening_bp',
    'scheduler_bp'
]