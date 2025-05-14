from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, unset_jwt_cookies, get_jwt
from flask_cors import CORS  
from flask_jwt_extended import JWTManager 
from .models import User  
from app.database import db 
import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException


auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'], endpoint='signup')
def signup():
    data = request.json
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')
    phone_number = data.get('phone_number')
    country_code = data.get('country_code')
    password = data.get('password')

    # Validate that either email or phone is provided
    if not email and not phone_number:
        return jsonify({"error": "Either email or phone number is required"}), 400
    
    # Validate phone number if provided
    if phone_number:
        if not country_code:
            return jsonify({"error": "Country code is required with phone number"}), 400
        try:
            parsed_number = phonenumbers.parse(phone_number, country_code)
            if not phonenumbers.is_valid_number(parsed_number):
                return jsonify({"error": "Invalid phone number for the given country code"}), 400
            # Format the number in E164 format
            phone_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        except NumberParseException as e:
            return jsonify({"error": str(e)}), 400
        
        # Check if phone number already exists
        if User.query.filter_by(phone_number=phone_number).first():
            return jsonify({"error": "Phone number already exists"}), 400

    # Check if email already exists (if provided)
    if email and User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists"}), 400

    # Create a new user
    new_user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone_number=phone_number,
        country_code=country_code
    )
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    # Generate a JWT token for the new user
    access_token = create_access_token(identity=str(new_user.id))
    return jsonify({
        "message": "User created successfully",
        "access_token": access_token,
        "user": {
            "first_name": new_user.first_name,
            "last_name": new_user.last_name,
            "email": new_user.email,
            "phone_number": new_user.phone_number
        }
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    phone_number = data.get('phone_number')
    country_code = data.get('country_code')
    password = data.get('password')

    # Validate that either email or phone is provided
    if not email and not phone_number:
        return jsonify({"error": "Either email or phone number is required"}), 400
    
    user = None
    
    if email:
        user = User.query.filter_by(email=email).first()
    else:
        # Validate and format phone number
        try:
            parsed_number = phonenumbers.parse(phone_number, country_code)
            if not phonenumbers.is_valid_number(parsed_number):
                return jsonify({"error": "Invalid phone number for the given country code"}), 400
            formatted_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
            user = User.query.filter_by(phone_number=formatted_number).first()
        except NumberParseException as e:
            return jsonify({"error": str(e)}), 400

    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(identity=str(user.id))
    
    return jsonify({
        "access_token": access_token,
        "user": {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone_number": user.phone_number
        }
    }), 200


@auth_bp.route("/user", methods=["GET"])
@jwt_required()
def get_user():
    try:
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({"error": "Invalid token"}), 401
            
        # Convert to int since your DB likely uses integer IDs
        user = User.query.get(int(user_id))
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        return jsonify({
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    
    jti = get_jwt()['jti']

    response = jsonify({"msg": "Successfully logged out"})
    unset_jwt_cookies(response)
    return response, 200