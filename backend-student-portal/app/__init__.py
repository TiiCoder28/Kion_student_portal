from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)  # Enable CORS for frontend communication

    from app.routes import chat_bp
    app.register_blueprint(chat_bp, url_prefix="/api")

    return app
