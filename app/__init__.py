"""Flask application factory."""
from flask import Flask, jsonify, render_template
from app.extensions import db, migrate

def create_app(config_class=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configure the app
    if config_class is None:
        # Default configuration
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    else:
        app.config.from_object(config_class)
    
    # Initialize Flask extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    with app.app_context():
        # Import all models to register them with SQLAlchemy
        from app.models import (
            Message, Profile, TestResult, 
            TopicArea, SubjectArea, InteractionType, SenderType
        )
        
        # Create tables if they don't exist
        db.create_all()
        
        # Register blueprints
        from app.routes.ai import bp as ai_bp
        from app.routes.chat import bp as chat_bp
        from app.routes.profiles import bp as profiles_bp
        from app.routes.analytics import bp as analytics_bp
        
        app.register_blueprint(ai_bp, url_prefix='/api/ai')
        app.register_blueprint(chat_bp)
        app.register_blueprint(profiles_bp)
        app.register_blueprint(analytics_bp)

        @app.route('/')
        def index():
            return render_template('index.html')
    
    return app

# Create a default app instance for use in routes
_app = None

def get_app():
    """Get or create the default app instance."""
    global _app
    if _app is None:
        _app = create_app()
    return _app 