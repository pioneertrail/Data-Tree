"""Basic tests for the AI Teacher System."""
import pytest
from app import create_app
from app.models import db as _db
from app.config import TestConfig

@pytest.fixture
def app():
    """Create application for the tests."""
    app = create_app(TestConfig)
    return app

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()

def test_app_exists(app):
    """Test that the app exists."""
    assert app is not None

def test_app_is_testing(app):
    """Test that the app is in testing mode."""
    assert app.config['TESTING']
    assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'

def test_client_get(client):
    response = client.get('/')
    assert response.status_code in (200, 404)  # Either is acceptable for root path 