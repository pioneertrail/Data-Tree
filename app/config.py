import os

class Config:
    """Base configuration."""
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///chat.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    
    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Rate limiting
    RATE_LIMIT = 30  # requests per minute
    RATE_WINDOW = 60  # seconds
    
    # Session
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes
    
    # Content settings
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB max file size
    MAX_MESSAGE_LENGTH = 5000  # characters
    
    # AI settings
    AI_MODEL = "gpt-3.5-turbo"
    AI_TEMPERATURE = 0.7
    AI_MAX_TOKENS = 300
    
    # Aha moment settings
    AHA_CONFIDENCE_THRESHOLD = 0.7
    AHA_STRONG_THRESHOLD = 0.9
    
    # Analytics settings
    ANALYTICS_WINDOW = 24 * 60 * 60  # 24 hours in seconds
    MIN_INTERACTIONS_FOR_ANALYTICS = 5

class TestConfig(Config):
    """Test configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test'
    os.environ['TESTING'] = 'true'

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    DEVELOPMENT = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    
    # Use more secure session settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    # Stricter rate limiting
    RATE_LIMIT = 20  # requests per minute
    
    # More conservative AI settings
    AI_TEMPERATURE = 0.5
    AI_MAX_TOKENS = 250

config = {
    'development': DevelopmentConfig,
    'testing': TestConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 