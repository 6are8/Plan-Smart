from app.routes.auth import auth_bp
from app.routes.journal import journal_bp
from app.routes.morning import morning_bp
from app.routes.evening import evening_bp
from app.routes.scheduler import scheduler_bp
from app.routes.today import today_bp
from app.routes.history import history_bp
from app.routes.settings import settings_bp
from app.routes.prototype import prototype_bp
from app.routes.weekly import weekly_bp 


__all__ = [
    "auth_bp",
    "journal_bp",
    "morning_bp",
    "evening_bp",
    "scheduler_bp",
    "today_bp",
    "history_bp",
    "settings_bp",
    "prototype_bp",
    "weekly_bp",
]
