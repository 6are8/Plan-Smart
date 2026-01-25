from datetime import datetime, timedelta, date
from app.models import JournalEntry, UserWeeklyProfile
from app.services.ai_service import AIService
from app.extensions import db
import logging

logger = logging.getLogger(__name__)


class WeeklyAnalysisService:
    """
    Service für wöchentliche Analyse von Benutzerverhalten
    """
    
    @staticmethod
    def get_week_boundaries(target_date=None):
        """
        Berechnet Start und Ende der Woche (Montag bis Sonntag)
        
        Args:
            target_date: Optional - Datum für die Wochenberechnung
            
        Returns:
            tuple: (week_start, week_end)
        """
        if target_date is None:
            target_date = date.today()
        
        # Montag der Woche finden (weekday: 0=Montag, 6=Sonntag)
        days_since_monday = target_date.weekday()
        week_start = target_date - timedelta(days=days_since_monday)
        week_end = week_start + timedelta(days=6)
        
        return week_start, week_end
    
    @staticmethod
    def analyze_user_week(user_id, week_start=None, force_reanalysis=False):
        """
        Analysiert die Woche eines Benutzers und erstellt/aktualisiert das Profil
        
        Args:
            user_id: ID des Benutzers
            week_start: Optional - Start der zu analysierenden Woche
            force_reanalysis: Wenn True, wird neu analysiert auch wenn Profil existiert
            
        Returns:
            UserWeeklyProfile oder None bei Fehler
        """
        try:
            # Wochengrenzen berechnen
            if week_start is None:
                week_start, week_end = WeeklyAnalysisService.get_week_boundaries()
            else:
                week_end = week_start + timedelta(days=6)
            
            logger.info(f"Analysiere Woche für User {user_id}: {week_start} bis {week_end}")
            
            # Prüfen ob Profil bereits existiert
            existing_profile = UserWeeklyProfile.get_profile_for_week(user_id, week_start)
            
            if existing_profile and not force_reanalysis:
                logger.info(f"Profil existiert bereits für Woche {week_start}")
                return existing_profile
            
            # Tagebucheinträge der Woche holen
            journals = JournalEntry.query.filter(
                JournalEntry.user_id == user_id,
                JournalEntry.date >= week_start,
                JournalEntry.date <= week_end
            ).order_by(JournalEntry.date.asc()).all()
            
            if not journals or len(journals) < 3:
                logger.warning(f"Zu wenige Einträge ({len(journals) if journals else 0}) für Analyse")
                return None
            
            logger.info(f"Gefunden: {len(journals)} Tagebucheinträge")
            
            # AI Analyse durchführen
            features = AIService.extract_weekly_features(journals)
            
            if not features:
                logger.error("AI konnte keine Features extrahieren")
                return None
            
            # Confidence Score berechnen (basierend auf Anzahl der Einträge)
            confidence = min(1.0, len(journals) / 7.0)
            
            # Profil erstellen oder aktualisieren
            if existing_profile:
                # Aktualisieren
                existing_profile.set_features(features)
                existing_profile.analyzed_entries_count = len(journals)
                existing_profile.confidence_score = confidence
                profile = existing_profile
                logger.info(f"Profil aktualisiert für Woche {week_start}")
            else:
                # Neu erstellen
                profile = UserWeeklyProfile(
                    user_id=user_id,
                    week_start_date=week_start,
                    week_end_date=week_end,
                    analyzed_entries_count=len(journals),
                    confidence_score=confidence
                )
                profile.set_features(features)
                db.session.add(profile)
                logger.info(f"Neues Profil erstellt für Woche {week_start}")
            
            db.session.commit()
            
            logger.info(f"✅ Wöchentliche Analyse erfolgreich für User {user_id}")
            return profile
            
        except Exception as e:
            logger.error(f"Fehler bei wöchentlicher Analyse: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def analyze_all_users_weekly():
        """
        Führt wöchentliche Analyse für alle Benutzer durch
        Wird vom Scheduler aufgerufen
        
        Returns:
            dict: Statistiken über die Analyse
        """
        from app.models import User
        
        logger.info("🔄 Starte wöchentliche Analyse für alle Benutzer")
        
        users = User.query.all()
        
        stats = {
            'total_users': len(users),
            'analyzed': 0,
            'skipped': 0,
            'errors': 0
        }
        
        week_start, week_end = WeeklyAnalysisService.get_week_boundaries()
        
        for user in users:
            try:
                # Prüfen ob genug Einträge vorhanden
                entries_count = JournalEntry.query.filter(
                    JournalEntry.user_id == user.id,
                    JournalEntry.date >= week_start,
                    JournalEntry.date <= week_end
                ).count()
                
                if entries_count < 3:
                    logger.info(f"User {user.username}: Nur {entries_count} Einträge - übersprungen")
                    stats['skipped'] += 1
                    continue
                
                # Analyse durchführen
                profile = WeeklyAnalysisService.analyze_user_week(user.id, week_start)
                
                if profile:
                    stats['analyzed'] += 1
                    logger.info(f"✅ User {user.username}: Analyse erfolgreich")
                else:
                    stats['errors'] += 1
                    logger.warning(f"⚠️ User {user.username}: Analyse fehlgeschlagen")
                    
            except Exception as e:
                logger.error(f"Fehler bei User {user.username}: {e}")
                stats['errors'] += 1
                continue
        
        logger.info(f"✅ Wöchentliche Analyse abgeschlossen: {stats}")
        return stats
    
    @staticmethod
    def get_user_latest_profile(user_id):
        """
        Holt das neueste Profil eines Benutzers
        
        Returns:
            dict: Features oder None
        """
        profile = UserWeeklyProfile.get_latest_profile(user_id)
        
        if profile:
            return profile.get_features()
        
        return None
    
    @staticmethod
    def format_profile_summary(features):
        """
        Formatiert Features zu einer lesbaren Zusammenfassung
        
        Args:
            features: Dictionary mit Features
            
        Returns:
            str: Lesbare Zusammenfassung
        """
        if not features:
            return "Kein Profil verfügbar"
        
        parts = []
        
        if features.get('stress_level'):
            parts.append(f"Stress: {features['stress_level']}")
        
        if features.get('energy_pattern'):
            parts.append(f"Energie: {features['energy_pattern']}")
        
        if features.get('dominant_interests'):
            interests = ', '.join(features['dominant_interests'])
            parts.append(f"Interessen: {interests}")
        
        return " | ".join(parts) if parts else "Keine spezifischen Muster erkannt"