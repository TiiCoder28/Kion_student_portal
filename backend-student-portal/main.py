from flask import Flask
from flask_cors import CORS
from app.database import db
from flask_jwt_extended import JWTManager
from auth.models import User  # Import the User model
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

def create_app():
    app = Flask(__name__)
    CORS(app, resources={
    r"/auth/*": {"origins": "http://localhost:5173", "methods": ["POST", "GET"], "allow_headers": ["Content-Type", "Authorization"]},
    r"/api/*": {"origins": "http://localhost:5173", "methods": ["POST", "GET"], "allow_headers": ["Content-Type", "Authorization"]}
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
    if not app.config['JWT_SECRET_KEY']:
        raise ValueError("JWT_SECRET_KEY not found in .env file")
    
    app.config['JWT_TOKEN_LOCATION'] = ['headers']
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600  # 1 hour
    jwt = JWTManager(app)  # Initialize JWTManager

    # Initialize database
    db.init_app(app)

    # Debug: Verify database connection
    with app.app_context():
        try:
            with db.engine.connect() as connection:
                result = connection.exec_driver_sql("SELECT current_database();")
                db_name = result.scalar()
                print(f"✅ Connected to database: {db_name}")
        except Exception as e:
            print(f"❌ ERROR: Could not connect to database! Error: {str(e)}")
            exit(1)

    # Debug: Check registered models
    with app.app_context():
        print("\n⏳ Checking registered models...")
        try:
            for table in db.metadata.tables.values():
                print(f"✅ Found table: {table.name}")
        except Exception as e:
            print(f"❌ ERROR: Could not check registered models! Error: {str(e)}")

    # Import blueprints AFTER initializing db
    from app.routes import chat_bp
    from auth.routes import auth_bp

    app.register_blueprint(chat_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/auth")

    return app

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        try:
            db.create_all()
            
            # List tables using SQLAlchemy 2.0+ compatible method
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print("✅ Tables in database:", tables)
        except Exception as e:
            print("\n❌ ERROR: Table creation failed!")
            print(f"❌ Error: {str(e)}")
            exit(1)
            
    app.run(debug=True, port=5000)