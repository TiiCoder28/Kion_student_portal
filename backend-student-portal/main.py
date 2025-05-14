from flask import Flask, jsonify, request
from flask_cors import CORS
from app.database import db
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from dotenv import load_dotenv
import os
from datetime import timedelta

# Load environment variables from .env file
load_dotenv()

def create_app():
    app = Flask(__name__)
    CORS(app, resources={
    r"/auth/*": {"origins": "http://localhost:5173", "methods": ["POST", "GET", "OPTIONS", "DELETE"], "allow_headers": ["Content-Type", "Authorization"]},
    r"/api/*": {"origins": "http://localhost:5173", "methods": ["POST", "GET", "OPTIONS", "DELETE"], "allow_headers": ["Content-Type", "Authorization"]}
},  supports_credentials=True)  
    exposed_headers = ['Authorization', 'Content-Type']
    app.after_request(lambda response: (response.headers.add('Access-Control-Expose-Headers', ', '.join(exposed_headers)), response)[1])

    # Configure PostgreSQL using environment variable
    DB_URI = os.getenv("DATABASE_URI")
    if not DB_URI:
        raise ValueError("DATABASE_URI not found in .env file")
    app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY")
    app.config['JWT_TOKEN_LOCATION'] = ['headers']
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 36000 # 1 hour
    app.config['JWT_HEADER_NAME'] = 'Authorization'
    app.config['JWT_HEADER_TYPE'] = 'Bearer'
    
    if not app.config['SQLALCHEMY_DATABASE_URI']:
        raise ValueError("DATABASE_URI not found in .env")
    if not app.config['JWT_SECRET_KEY']:
        raise ValueError("JWT_SECRET_KEY not found in .env file")
    
    jwt = JWTManager(app)  # Initialize JWTManager

    # Initialize database
    db.init_app(app)
    jwt.init_app(app)
 
    from app.routes import chat_bp
    from auth.routes import auth_bp

    app.register_blueprint(chat_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/auth")

    with app.app_context():
        db.create_all()

    return app

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        try: 
            db.create_all()
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            exit(1)
            
    app.run(debug=True, port=5000)