"""Test configuration and fixtures."""
import pytest
import logging
from flask import Flask
from app import create_app
from app.extensions import db
from app.models import Message, Profile, TopicArea, LearningStyle

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TestConfig:
    """Test configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'  # Use a file-based database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True  # Enable SQL query logging

@pytest.fixture(scope='function')
def app():
    """Create and configure a new app instance for each test."""
    app = create_app(TestConfig)
    
    # Create tables in a test-specific context
    with app.app_context():
        logger.info("Creating database tables in app fixture")
        db.drop_all()  # Clean up any existing tables
        
        # Import models to ensure they're registered with SQLAlchemy
        from app.models import Message, Profile
        
        # Create all tables fresh
        db.create_all()
        
        # Verify tables were created
        inspector = db.inspect(db.engine)
        table_names = inspector.get_table_names()
        logger.info(f"Created tables: {table_names}")
        
        yield app
        
        logger.info("Cleaning up database in app fixture")
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='function')
def client(app):
    """A test client for the app."""
    logger.info("Setting up test client")
    with app.test_client() as client:
        with app.app_context():
            # Ensure we have a fresh database for each test
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

@pytest.fixture(scope='function')
def db_session(app):
    """Create a fresh database session for a test."""
    logger.info("Setting up database session")
    with app.app_context():
        # Ensure we have a fresh database
        db.create_all()
        
        connection = db.engine.connect()
        transaction = connection.begin()
        
        options = dict(bind=connection, binds={})
        session = db.create_scoped_session(options=options)
        
        db.session = session
        
        yield session
        
        transaction.rollback()
        connection.close()
        session.remove()

@pytest.fixture
def session_id():
    """Generate a test session ID."""
    return "test_session_123"

@pytest.fixture
def student_id():
    """Generate a test student ID."""
    return "test_student_123"

@pytest.fixture
def sample_message_data():
    """Generate sample message data."""
    return {
        'content': 'Test message content',
        'topic_area': TopicArea.MATH.value,
        'is_ai': False
    }

@pytest.fixture
def sample_profile_data():
    """Generate sample profile data."""
    return {
        'learning_style': LearningStyle.VISUAL.value,
        'topic_preferences': {'math': 0.8, 'science': 0.6},
        'topic_mastery': {'math': 0.7, 'science': 0.5},
        'interaction_history': []
    }

@pytest.fixture
def sample_message(db_session, session_id, sample_message_data):
    """Create a sample message in the database."""
    message = Message(
        session_id=session_id,
        content=sample_message_data['content'],
        topic_area=sample_message_data['topic_area'],
        is_ai=sample_message_data['is_ai']
    )
    db_session.add(message)
    db_session.commit()
    return message 