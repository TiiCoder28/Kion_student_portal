from flask import Flask
from .routes import auth_bp  # Import the auth_bp Blueprint from the routes module

def init_auth(app: Flask):
    """
    Initialize the authentication module and register the auth Blueprint.
    """
    app.register_blueprint(auth_bp, url_prefix='/auth')