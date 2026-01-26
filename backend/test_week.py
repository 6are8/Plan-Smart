# test_week.py
from datetime import date, timedelta

today = date.today()
print(f"Today: {today} ({today.strftime('%A')})")

days_since_monday = today.weekday()
week_start = today - timedelta(days=days_since_monday)
week_end = week_start + timedelta(days=6)

print(f"Days since Monday: {days_since_monday}")
print(f"Week Start: {week_start} ({week_start.strftime('%A')})")
print(f"Week End: {week_end} ({week_end.strftime('%A')})")

# Test: هل المذكرات موجودة؟
from app import create_app
from app.models import User, JournalEntry

app = create_app("development")

with app.app_context():
    user = User.query.first()

    print(f"\n📋 All journals for user {user.username}:")
    all_journals = JournalEntry.query.filter_by(user_id=user.id).all()
    for j in all_journals:
        print(f"  - {j.date} ({j.date.strftime('%A')}): Mood {j.mood}")

    print(f"\n🔍 Journals in current week ({week_start} to {week_end}):")
    week_journals = JournalEntry.query.filter(
        JournalEntry.user_id == user.id,
        JournalEntry.date >= week_start,
        JournalEntry.date <= week_end,
    ).all()

    print(f"Found: {len(week_journals)} journals")
    for j in week_journals:
        print(f"  - {j.date}: Mood {j.mood}")
