import requests
import os


class AIService:
    @staticmethod
    def generate_text(prompt, system_prompt=None):
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
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data.get('response', ''), None
            
        except requests.exceptions.Timeout:
            return None, "AI request timed out"
        except requests.exceptions.RequestException as e:
            return None, f"AI service error: {str(e)}"

    @staticmethod
    def detect_emotion_simple(text):
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
    def generate_morning_plan(user_name, city, weather=None, sleep_hours=None, last_entries=None):
        system_prompt = """Du bist ein empathischer Produktivitäts-Coach. 
        Erstelle motivierende, personalisierte Tagespläne in natürlicher deutscher Sprache.
        Sei freundlich, konkret und realistisch. Benutze Emojis sparsam."""
        
        context_parts = [f"Erstelle einen Tagesplan für {user_name} aus {city}."]
        
        if weather:
            context_parts.append(f"\nWetter heute: {weather}")
        
        if sleep_hours is not None:
            context_parts.append(f"\nSchlaf: {sleep_hours} Stunden")
            if sleep_hours < 6:
                context_parts.append("⚠️ Wenig Schlaf - plane extra Pausen ein!")
            elif sleep_hours >= 8:
                context_parts.append("✅ Guter Schlaf - du startest ausgeruht!")
        
        if last_entries:
            context_parts.append(f"\nLetzte Einträge:\n{last_entries}")
        
        context_parts.append("\n\nDer Tagesplan soll:")
        context_parts.append("- Mit 'Guten Morgen' und dem Namen beginnen")
        context_parts.append("- Freundlich und motivierend sein")
        context_parts.append("- 3-5 konkrete Empfehlungen geben")
        context_parts.append("- Maximal 150 Wörter lang sein")
        context_parts.append("- Mit einem motivierenden Emoji enden")
        
        prompt = "\n".join(context_parts)
        
        return AIService.generate_text(prompt, system_prompt)
    
    @staticmethod
    def analyze_journal_entry(entry_text):
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