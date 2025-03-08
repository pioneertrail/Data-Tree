"""Tests for AI routes."""
import pytest
from app.models import Message, TopicArea

def test_ai_response_generation(client):
    """Test generating an AI response."""
    data = {
        'content': 'What is a neural network?',
        'topic_area': 'science',
        'session_id': 'test_session_123'
    }
    response = client.post('/api/ai/generate', json=data)
    assert response.status_code == 200
    assert response.json['content']
    assert response.json['topic_area'] == 'science'

def test_ai_context_handling(client):
    """Test handling conversation context."""
    # First message
    data1 = {
        'content': 'What is a neural network?',
        'topic_area': 'science',
        'session_id': 'test_session_123'
    }
    response1 = client.post('/api/ai/generate', json=data1)
    assert response1.status_code == 200
    
    # Get context
    response2 = client.get('/api/ai/context/test_session_123')
    assert response2.status_code == 200
    assert len(response2.json) == 1

def test_ai_error_handling(client):
    """Test error handling for invalid requests."""
    # Missing required fields
    data = {
        'content': 'What is a neural network?'
        # Missing topic_area and session_id
    }
    response = client.post('/api/ai/generate', json=data)
    assert response.status_code == 400
    assert 'error' in response.json

def test_ai_response_format(client):
    """Test AI response format."""
    data = {
        'content': 'What is a neural network?',
        'topic_area': 'science',
        'session_id': 'test_session_123'
    }
    response = client.post('/api/ai/generate', json=data)
    assert response.status_code == 200
    assert 'content' in response.json
    assert 'topic_area' in response.json
    assert 'analytics' in response.json
    assert 'complexity_score' in response.json['analytics']
    assert 'engagement_score' in response.json['analytics']
    assert 'topic_relevance' in response.json['analytics']

def test_ai_topic_consistency(client):
    """Test that AI responses maintain topic consistency."""
    # Student message
    student_data = {
        'content': 'What is a neural network?',
        'topic_area': 'science',
        'session_id': 'test_session_123'
    }
    response = client.post('/api/ai/generate', json=student_data)
    assert response.status_code == 200
    student_msg = response.json
    
    # AI response should have same topic
    assert student_msg['topic_area'] == 'science'

def test_ai_response_metrics(client):
    """Test that AI responses include analytics metrics."""
    data = {
        'content': 'Explain neural networks',
        'topic_area': 'science',
        'session_id': 'test_session_123'
    }
    response = client.post('/api/ai/generate', json=data)
    assert response.status_code == 200
    msg = response.json
    assert 'analytics' in msg
    assert 0 <= msg['analytics']['complexity_score'] <= 1
    assert 0 <= msg['analytics']['engagement_score'] <= 1
    assert 0 <= msg['analytics']['topic_relevance'] <= 1 