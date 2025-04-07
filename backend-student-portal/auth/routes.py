from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, unset_jwt_cookies, get_jwt
from flask_cors import CORS  # Import CORS for handling cross-origin requests
from flask_jwt_extended import JWTManager  # Import JWTManager for handling JWTs

from .models import User  # Import the User model from the models module
from app.database import db  # Import the shared SQLAlchemy instance

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'], endpoint='signup')
def signup():
    data = request.json
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')
    password = data.get('password')

    # Check if the email already exists
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists"}), 400

    # Create a new user
    new_user = User(
        first_name=first_name,
        last_name=last_name,
        email=email
    )
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    # Generate a JWT token for the new user
    access_token = create_access_token(identity=new_user.id)
    return jsonify({
        "message": "User created successfully",
        "access_token": access_token,
        "user": {
            "first_name": new_user.first_name,
            "last_name": new_user.last_name,
        }
    }), 201

@auth_bp.route('/login', methods=['POST'], endpoint='login')
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    # Find the user by email
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    # Generate a JWT token
    access_token = create_access_token(identity=user.id)
    return jsonify({"access_token": access_token}), 200

@auth_bp.route('/user', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    return jsonify({
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email
    })

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    
    jti = get_jwt()['jti']

    response = jsonify({"msg": "Successfully logged out"})
    unset_jwt_cookies(response)
    return response, 200