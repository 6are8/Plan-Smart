import requests
import os
import json
import re


class AIService:
    @staticmethod
    def generate_text(prompt, system_prompt=None):
        """
        Generiert Text über Ollama API
        """
        try:
            ollama_url = os.getenv('OLLAMA_API_URL', 'http://localhost:11434')
            ollama_model = os.getenv('OLLAMA_MODEL', 'gemma3:4b')

            url = f"{ollama_url}/api/generate"
            payload = {
                "model": ollama_model,
                "prompt": prompt,
                "stream": False
            }

            if system_prompt:
                payload["system"] = system_prompt

            response = requests.post(url, json=payload, timeout=200)
            response.raise_for_status()

            data = response.json()
            return data.get('response', ''), None

        except requests.exceptions.Timeout:
            return None, "AI request timed out"
        except requests.exceptions.RequestException as e:
            return None, f"AI service error: {str(e)}"

    @staticmethod
    def detect_emotion_simple(text):
        """
        Einfache Emotionserkennung basierend auf Keywords
        """
        if not text:
            return "neutral"

        text_lower = text.lower()

        positive_keywords = ['glücklich', 'fröhlich', 'gut', 'super', 'toll', 
                           'freude', 'entspannt', 'zufrieden', 'motiviert']
        negative_keywords = ['gestresst', 'müde', 'traurig', 'schlecht', 
                           'ängstlich', 'sorge', 'problem', 'erschöpft', 'überfordert']

        positive_count = sum(1 for keyword in positive_keywords if keyword in text_lower)
        negative_count = sum(1 for keyword in negative_keywords if keyword in text_lower)

        if negative_count > positive_count:
            if 'gestresst' in text_lower or 'überfordert' in text_lower:
                return "gestresst"
            elif 'müde' in text_lower or 'erschöpft' in text_lower:
                return "erschöpft"
            elif 'traurig' in text_lower:
                return "traurig"
            else:
                return "negativ"
        elif positive_count > negative_count:
            if 'glücklich' in text_lower or 'freude' in text_lower:
                return "glücklich"
            elif 'motiviert' in text_lower:
                return "motiviert"
            else:
                return "positiv"
        else:
            return "neutral"

    @staticmethod

    def extract_weekly_features(journals, previous_profile=None):
        """
        Persona-Based Analysis - Simple & Flexible Version
        """
        if not journals or len(journals) == 0:
            return None

        # 1. Tagebucheinträge formatieren
        journals_text = ""
        for j in journals:
            weekday = j.date.strftime('%A')
            mood = "😊" if j.mood >= 4 else "😐" if j.mood == 3 else "😔"

            journals_text += f"[{weekday}] {mood} Stimmung {j.mood}/5:\n"
            if j.what_went_well:
                journals_text += f"  ✅ {j.what_went_well}\n"
            if j.what_to_improve:
                journals_text += f"  ⚠️ {j.what_to_improve}\n"
            if j.how_i_feel:
                journals_text += f"  💭 {j.how_i_feel}\n"
            journals_text += "\n"

        # 2. Vorherige Traits und Notizen
        previous_traits = []
        previous_notes = []

        if previous_profile and previous_profile.get('persona'):
            previous_traits = previous_profile['persona'].get('traits', [])
            previous_notes = previous_profile['persona'].get('coaching_notes', [])

        # 3. System Prompt
        system_prompt = """Du bist ein aufmerksamer Personal Coach.
    Beobachte Verhaltensmuster und erstelle ein prägnantes Persönlichkeitsprofil."""

        # 4. Der einfache Prompt
        prompt = f"""
    Analysiere diese Tagebucheinträge:

    {journals_text}

    {'─'*60}
    LETZTE WOCHE hattest du erkannt:
    Traits: {previous_traits if previous_traits else "Noch keine"}
    Notizen: {previous_notes if previous_notes else "Keine"}
    {'─'*60}

    DEINE AUFGABE:
    Erstelle/aktualisiere das Persona-Profil dieser Person.

    1️⃣ TRAITS (3-5 prägnante Eigenschaften):
    Beschreibe die Person mit kurzen Tags (CamelCase, Englisch).
    
    Beispiele guter Traits:
    - "NightOwl" (produktiv abends)
    - "MorningPerson" (früh wach, morgens aktiv)
    - "GymMotivationNeeded" (will Sport, schiebt oft auf)
    - "StructureLover" (braucht klaren Plan)
    - "DeepFocusPreferred" (mag lange Konzentrationsphasen)
    
    Regeln:
    • Maximal 5 Traits
    • Kurz & prägnant (1-3 Wörter pro Trait)
    • Basiere sie auf ECHTEN Beobachtungen
    • Behalte alte Traits wenn noch zutreffend
    • Lösche Traits wenn widerlegt
    • Füge neue hinzu wenn entdeckt

    2️⃣ COACHING NOTES (Genau 3 Anweisungen):
    Wie soll der Tages-Planer diese Person behandeln?
    
    Format: "[Was tun] - [Warum]"
    Max. 60 Zeichen pro Note!
    
    Beispiele:
    ✅ "Sport abends vorschlagen - nutzt NightOwl-Energie"
    ✅ "Kleine Erfolge loben - braucht Bestätigung"
    ✅ "Morgen-Meetings meiden - braucht Anlaufzeit"

    3️⃣ TREND (1 kurzer Satz, max 50 Zeichen):
    Wie entwickelt sich die Person?
    
    Beispiele:
    ✅ "Besser: Sport 3x gemacht!"
    ✅ "Stagniert: Viele Pläne, wenig Umsetzung"

    4️⃣ TOP-PRIORITÄT MORGEN (1 Satz, max 80 Zeichen):
    Was ist DIE wichtigste Sache für morgen?
    
    Beispiele:
    ✅ "10min Yoga um 7:00 - Sport-Gewohnheit starten"
    ✅ "Wichtigste Aufgabe bis 10:00 erledigen"

    {'─'*60}
    ANTWORTE NUR MIT DIESEM JSON (kein Text davor/danach):
    {'─'*60}
    {{
    "persona": {{
        "traits": ["Trait1", "Trait2", "Trait3"],
        "coaching_notes": [
        "Note 1 hier",
        "Note 2 hier", 
        "Note 3 hier"
        ]
    }},
    "trend": "Kurzer Trend-Satz",
    "priority": "Priorität für morgen"
    }}

    WICHTIG:
    ✓ Traits: 3-5 Stück, kurz, CamelCase
    ✓ Notes: Exakt 3, je max 60 Zeichen
    ✓ Trend: Max 50 Zeichen
    ✓ Priority: Max 80 Zeichen
    """

        try:
            # 5. AI aufrufen
            raw_response, error = AIService.generate_text(prompt, system_prompt)

            if error:
                print(f"AI Error: {error}")
                return None

            # 6. JSON extrahieren
            import re
            match = re.search(r'\{.*\}', raw_response, re.DOTALL)

            if not match:
                print("No JSON found")
                return None

            features = json.loads(match.group(0))

            # 7. Einfache Validierung (nur Limits, keine Listen)
            if 'persona' not in features:
                return None

            persona = features['persona']

            # Limit traits to 5
            if 'traits' in persona and len(persona['traits']) > 5:
                persona['traits'] = persona['traits'][:5]

            # Ensure exactly 3 coaching notes
            if 'coaching_notes' in persona:
                notes = persona['coaching_notes']
                if len(notes) > 3:
                    notes = notes[:3]
                elif len(notes) < 3:
                    while len(notes) < 3:
                        notes.append("Unterstütze bei der Zielerreichung")
                # Trim each note
                persona['coaching_notes'] = [n[:60] for n in notes]

            # Trim trend and priority
            if 'trend' in features:
                features['trend'] = features['trend'][:50]

            if 'priority' in features:
                features['priority'] = features['priority'][:80]

            return features

        except Exception as e:
            print(f"Error: {e}")
            return None

    @staticmethod
    def generate_morning_plan(user_name, city, weather=None, sleep_hours=None, last_entries=None, weekly_profile=None):
        
        # 1. System Prompt: 
        system_prompt = """Du bist ein empathischer Produktivitäts-Coach. 
        Deine Aufgabe ist es, einen Tagesplan zu erstellen.
        
        REGELN:
        1. Antworte AUSSCHLIESSLICH auf Deutsch (auch wenn der Input englisch ist).
        2. Sei motivierend, aber komm schnell auf den Punkt.
        3. Nutze das 'Weekly Profile', um den Plan zu personalisieren."""

        context_parts = [f"Erstelle einen Tagesplan für {user_name} aus {city}."]

        if weather:
            context_parts.append(f"\nWetter heute: {weather}")

        if sleep_hours is not None:
            status = "⚠️ Wenig Schlaf" if sleep_hours < 6 else "✅ Guter Schlaf"
            context_parts.append(f"\nSchlaf: {sleep_hours} Stunden ({status})")

        if last_entries:
            context_parts.append(f"\nLetzte Einträge:\n{last_entries}")

        if weekly_profile:
            profile_str = json.dumps(weekly_profile, ensure_ascii=False, indent=2)
            context_parts.append(f"\n--- USER CONTEXT (WEEKLY PROFILE) ---\n{profile_str}")
            context_parts.append("\n(Ignoriere englische Begriffe im Profil und nutze die deutschen Entsprechungen)")



        context_parts.append("\n\nFORMATIERUNG (Strikt):")
        context_parts.append("1. Starte: 'Guten Morgen [Name]! ☀️' + 1 kurzer Satz.")
        context_parts.append("2. KEINE Floskeln wie 'Hier ist dein Plan'.")
        context_parts.append("3. Zeitplan (4-5 Blöcke) chronologisch logisch (Morgen -> Abend):")
        context_parts.append("   - Format: **HH:MM Uhr:** [Titel]") 
        context_parts.append("   - Darunter: NUR 1 kurzer Befehl (Max. 6 Wörter).") 
        
        context_parts.append("4. BEISPIEL FÜR GUTES FORMAT:")
        context_parts.append("   **08:00 Uhr:** Frühstück & Start")
        context_parts.append("   Iss etwas Gesundes und trink Kaffee.")
        
        context_parts.append("5. Ende: Ein kurzer 'Viel Erfolg' Satz + Emoji.")

        prompt = "\n".join(context_parts)

        return AIService.generate_text(prompt, system_prompt)
    
    @staticmethod
    def analyze_journal_entry(entry_text):
        """
        Analysiert einen einzelnen Tagebucheintrag
        """
        system_prompt = """Du bist ein empathischer Coach. 
Analysiere Tagebucheinträge und erstelle kurze, ermutigende Zusammenfassungen.
Sei einfühlsam, konstruktiv und motivierend."""

        prompt = f"""Analysiere diesen Tagebucheintrag und erstelle eine kurze, 
motivierende Zusammenfassung (max. 50 Wörter):

{entry_text}

Die Zusammenfassung soll:
- Die Hauptpunkte hervorheben
- Positives verstärken
- Bei negativen Punkten konstruktive Perspektiven bieten
- Mit einem passenden Emoji enden"""

        return AIService.generate_text(prompt, system_prompt)

    @staticmethod
    def generate_evening_reflection_prompt(user_name, today_plan=None):
        """
        Generiert eine Aufforderung zur abendlichen Reflexion
        """
        system_prompt = """Du bist ein empathischer Coach für Tagesreflexion. 
Sei warmherzig und ermutigend."""

        prompt_parts = [f"Erstelle eine kurze, einladende Nachricht für {user_name} zur Tagesreflexion am Abend."]

        if today_plan:
            prompt_parts.append(f"\nHeute morgen hatte {user_name} diesen Plan:\n{today_plan[:100]}...")

        prompt_parts.append("\nDie Nachricht soll:")
        prompt_parts.append("- Freundlich zur Reflexion einladen")
        prompt_parts.append("- Kurz sein (max. 40 Wörter)")
        prompt_parts.append("- Mit einem passenden Emoji enden")

        prompt = "\n".join(prompt_parts)

        return AIService.generate_text(prompt, system_prompt)