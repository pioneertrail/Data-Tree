"""Flask application factory."""
from flask import Flask, jsonify, render_template
from app.extensions import db, init_db
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app(test_config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configure the Flask app
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize Flask extensions
    db.init_app(app)
    
    # Initialize database and create tables
    init_db(app)
    
    # Register blueprints
    from app.routes.ai import bp as ai_bp
    app.register_blueprint(ai_bp)
    
    @app.route('/')
    def index():
        """Render the main page."""
        return render_template('index.html')
        
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors."""
        return jsonify({'error': 'Not found'}), 404
        
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
        
    return app

# Create a default app instance for use in routes
_app = None

def get_app():
    """Get or create the default app instance."""
    global _app
    if _app is None:
        _app = create_app()
    return _app 