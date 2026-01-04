from flask import Flask, jsonify
from flask_cors import CORS
from app.config import config
from app.extensions import db, jwt
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    CORS(app, resources={
        r"/*": {
            "origins": ["http://localhost:4200"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # extensions Initializierung
    db.init_app(app)
    jwt.init_app(app)
    
    # Blueprints Register
    from app.routes import auth_bp, journal_bp, morning_bp, evening_bp, scheduler_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(journal_bp, url_prefix='/journal')
    app.register_blueprint(morning_bp, url_prefix='/morning')
    app.register_blueprint(evening_bp, url_prefix='/evening')
    app.register_blueprint(scheduler_bp, url_prefix='/scheduler')
    
    # JWT callbacks
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        from app.models import TokenBlocklist
        jti = jwt_payload['jti']
        token = TokenBlocklist.query.filter_by(jti=jti).first()
        return token is not None
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'error': 'Token has expired'}), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'error': 'Invalid token'}), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'error': 'Missing token'}), 401
    
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'message': 'STRIVO Backend',
            'version': '1.0.0'
        }), 200
    
    with app.app_context():
        db.create_all()
        print("✅ Database tables created")
        
        from app.services.scheduler_service import scheduler_service
        scheduler_service.init_app(app)
        print("✅ Scheduler initialized")
    
    return app