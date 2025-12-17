from datetime import date
from models import User, JournalEntry
from extensions import db


def test_get_or_create_today_creates_entry(app):
    """Test creating a new journal entry for today"""
    with app.app_context():
        user = User(username="testuser", city="Berlin")
        user.set_password("1234")
        db.session.add(user)
        db.session.commit()

        entry = JournalEntry.get_or_create_today(user.id)

        assert entry is not None
        assert entry.user_id == user.id
        assert entry.date == date.today()


def test_get_or_create_today_returns_existing(app):
    """Test returning an existing entry instead of creating a new one"""
    with app.app_context():
        user = User(username="testuser2", city="Hamburg")
        user.set_password("1234")
        db.session.add(user)
        db.session.commit()

        entry1 = JournalEntry.get_or_create_today(user.id)
        entry1_id = entry1.id

        entry2 = JournalEntry.get_or_create_today(user.id)

        assert entry1_id == entry2.id



def test_update_reflection(app):
    """Test updating evening reflection and mood"""
    with app.app_context():
        user = User(username="testuser3", city="Munich")
        user.set_password("1234")
        db.session.add(user)
        db.session.commit()

        entry = JournalEntry.get_or_create_today(user.id)
        entry_id = entry.id

        entry.update_reflection(5, "Great day")

        updated_entry = JournalEntry.query.get(entry_id)
        assert updated_entry.mood == 5
        assert updated_entry.evening_reflection == "Great day"


def test_set_morning_plan(app):
    """Test setting the morning plan"""
    with app.app_context():
        user = User(username="testuser4", city="Frankfurt")
        user.set_password("1234")
        db.session.add(user)
        db.session.commit()

        entry = JournalEntry.get_or_create_today(user.id)
        entry_id = entry.id

        entry.set_morning_plan("Reading a book + exercise")

        updated_entry = JournalEntry.query.get(entry_id)
        assert updated_entry.morning_plan == "Reading a book + exercise"


def test_get_journal_history(app):
    """Test retrieving journal history with a limit"""
    with app.app_context():
        user = User(username="testuser5", city="Cologne")
        user.set_password("1234")
        db.session.add(user)
        db.session.commit()

        # Create 5 entries
        for i in range(5):
            entry = JournalEntry(
                user_id=user.id,
                date=date.today(),
                mood=i + 1,
                morning_plan=f"Plan {i + 1}"
            )
            db.session.add(entry)
        db.session.commit()

        # Request only 3 entries
        any_entry = JournalEntry.query.filter_by(user_id=user.id).first()
        history = any_entry.get_journal_history(limit=3)

        assert len(history) == 3
        assert all(entry.user_id == user.id for entry in history)


def test_journal_entry_all_fields(app):
    """Test all JournalEntry fields"""
    with app.app_context():
        user = User(username="testuser6", city="Stuttgart")
        user.set_password("1234")
        db.session.add(user)
        db.session.commit()

        entry = JournalEntry(
            user_id=user.id,
            date=date.today(),
            mood=4,
            morning_plan="Morning plan",
            evening_reflection="Evening reflection",
            ai_summary="AI summary",
            emotion_detected="Happy"
        )
        db.session.add(entry)
        db.session.commit()

        assert entry.id is not None
        assert entry.user_id == user.id
        assert entry.date == date.today()
        assert entry.mood == 4
        assert entry.morning_plan == "Morning plan"
        assert entry.evening_reflection == "Evening reflection"
        assert entry.ai_summary == "AI summary"
        assert entry.emotion_detected == "Happy"
        assert entry.created_at is not None


def test_journal_relationship_with_user(app):
    """Test relationship between JournalEntry and User"""
    with app.app_context():
        user = User(username="testuser7", city="Leipzig")
        user.set_password("1234")
        db.session.add(user)
        db.session.commit()

        entry = JournalEntry.get_or_create_today(user.id)

        # Check relationship from Entry side
        assert entry.user.username == "testuser7"
        assert entry.user.city == "Leipzig"

        # Check relationship from User side
        assert len(user.journal_entries) == 1
        assert user.journal_entries[0].id == entry.id


def test_journal_cascade_delete(app):
    """Test cascade delete of journal entries when user is deleted"""
    with app.app_context():
        user = User(username="testuser8", city="Dresden")
        user.set_password("1234")
        db.session.add(user)
        db.session.commit()
        user_id = user.id

        # Create two entries
        entry1 = JournalEntry.get_or_create_today(user.id)
        entry2 = JournalEntry(user_id=user.id, date=date.today(), mood=3)
        db.session.add(entry2)
        db.session.commit()

        # Ensure entries exist
        entries_before = JournalEntry.query.filter_by(user_id=user_id).all()
        assert len(entries_before) == 2

        # Delete user
        db.session.delete(user)
        db.session.commit()

        # Ensure entries are deleted
        entries_after = JournalEntry.query.filter_by(user_id=user_id).all()
        assert len(entries_after) == 0


def test_multiple_users_separate_entries(app):
    """Test that each user has their own separate entries"""
    with app.app_context():
        user1 = User(username="user1", city="Berlin")
        user1.set_password("pass1")
        user2 = User(username="user2", city="Hamburg")
        user2.set_password("pass2")
        db.session.add_all([user1, user2])
        db.session.commit()

        entry1 = JournalEntry.get_or_create_today(user1.id)
        entry2 = JournalEntry.get_or_create_today(user2.id)

        entry1.set_morning_plan("User one plan")
        entry2.set_morning_plan("User two plan")

        assert entry1.id != entry2.id
        assert entry1.user_id == user1.id
        assert entry2.user_id == user2.id
        assert entry1.morning_plan != entry2.morning_plan


def test_mood_range_valid(app):
    """Test that mood accepts values from 1 to 5"""
    with app.app_context():
        user = User(username="testuser9", city="Bonn")
        user.set_password("1234")
        db.session.add(user)
        db.session.commit()

        entry = JournalEntry.get_or_create_today(user.id)

        for mood in [1, 2, 3, 4, 5]:
            entry.update_reflection(mood, f"Reflection {mood}")
            assert entry.mood == mood


def test_journal_entry_repr(app):
    """Test __repr__ method"""
    with app.app_context():
        user = User(username="testuser10", city="Essen")
        user.set_password("1234")
        db.session.add(user)
        db.session.commit()

        entry = JournalEntry.get_or_create_today(user.id)

        repr_str = repr(entry)
        assert "JournalEntry" in repr_str
        assert str(user.id) in repr_str
        assert str(date.today()) in repr_str


def test_empty_fields_allowed(app):
    """Test that empty fields are allowed"""
    with app.app_context():
        user = User(username="testuser11", city="Dortmund")
        user.set_password("1234")
        db.session.add(user)
        db.session.commit()

        entry = JournalEntry(
            user_id=user.id,
            date=date.today()
        )
        db.session.add(entry)
        db.session.commit()

        assert entry.mood is None
        assert entry.morning_plan is None
        assert entry.evening_reflection is None
        assert entry.ai_summary is None
        assert entry.emotion_detected is None