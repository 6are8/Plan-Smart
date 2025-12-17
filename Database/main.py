from flask import Flask, jsonify
from extensions import db, jwt
from auth import auth_bp
from users import user_bp
from models import User, TokenBlocklist
from flask_cors import CORS



def create_app():
    
    app = Flask(__name__)
    
    app.config.from_prefixed_env()

    CORS(app, resources={r"/*": {"origins": "http://localhost:4200"}}, supports_credentials=True)
    
    #initialize exts
    db.init_app(app)
    jwt.init_app(app)
    
    
    #register bluepints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(user_bp, url_prefix='/users')

    #additional claims
    @jwt.additional_claims_loader
    def make_additional_claims(identity):
        if identity == 'admin':
            return {"is_admin": True}
        return {"is_admin": False}


    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_data):
        return jsonify({"message": "Token has expired", "error": "token_expired"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"message": "Signature verification failed", "error": "invalid_token"}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"message": "Request doesnt contain valid token", "error": "authorization_header"}), 401
    

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return (jsonify({"message": "Request doesnt contain valid token", "error": "authorization_header"}), 401)
    


    @jwt.token_in_blocklist_loader
    def token_in_blocklist_callback(jwt_header, jwt_data):
        jti = jwt_data['jti']
        
        token = db.session.query(TokenBlocklist).filter(TokenBlocklist.jti == jti).scalar()
        return token is not None

    return app