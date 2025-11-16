from flask import Flask
from flask_cors import CORS
from app.config import Config
from app.db import db


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Enable CORS for all routes
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Initialize SQLAlchemy
    db.init_app(app)
    
    # Register API blueprint
    from app.api.routes import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app

