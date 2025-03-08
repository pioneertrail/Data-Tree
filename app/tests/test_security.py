import pytest
import time
from ..models import Message, TopicArea
from flask import json

def test_message_sanitization(client, session_id):
    """Test that message content is properly sanitized"""
    malicious_messages = [
        {
            'content': '<script>alert("xss")</script>',
            'sender_type': SenderType.STUDENT.value,
            'topic_area': TopicArea.MATH.value
        },
        {
            'content': 'javascript:alert("xss")',
            'sender_type': SenderType.STUDENT.value,
            'topic_area': TopicArea.MATH.value
        },
        {
            'content': '"; DROP TABLE messages; --',
            'sender_type': SenderType.STUDENT.value,
            'topic_area': TopicArea.MATH.value
        }
    ]
    
    for msg in malicious_messages:
        response = client.post(f'/api/chat/{session_id}', json=msg)
        assert response.status_code == 201

    # Verify messages are sanitized
    response = client.get(f'/api/chat/{session_id}')
    assert response.status_code == 200
    messages = response.json
    for msg in messages:
        assert '<script>' not in msg['content']
        assert 'javascript:' not in msg['content']
        assert 'DROP TABLE' in msg['content']  # SQL commands are not sanitized, just parameterized

def test_rate_limiting(client, session_id):
    """Test rate limiting on message sending"""
    # Send messages in rapid succession
    message = {
        'content': 'Test message',
        'sender_type': SenderType.STUDENT.value,
        'topic_area': TopicArea.MATH.value
    }
    
    responses = []
    for _ in range(10):  # Try to send 10 messages quickly
        response = client.post(f'/api/chat/{session_id}', json=message)
        responses.append(response.status_code)
        time.sleep(0.1)  # Small delay to simulate rapid requests
    
    # Some of the later requests should be rate limited
    assert 429 in responses  # HTTP 429 Too Many Requests

def test_session_token_validation(client):
    """Test validation of session tokens"""
    invalid_sessions = [
        'invalid;token',  # Contains semicolon
        '../../../etc',   # Path traversal attempt
        'x' * 1000,      # Too long
        '',              # Empty
        '   ',          # Whitespace
        '<script>'      # HTML injection attempt
    ]
    
    for session in invalid_sessions:
        response = client.get(f'/api/chat/{session}')
        assert response.status_code == 400
        assert 'error' in response.json

def test_input_length_limits(client, session_id):
    """Test limits on input length"""
    long_message = {
        'content': 'x' * 10000,  # Very long message
        'sender_type': SenderType.STUDENT.value,
        'topic_area': TopicArea.MATH.value
    }
    
    response = client.post(f'/api/chat/{session_id}', json=long_message)
    assert response.status_code == 400
    assert 'error' in response.json

def test_content_type_validation(client, session_id):
    """Test validation of content type headers"""
    message = {
        'content': 'Test message',
        'sender_type': SenderType.STUDENT.value,
        'topic_area': TopicArea.MATH.value
    }
    
    # Test without content type header
    response = client.post(f'/api/chat/{session_id}', data=str(message))
    assert response.status_code == 415  # Unsupported Media Type
    assert 'error' in response.json
    
    # Test with incorrect content type
    response = client.post(f'/api/chat/{session_id}', 
                         data=str(message),
                         content_type='text/plain')
    assert response.status_code == 400

def test_error_response_format(client, session_id):
    """Test that error responses follow a consistent format"""
    # Test with invalid JSON
    response = client.post(f'/api/chat/{session_id}', 
                         data='invalid json',
                         content_type='application/json')
    assert response.status_code == 400
    data = response.json
    assert 'error' in data
    assert isinstance(data['error'], str)
    
    # Test with missing required fields
    response = client.post(f'/api/chat/{session_id}', 
                         json={'content': 'Test'})  # Missing sender_type and topic
    assert response.status_code == 400
    data = response.json
    assert 'error' in data
    assert 'message' in data

def test_concurrent_sessions(client):
    """Test handling of concurrent chat sessions"""
    sessions = [f'session_{i}' for i in range(5)]
    message = {
        'content': 'Test message',
        'sender_type': SenderType.STUDENT.value,
        'topic_area': TopicArea.MATH.value
    }
    
    # Send messages to different sessions concurrently
    for session in sessions:
        response = client.post(f'/api/chat/{session}', json=message)
        assert response.status_code == 201
    
    # Verify each session has its own messages
    for session in sessions:
        response = client.get(f'/api/chat/{session}')
        assert response.status_code == 200
        messages = response.json
        assert len(messages) == 1
        assert messages[0]['session_id'] == session

def test_invalid_json(client, session_id):
    """Test handling of invalid JSON data."""
    response = client.post(
        f'/api/chat/{session_id}',
        data='invalid json',
        content_type='application/json'
    )
    assert response.status_code == 400

def test_missing_required_fields(client, session_id):
    """Test handling of missing required fields."""
    # Missing sender_type
    data = {
        'content': 'Test message',
        'topic_area': TopicArea.MATH.value
    }
    response = client.post(f'/api/chat/{session_id}', json=data)
    assert response.status_code == 400
    assert 'error' in response.json

    # Missing content
    data = {
        'sender_type': SenderType.STUDENT.value,
        'topic_area': TopicArea.MATH.value
    }
    response = client.post(f'/api/chat/{session_id}', json=data)
    assert response.status_code == 400
    assert 'error' in response.json

def test_invalid_enum_values(client, session_id):
    """Test handling of invalid enum values."""
    # Invalid sender_type
    data = {
        'content': 'Test message',
        'sender_type': 'invalid_sender',
        'topic_area': TopicArea.MATH.value
    }
    response = client.post(f'/api/chat/{session_id}', json=data)
    assert response.status_code == 400
    assert 'error' in response.json

    # Invalid topic_area
    data = {
        'content': 'Test message',
        'sender_type': SenderType.STUDENT.value,
        'topic_area': 'invalid_topic'
    }
    response = client.post(f'/api/chat/{session_id}', json=data)
    assert response.status_code == 400
    assert 'error' in response.json

def test_xss_prevention(client, session_id):
    """Test prevention of XSS attacks."""
    data = {
        'content': '<script>alert("XSS")</script>',
        'sender_type': SenderType.STUDENT.value,
        'topic_area': TopicArea.MATH.value
    }
    response = client.post(f'/api/chat/{session_id}', json=data)
    assert response.status_code == 201

    # Verify the message is escaped when retrieved
    response = client.get(f'/api/chat/{session_id}')
    assert response.status_code == 200
    messages = response.json
    assert '<script>' not in messages[0]['content']

def test_sql_injection_prevention(client):
    """Test prevention of SQL injection attacks."""
    malicious_id = "1; DROP TABLE messages; --"
    response = client.get(f'/api/profile/{malicious_id}')
    assert response.status_code == 404  # Should be treated as non-existent ID

def test_rate_limiting(client, session_id):
    """Test rate limiting functionality."""
    # Send multiple requests in quick succession
    data = {
        'content': 'Test message',
        'sender_type': SenderType.STUDENT.value,
        'topic_area': TopicArea.MATH.value
    }
    
    responses = []
    for _ in range(50):  # Attempt to send 50 messages quickly
        responses.append(
            client.post(f'/api/chat/{session_id}', json=data)
        )
    
    # Check if any responses indicate rate limiting
    assert any(r.status_code == 429 for r in responses)

def test_message_sanitization(client, session_id):
    msg = {
        "content": "<script>alert('xss')</script>",
        "topic_area": TopicArea.MATH.value,
        "is_ai": False
    }
    response = client.post(f'/api/chat/{session_id}', json=msg)
    assert response.status_code == 200
    data = response.get_json()
    assert '<script>' not in data['content']

def test_session_token_validation(client):
    session = "invalid_session_token"
    response = client.get(f'/api/chat/{session}')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 0

def test_input_length_limits(client, session_id):
    long_message = {
        "content": "a" * 10000,  # Very long message
        "topic_area": TopicArea.MATH.value,
        "is_ai": False
    }
    response = client.post(f'/api/chat/{session_id}', json=long_message)
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_content_type_validation(client, session_id):
    response = client.post(
        f'/api/chat/{session_id}',
        data="not json data",
        content_type='text/plain'
    )
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_error_response_format(client, session_id):
    data = {
        "content": "",  # Empty content
        "topic_area": TopicArea.MATH.value,
        "is_ai": False
    }
    response = client.post(f'/api/chat/{session_id}', json=data)
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert isinstance(data['error'], str)

def test_concurrent_sessions(client):
    sessions = ["session1", "session2", "session3"]
    message = {
        "content": "Test message",
        "topic_area": TopicArea.MATH.value,
        "is_ai": False
    }
    
    # Post to multiple sessions
    for session in sessions:
        response = client.post(f'/api/chat/{session}', json=message)
        assert response.status_code == 200
    
    # Verify each session has its own messages
    for session in sessions:
        response = client.get(f'/api/chat/{session}')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1

def test_invalid_json(client, session_id):
    response = client.post(
        f'/api/chat/{session_id}',
        data="{invalid json",
        content_type='application/json'
    )
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_missing_required_fields(client, session_id):
    data = {
        "content": "Test message",
        # Missing topic_area
        "is_ai": False
    }
    response = client.post(f'/api/chat/{session_id}', json=data)
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_invalid_enum_values(client, session_id):
    data = {
        "content": "Test message",
        "topic_area": "invalid_topic",  # Invalid topic
        "is_ai": False
    }
    response = client.post(f'/api/chat/{session_id}', json=data)
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_xss_prevention(client, session_id):
    data = {
        "content": '<img src="x" onerror="alert(1)">',
        "topic_area": TopicArea.MATH.value,
        "is_ai": False
    }
    response = client.post(f'/api/chat/{session_id}', json=data)
    assert response.status_code == 200
    data = response.get_json()
    assert '<img' not in data['content']

def test_sql_injection_prevention(client):
    malicious_id = "1; DROP TABLE users;"
    response = client.get(f'/api/profile/{malicious_id}')
    assert response.status_code == 404

def test_rate_limiting(client, session_id):
    data = {
        "content": "Test message",
        "topic_area": TopicArea.MATH.value,
        "is_ai": False
    }
    
    # Send many requests quickly
    responses = []
    for _ in range(50):
        response = client.post(f'/api/chat/{session_id}', json=data)
        responses.append(response.status_code)
    
    # At least one request should be rate limited
    assert 429 in responses 