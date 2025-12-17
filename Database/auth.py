from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt, current_user,get_jwt_identity
from models import User, TokenBlocklist

auth_bp = Blueprint('auth', __name__)

@auth_bp.post('/register')
def register_user():

    data = request.get_json()

    user = User.find_by_username(username= data.get('username'))

    if user is not None:
        return jsonify({"error": "User already exists"}), 403

    new_user = User(
        username = data.get('username'),
        city = data.get('city')
    )

    new_user.set_password(password= data.get('password'))

    new_user.save()

    return jsonify({"message": "User created"}), 201

@auth_bp.post('/login')
def login_user():
    data = request.get_json()

    user = User.find_by_username(username= data.get('username'))

    if user and user.check_password(password= data.get('password')):
        access_token = create_access_token(identity=user.username)
        refresh_token = create_refresh_token(identity=user.username)

        return jsonify({
            "message": "Login successful",
            "access_token": access_token,
            "refresh_token": refresh_token
        }), 200
    
    return jsonify({"error": "Invalid credentials"}), 401

@auth_bp.get('/whoami')
@jwt_required()
def whoami():
    claims = get_jwt()
    return jsonify({"message": "You are logged in", "claims": claims}), 200

@auth_bp.get('/refresh')
@jwt_required(refresh=True)
def refresh_access():
    identity = get_jwt_identity()

    new_access_token = create_access_token(identity=identity)

    return jsonify({"access_token": new_access_token})


@auth_bp.get("/logout")
@jwt_required(refresh=True)
def logout():
    jwt = get_jwt()
    jti = jwt['jti']

    token_type = jwt['type']

    token_b = TokenBlocklist(jti=jti)
    token_b.save()

    return jsonify({"message": f"Successfully logged out {token_type} token"}), 200