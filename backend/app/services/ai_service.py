import os
import requests


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
        if not text:
            return "neutral"

        text_lower = text.lower()

        positive_keywords = [
            'glücklich', 'fröhlich', 'gut', 'super', 'toll',
            'freude', 'entspannt', 'zufrieden', 'motiviert'
        ]
        negative_keywords = [
            'gestresst', 'müde', 'traurig', 'schlecht',
            'ängstlich', 'sorge', 'problem', 'erschöpft', 'überfordert'
        ]

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
    def generate_morning_plan(
        user_name,
        city,
        weather=None,
        sleep_hours=None,
        last_entries=None,
        tomorrow_plan=None
    ):
        """
        Generate a morning plan.
        Key goals:
        - avoid monotony: produce concrete HH:MM timeline when possible
        - reuse tomorrow_plan if provided (usually from what_to_improve)
        - keep it realistic and not invent "already done" facts
        """
        system_prompt = (
            "Du bist ein empathischer Produktivitäts-Coach. "
            "Erstelle motivierende, personalisierte Tagespläne in natürlicher deutscher Sprache. "
            "WICHTIG: Wenn der Nutzer einen Plan (mit Uhrzeiten) angibt, nutze diese Uhrzeiten als Timeline. "
            "Erfinde keine Fakten. Sei konkret, realistisch und abwechslungsreich. "
            "Benutze Emojis sparsam."
        )

        context_parts = [f"Erstelle einen Tagesplan für {user_name} aus {city}."]

        if weather:
            context_parts.append(f"Wetter heute: {weather}")

        if sleep_hours is not None:
            context_parts.append(f"Schlaf: {sleep_hours} Stunden")
            if sleep_hours < 6:
                context_parts.append("Hinweis: Wenig Schlaf – plane extra Pausen und leichte Ziele ein.")
            elif sleep_hours >= 8:
                context_parts.append("Hinweis: Guter Schlaf – du startest ausgeruht.")

        if last_entries:
            context_parts.append(f"Letzte Einträge (Kurz):\n{last_entries}")

        if tomorrow_plan:
            context_parts.append(
                "Nutzer-Plan/Verbesserung (FUTURE, noch nicht passiert) – bitte übernehmen und strukturieren:\n"
                f"{tomorrow_plan}"
            )

        # Output constraints
        context_parts.append("\nAUSGABE-REGELN:")
        context_parts.append("- Beginne mit 'Guten Morgen' und dem Namen.")
        context_parts.append("- Wenn Uhrzeiten genannt werden (z.B. 07:00), erstelle eine Timeline im Format 'HH:MM – ...'.")
        context_parts.append("- Wenn keine Uhrzeiten vorhanden sind, gib 4–6 konkrete Punkte (kurz, nicht generisch).")
        context_parts.append("- Maximal 170 Wörter.")
        context_parts.append("- Ende mit 1 motivierendem Emoji.")
        context_parts.append("- Keine Markdown-Fettschrift wie **...**.")

        prompt = "\n".join(context_parts)

        return AIService.generate_text(prompt, system_prompt)

    @staticmethod
    def analyze_journal_entry(entry_text):
        """
        Summarize a journal entry WITHOUT turning future intentions into past achievements.
        """
        system_prompt = (
            "Du bist ein empathischer Coach. "
            "Schreibe eine kurze, motivierende Zusammenfassung (max. 50 Wörter). "
            "WICHTIG: Inhalte im Abschnitt FUTURE sind Pläne/Vorsätze und dürfen NICHT als bereits passiert formuliert werden. "
            "Formuliere FUTURE immer als Plan (z.B. 'Morgen könntest du ...'). "
            "Sei einfühlsam, konstruktiv und ermutigend. "
            "Beende mit einem passenden Emoji."
        )

        prompt = (
            "Analysiere diesen Tagebucheintrag.\n"
            "Achte streng auf die Abschnitte PAST/FUTURE/CURRENT.\n\n"
            f"{entry_text}\n\n"
            "Erstelle eine kurze Zusammenfassung (max. 50 Wörter):\n"
            "- Hebe 1–2 positive Punkte aus PAST hervor\n"
            "- FUTURE als Plan/Vorsatz formulieren\n"
            "- CURRENT kurz spiegeln\n"
            "- Ende mit einem Emoji"
        )

        return AIService.generate_text(prompt, system_prompt)

    @staticmethod
    def generate_evening_reflection_prompt(user_name, today_plan=None):
        system_prompt = (
            "Du bist ein empathischer Coach für Tagesreflexion. "
            "Sei warmherzig, kurz und ermutigend."
        )

        prompt_parts = [f"Erstelle eine kurze, einladende Nachricht für {user_name} zur Tagesreflexion am Abend."]

        if today_plan:
            prompt_parts.append(f"Heute Morgen gab es diesen Plan (nur Kontext, nicht wiederholen):\n{today_plan[:160]}")

        prompt_parts.append("\nREGELN:")
        prompt_parts.append("- Kurz (max. 40 Wörter)")
        prompt_parts.append("- Einladend, nicht belehrend")
        prompt_parts.append("- Ende mit einem passenden Emoji")
        prompt = "\n".join(prompt_parts)

        return AIService.generate_text(prompt, system_prompt)