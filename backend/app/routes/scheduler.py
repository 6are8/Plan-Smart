from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.services.scheduler_service import scheduler_service
import logging

logger = logging.getLogger(__name__)

scheduler_bp = Blueprint('scheduler', __name__)


@scheduler_bp.route('/status', methods=['GET'])
def get_scheduler_status():
    try:
        jobs = scheduler_service.scheduler.get_jobs()
        
        jobs_info = []
        for job in jobs:
            jobs_info.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        
        return jsonify({
            'running': scheduler_service.scheduler.running,
            'jobs_count': len(jobs),
            'jobs': jobs_info
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@scheduler_bp.route('/trigger/morning', methods=['POST'])
@jwt_required()
def trigger_morning_routine():
    try:
        logger.info("Manual trigger: Morning plans generation")
        scheduler_service.generate_morning_plans()
        
        return jsonify({
            'message': 'Morning plans generated successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Manual morning trigger error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@scheduler_bp.route('/trigger/evening', methods=['POST'])
@jwt_required()
def trigger_evening_routine():
    try:
        logger.info("Manual trigger: Evening data preparation")
        scheduler_service.prepare_evening_data()
        
        return jsonify({
            'message': 'Evening data prepared successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Manual evening trigger error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500