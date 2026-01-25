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
    def extract_weekly_features(journals):
        """
        Analysiert wöchentliche Tagebucheinträge und extrahiert Verhaltensmuster
        
        Args:
            journals: Liste von JournalEntry-Objekten
            
        Returns:
            dict: Analysierte Features oder None bei Fehler
        """
        if not journals or len(journals) == 0:
            return None
        
        # 1. Tagebucheinträge zu Text zusammenfassen
        journals_text = ""
        for j in journals:
            # Wochentag auf Deutsch
            weekday = j.date.strftime('%A')
            mood_emoji = "😊" if j.mood and j.mood >= 4 else "😐" if j.mood == 3 else "😔"
            
            # Alle relevanten Felder sammeln
            entry_parts = []
            if j.what_went_well:
                entry_parts.append(f"Gut: {j.what_went_well}")
            if j.what_to_improve:
                entry_parts.append(f"Verbesserung: {j.what_to_improve}")
            if j.how_i_feel:
                entry_parts.append(f"Gefühle: {j.how_i_feel}")
            
            content = " | ".join(entry_parts)
            journals_text += f"- [{weekday}, {j.date.strftime('%d.%m.')}] {mood_emoji} Stimmung ({j.mood}/5): {content}\n"
        
        # 2. System Prompt definieren
        system_prompt = """Du bist ein erfahrener KI-Psychologe und Datenanalyst. 
Deine Aufgabe ist es, Muster im Verhalten zu erkennen und strukturierte Daten zu liefern.
Du bist präzise, objektiv und arbeitest ausschließlich mit den gegebenen Informationen."""
        
        # 3. Hauptprompt für die Analyse
        prompt = f"""
Analysiere die folgenden Tagebucheinträge einer Woche:

{journals_text}

WICHTIG - STRENGE REGELN:
- Extrahiere nur wiederkehrende Muster, die KLAR erkennbar sind
- Wenn etwas plausibel abgeleitet werden kann (z.B. "viel Arbeit" → workload: hoch), darfst du es ergänzen
- KEINE Diagnosen, KEINE unplausiblen Informationen
- Antworte NUR in einem validen JSON-Objekt
- Wenn keine Information erkennbar ist → null
- Listen können leer sein: []

Antworte im folgenden JSON-Format (EXAKT so):
{{
  "stress_level": "hoch | mittel | niedrig | null",
  "sleep_quality": "gut | schlecht | null",
  "energy_pattern": "morgens | abends | schwankend | null",
  "planning_style": "strukturiert | flexibel | null",
  "emotional_stability": "stabil | labil | null",
  "focus_level": "hoch | niedrig | null",
  "workload": "hoch | mittel | niedrig | null",
  "dominant_interests": ["Sport", "Arbeit", "Lernen"] | null,
  "motivation_triggers": ["klare Ziele", "Pausen", "Erfolge"] | null,
  "plan_preference": "detailliert | flexibel | null",
  "risk_flags": ["Überforderung", "Erschöpfung"] | null
}}

Antworte NUR mit dem JSON-Objekt, OHNE zusätzlichen Text.
"""
        
        try:
            # 4. AI API aufrufen
            raw_response, error = AIService.generate_text(prompt, system_prompt)
            
            if error:
                print(f"AI Service Error: {error}")
                return None
            
            if not raw_response:
                print("AI Warning: Empty response")
                return None
            
            # 5. JSON extrahieren (falls AI zusätzlichen Text zurückgibt)
            # Suche nach dem ersten { bis zum letzten }
            match = re.search(r'\{.*\}', raw_response, re.DOTALL)
            
            if match:
                clean_json = match.group(0)
                features = json.loads(clean_json)
                
                # 6. Validierung der Struktur
                required_keys = [
                    'stress_level', 'sleep_quality', 'energy_pattern',
                    'planning_style', 'emotional_stability', 'focus_level',
                    'workload', 'dominant_interests', 'motivation_triggers',
                    'plan_preference', 'risk_flags'
                ]
                
                # Prüfen ob alle Keys vorhanden sind
                if not all(key in features for key in required_keys):
                    print("AI Warning: Missing keys in response")
                    # Fehlende Keys mit null ergänzen
                    for key in required_keys:
                        if key not in features:
                            features[key] = None
                
                return features
            else:
                print(f"AI Warning: No JSON found in response: {raw_response[:200]}")
                return None
                
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}")
            print(f"Raw response was: {raw_response[:500]}")
            return None
        except Exception as e:
            print(f"AI Service Error in extract_weekly_features: {e}")
            return None

    @staticmethod
    def generate_morning_plan(user_name, city, weather=None, sleep_hours=None, 
                            last_entries=None, weekly_profile=None):
        """
        Generiert einen personalisierten Morgenplan
        
        Args:
            weekly_profile: Optional - UserWeeklyProfile features dict
        """
        system_prompt = """Du bist ein empathischer Produktivitäts-Coach. 
Erstelle motivierende, personalisierte Tagespläne in natürlicher deutscher Sprache.
Sei freundlich, konkret und realistisch. Benutze Emojis sparsam."""
        
        context_parts = [f"Erstelle einen Tagesplan für {user_name} aus {city}."]
        
        # Wetter
        if weather:
            context_parts.append(f"\nWetter heute: {weather}")
        
        # Schlaf
        if sleep_hours is not None:
            context_parts.append(f"\nSchlaf: {sleep_hours} Stunden")
            if sleep_hours < 6:
                context_parts.append("⚠️ Wenig Schlaf - plane extra Pausen ein!")
            elif sleep_hours >= 8:
                context_parts.append("✅ Guter Schlaf - du startest ausgeruht!")
        
        # Letzte Einträge
        if last_entries:
            context_parts.append(f"\nLetzte Einträge:\n{last_entries}")
        
        # NEUE SEKTION: Weekly Profile Integration
        if weekly_profile:
            context_parts.append("\n--- PERSÖNLICHKEITSPROFIL (letzte Woche) ---")
            
            if weekly_profile.get('stress_level'):
                context_parts.append(f"Stresslevel: {weekly_profile['stress_level']}")
            
            if weekly_profile.get('energy_pattern'):
                context_parts.append(f"Energiemuster: {weekly_profile['energy_pattern']}")
            
            if weekly_profile.get('planning_style'):
                context_parts.append(f"Planungsstil: {weekly_profile['planning_style']}")
            
            if weekly_profile.get('dominant_interests'):
                interests = ', '.join(weekly_profile['dominant_interests'])
                context_parts.append(f"Interessen: {interests}")
            
            if weekly_profile.get('motivation_triggers'):
                triggers = ', '.join(weekly_profile['motivation_triggers'])
                context_parts.append(f"Motiviert durch: {triggers}")
            
            if weekly_profile.get('risk_flags'):
                flags = ', '.join(weekly_profile['risk_flags'])
                context_parts.append(f"⚠️ Achtung: {flags}")
        
        # Anweisungen für den Plan
        context_parts.append("\n\nDer Tagesplan soll:")
        context_parts.append("- Mit 'Guten Morgen' und dem Namen beginnen")
        context_parts.append("- Freundlich und motivierend sein")
        context_parts.append("- 3-5 konkrete Empfehlungen geben")
        
        # Wenn Weekly Profile vorhanden, anpassen
        if weekly_profile:
            if weekly_profile.get('plan_preference') == 'detailliert':
                context_parts.append("- Detaillierte Zeitangaben und Schritte enthalten")
            elif weekly_profile.get('plan_preference') == 'flexibel':
                context_parts.append("- Flexibel und anpassungsfähig gestaltet sein")
        
        context_parts.append("- Maximal 150 Wörter lang sein")
        context_parts.append("- Mit einem motivierenden Emoji enden")
        
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