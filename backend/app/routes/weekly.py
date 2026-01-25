from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, UserWeeklyProfile
from app.services.weekly_analysis_service import WeeklyAnalysisService
from app.extensions import db
from datetime import datetime, date

weekly_bp = Blueprint('weekly', __name__)


@weekly_bp.route('/analyze', methods=['POST'])
@jwt_required()
def trigger_weekly_analysis():
    """
    Triggert manuelle wöchentliche Analyse für den aktuellen Benutzer
    """
    try:
        username = get_jwt_identity()
        user = User.find_by_username(username=username)
        
        if not user:
            return jsonify({'error': 'Benutzer nicht gefunden'}), 404
        
        # Optional: Spezifische Woche analysieren
        week_start_str = request.args.get('week_start')
        week_start = None
        
        if week_start_str:
            try:
                week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Ungültiges Datumsformat (YYYY-MM-DD)'}), 400
        
        # Force re-analysis?
        force = request.args.get('force', 'false').lower() == 'true'
        
        # Analyse durchführen
        profile = WeeklyAnalysisService.analyze_user_week(
            user_id=user.id,
            week_start=week_start,
            force_reanalysis=force
        )
        
        if not profile:
            return jsonify({
                'error': 'Analyse fehlgeschlagen',
                'hint': 'Möglicherweise zu wenige Tagebucheinträge (<3)'
            }), 400
        
        return jsonify({
            'message': 'Wöchentliche Analyse erfolgreich',
            'profile': profile.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@weekly_bp.route('/profile/latest', methods=['GET'])
@jwt_required()
def get_latest_profile():
    """
    Holt das neueste wöchentliche Profil des Benutzers
    """
    try:
        username = get_jwt_identity()
        user = User.find_by_username(username=username)
        
        if not user:
            return jsonify({'error': 'Benutzer nicht gefunden'}), 404
        
        profile = UserWeeklyProfile.get_latest_profile(user.id)
        
        if not profile:
            return jsonify({
                'message': 'Noch kein Profil vorhanden',
                'profile': None
            }), 200
        
        # Zusätzlich: Lesbare Zusammenfassung
        summary = WeeklyAnalysisService.format_profile_summary(
            profile.get_features()
        )
        
        return jsonify({
            'profile': profile.to_dict(),
            'summary': summary
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@weekly_bp.route('/profile/history', methods=['GET'])
@jwt_required()
def get_profile_history():
    """
    Holt alle wöchentlichen Profile des Benutzers
    """
    try:
        username = get_jwt_identity()
        user = User.find_by_username(username=username)
        
        if not user:
            return jsonify({'error': 'Benutzer nicht gefunden'}), 404
        
        # Query Parameter
        limit = request.args.get('limit', type=int, default=10)
        
        if limit < 1 or limit > 50:
            limit = 10
        
        profiles = UserWeeklyProfile.query.filter_by(user_id=user.id)\
            .order_by(UserWeeklyProfile.week_end_date.desc())\
            .limit(limit)\
            .all()
        
        return jsonify({
            'profiles': [p.to_dict() for p in profiles],
            'count': len(profiles)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@weekly_bp.route('/profile/<profile_id>', methods=['GET'])
@jwt_required()
def get_profile_by_id(profile_id):
    """
    Holt ein spezifisches wöchentliches Profil
    """
    try:
        username = get_jwt_identity()
        user = User.find_by_username(username=username)
        
        if not user:
            return jsonify({'error': 'Benutzer nicht gefunden'}), 404
        
        profile = UserWeeklyProfile.query.filter_by(
            id=profile_id,
            user_id=user.id
        ).first()
        
        if not profile:
            return jsonify({'error': 'Profil nicht gefunden'}), 404
        
        summary = WeeklyAnalysisService.format_profile_summary(
            profile.get_features()
        )
        
        return jsonify({
            'profile': profile.to_dict(),
            'summary': summary
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@weekly_bp.route('/profile/<profile_id>', methods=['DELETE'])
@jwt_required()
def delete_profile(profile_id):
    """
    Löscht ein wöchentliches Profil
    """
    try:
        username = get_jwt_identity()
        user = User.find_by_username(username=username)
        
        if not user:
            return jsonify({'error': 'Benutzer nicht gefunden'}), 404
        
        profile = UserWeeklyProfile.query.filter_by(
            id=profile_id,
            user_id=user.id
        ).first()
        
        if not profile:
            return jsonify({'error': 'Profil nicht gefunden'}), 404
        
        db.session.delete(profile)
        db.session.commit()
        
        return jsonify({
            'message': 'Profil erfolgreich gelöscht',
            'deleted_id': profile_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@weekly_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_weekly_stats():
    """
    Statistiken über wöchentliche Profile
    """
    try:
        username = get_jwt_identity()
        user = User.find_by_username(username=username)
        
        if not user:
            return jsonify({'error': 'Benutzer nicht gefunden'}), 404
        
        profiles = UserWeeklyProfile.query.filter_by(user_id=user.id).all()
        
        if not profiles:
            return jsonify({
                'total_profiles': 0,
                'average_confidence': None,
                'weeks_analyzed': 0
            }), 200
        
        # Durchschnittliche Confidence
        confidences = [p.confidence_score for p in profiles if p.confidence_score]
        avg_confidence = sum(confidences) / len(confidences) if confidences else None
        
        # Häufigste Muster sammeln
        all_interests = []
        stress_levels = []
        
        for p in profiles:
            features = p.get_features()
            if features:
                if features.get('dominant_interests'):
                    all_interests.extend(features['dominant_interests'])
                if features.get('stress_level'):
                    stress_levels.append(features['stress_level'])
        
        # Häufigste Interessen
        from collections import Counter
        interest_counts = Counter(all_interests)
        top_interests = interest_counts.most_common(5)
        
        # Häufigster Stresslevel
        stress_counts = Counter(stress_levels)
        
        return jsonify({
            'total_profiles': len(profiles),
            'average_confidence': round(avg_confidence, 2) if avg_confidence else None,
            'weeks_analyzed': len(profiles),
            'top_interests': [{'interest': i, 'count': c} for i, c in top_interests],
            'stress_distribution': dict(stress_counts),
            'latest_profile_date': profiles[0].week_end_date.isoformat() if profiles else None
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500