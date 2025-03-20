from flask import Flask
from flask_cors import CORS
from app.routes import chat_bp  # Import chat blueprint

def create_app():
    app = Flask(__name__)
    CORS(app)  # Enable CORS for frontend communication

    # Register the chat blueprint with the "/api" prefix
    app.register_blueprint(chat_bp, url_prefix="/api")

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)