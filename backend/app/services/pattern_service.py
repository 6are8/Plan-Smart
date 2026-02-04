import json
import re
from datetime import date, timedelta
from app.services.ai_service import AIService


class SmartPatternService:
    """
    Intelligenter Service, der AI nutzt um Benutzermuster zu erkennen
    und Vorschläge für morgige Aufgaben zu generieren.
    """

    # Einfacher Cache für Vorschläge (wird täglich aktualisiert)
    _cache = {}

    @staticmethod
    def get_suggestions_for_tomorrow(user_id, models):
        """
        Generiert intelligente Vorschläge für den nächsten Tag
        basierend auf historischen Mustern des Benutzers.

        Args:
            user_id: Die ID des Benutzers
            models: Die Datenbank-Modelle (JournalEntry, etc.)

        Returns:
            Liste von Vorschlägen im Format:
            [{"text": "Gym 18:00", "type": "ai_prediction", "day": "Monday"}, ...]
        """

        # Cache-Prüfung (vermeidet unnötige AI-Aufrufe)
        cache_key = f"{user_id}_{date.today()}"
        if cache_key in SmartPatternService._cache:
            print("📦 Verwende gecachte AI-Vorschläge")
            return SmartPatternService._cache[cache_key]

        # 1. Bestimme den morgigen Tag
        tomorrow = date.today() + timedelta(days=1)
        tomorrow_day_name = tomorrow.strftime("%A")  # z.B. "Monday"

        # 2. Hole Daten der letzten 3 Wochen
        # (3 Wochen geben genug Kontext für wöchentliche Muster)
        three_weeks_ago = date.today() - timedelta(days=21)

        entries = (
            models.JournalEntry.query.filter(
                models.JournalEntry.user_id == user_id,
                models.JournalEntry.date >= three_weeks_ago,
            )
            .order_by(models.JournalEntry.date.asc())
            .all()
        )

        # Mindestens 3 Einträge nötig für sinnvolle Muster
        if len(entries) < 3:
            print("⚠️ Nicht genug Daten für AI-Musteranalyse")
            return []

        # 3. Bereite den Text für die AI vor
        # Format: "- Monday (15.01): Gym 18:00, Meeting 10:00"
        history_text = ""
        for entry in entries:
            day_name = entry.date.strftime("%A")
            content = entry.what_to_improve if entry.what_to_improve else ""

            if content and content.strip():
                history_text += (
                    f"- {day_name} ({entry.date.strftime('%d.%m')}): {content}\n"
                )

        # Wenn keine verwertbaren Daten vorhanden sind
        if not history_text.strip():
            print("⚠️ Keine Aufgaben-Historie gefunden")
            return []

        # 4. Erstelle den intelligenten Prompt
        system_prompt = (
            "Du bist ein persönlicher Assistent, der Gewohnheitsmuster analysiert. "
            "Du antwortest NUR mit validen JSON-Arrays, ohne zusätzlichen Text."
        )

        prompt = f"""
Analysiere die folgenden Tagebucheinträge der letzten 3 Wochen:

{history_text}

AUFGABE:
Morgen ist **{tomorrow_day_name}** ({tomorrow.strftime("%d.%m.%Y")}).

Identifiziere wiederkehrende Muster für {tomorrow_day_name}:
- Ignoriere einmalige Ereignisse (z.B. "Arzttermin am 15.01.")
- Fokussiere auf echte Gewohnheiten (z.B. "jeden Montag Gym")
- Maximal 5 Vorschläge, jeweils max. 40 Zeichen

FORMAT (NUR JSON, KEIN ZUSÄTZLICHER TEXT):
["Task 1", "Task 2", "Task 3"]

BEISPIELE:
✅ ["Gym 18:00", "Team Meeting", "Wocheneinkauf"]
✅ ["Deutschkurs", "Joggen"]
❌ ["Am Montag hatte ich..."] (zu spezifisch!)

Falls KEINE klaren Muster erkennbar: []
"""

        # 5. Rufe die AI auf
        try:
            print(f"🤖 Rufe AI für {tomorrow_day_name}-Vorschläge auf...")
            response, error = AIService.generate_text(prompt, system_prompt)

            # Fehlerbehandlung: AI-Service-Fehler
            if error:
                print(f"❌ AI-Fehler: {error}")
                return []

            # Fehlerbehandlung: Leere Antwort
            if not response or not response.strip():
                print("⚠️ AI hat leere Antwort zurückgegeben")
                return []

            # 6. Bereinige und analysiere die AI-Antwort
            print(f"📥 AI-Antwort (erste 200 Zeichen): {response[:200]}")

            # Extrahiere JSON-Array mit Regex
            # Beispiel: "Hier sind die Vorschläge: ["Gym", "Meeting"]" → ["Gym", "Meeting"]
            match = re.search(r"\[.*?\]", response, re.DOTALL)
            if not match:
                print("⚠️ Kein JSON-Array in AI-Antwort gefunden")
                return []

            # Parse JSON
            suggestions_raw = json.loads(match.group(0))

            # 7. Validiere und bereinige die Vorschläge
            if not isinstance(suggestions_raw, list):
                print("⚠️ AI-Antwort ist keine Liste")
                return []

            suggestions = []
            for task in suggestions_raw[:5]:  # Maximal 5 Vorschläge
                if isinstance(task, str) and len(task.strip()) > 0:
                    # Bereinige und kürze den Text (max 50 Zeichen)
                    clean_task = task.strip()[:50]
                    suggestions.append(
                        {
                            "text": clean_task,
                            "type": "ai_prediction",
                            "day": tomorrow_day_name,
                        }
                    )

            print(f"✅ {len(suggestions)} AI-Vorschläge generiert")

            # 8. Speichere im Cache (gültig bis Mitternacht)
            SmartPatternService._cache[cache_key] = suggestions

            return suggestions

        except json.JSONDecodeError as e:
            # Fehlerbehandlung: JSON konnte nicht geparst werden
            print(f"❌ JSON-Parsing-Fehler: {e}")
            print(f"Rohe AI-Antwort: {response}")
            return []

        except Exception as e:
            # Fehlerbehandlung: Unerwarteter Fehler
            print(f"❌ Unerwarteter Fehler: {e}")
            return []
