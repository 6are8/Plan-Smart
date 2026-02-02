from app import create_app, db
from app.models import JournalEntry

app = create_app()

# Mapping: Old numeric mood → New string mood
MOOD_MAPPING = {5: "Happy", 4: "Calm", 3: "Focused", 2: "Tired", 1: "Sad"}

with app.app_context():
    entries = JournalEntry.query.all()

    print(f"🔄 Migrating {len(entries)} journal entries...")

    for entry in entries:
        old_mood = entry.mood

        # Wenn mood schon ein String ist, überspringe
        if isinstance(old_mood, str):
            print(f"  ✓ Entry {entry.id}: Already migrated ({old_mood})")
            continue

        # Konvertiere numerische Moods
        try:
            old_mood_int = int(old_mood) if old_mood else 3
            new_mood = MOOD_MAPPING.get(old_mood_int, "Calm")

            entry.mood = new_mood
            print(f"  ✓ Entry {entry.id}: {old_mood} → {new_mood}")

        except (ValueError, TypeError):
            entry.mood = "Calm"
            print(f"  ! Entry {entry.id}: Invalid mood, set to Calm")

    db.session.commit()
    print(f"\n✅ Migration complete!")
