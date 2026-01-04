from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt, current_user,get_jwt_identity
from app.models import User, TokenBlocklist
from app.extensions import db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validation
        required_fields = ['username', 'city', 'password']
        if not data or not all(k in data for k in required_fields):
            return jsonify({
                'error': 'Missing required fields',
                'required': required_fields
            }), 400
        
        # prüf ob user exist
        existing_user = User.find_by_username(username=data['username'])
        if existing_user:
            return jsonify({'error': 'User already exists'}), 403
        
        # erstellt neu user
        new_user = User(
            username=data['username'],
            city=data['city'],
            sleep_goal_hours=data.get('sleep_goal_hours', 8.0)
        )
        new_user.set_password(data['password'])
        new_user.save()
        
        return jsonify({
            'message': 'User created successfully',
            'user': new_user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        # Validation
        required_fields = ['username', 'password']
        if not data or not all(k in data for k in required_fields):
            return jsonify({
                'error': 'Missing required fields',
                'required': required_fields
            }), 400
        
        # user finden
        user = User.find_by_username(username=data['username'])
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # erstellt tokens
        access_token = create_access_token(identity=user.username)
        refresh_token = create_refresh_token(identity=user.username)
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():

    try:
        username = get_jwt_identity()
        user = User.find_by_username(username=username)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@auth_bp.route('/refresh', methods=['GET', 'POST'])
@jwt_required(refresh=True)
def refresh_access():
   
    try:
        identity = get_jwt_identity()
        new_access_token = create_access_token(identity=identity)
        
        return jsonify({
            'access_token': new_access_token
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@auth_bp.route('/logout', methods=['GET', 'POST'])
@jwt_required(refresh=True)
def logout():
    
    try:
        jwt_data = get_jwt()
        jti = jwt_data['jti']
        token_type = jwt_data['type']
        
        # in blocklist hinzufügen
        token_b = TokenBlocklist(jti=jti)
        token_b.save()
        
        return jsonify({
            'message': f'Successfully logged out {token_type} token'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@auth_bp.route('/whoami', methods=['GET'])
@jwt_required()
def whoami():
    
    try:
        claims = get_jwt()
        return jsonify({
            'message': 'You are logged in',
            'claims': claims
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500