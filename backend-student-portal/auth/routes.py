from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from .models import User  # Import the User model from the models module
from app.database import db  # Import the shared SQLAlchemy instance

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'])
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
        "access_token": access_token  # Return the token
    }), 201

@auth_bp.route('/login', methods=['POST'])
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