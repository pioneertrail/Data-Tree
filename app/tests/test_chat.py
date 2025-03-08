import pytest
from ..models import Message, TopicArea

@pytest.mark.asyncio
async def test_chat_post_message(async_client, sample_message_data):
    session_id = 'test-session'
    response = await async_client.post(f'/api/chat/{session_id}', json=sample_message_data)
    assert response.status_code == 201
    data = await response.get_json()
    
    assert 'user_message' in data
    assert 'ai_response' in data
    assert data['user_message']['content'] == sample_message_data['content']
    assert data['user_message']['topic_area'] == sample_message_data['topic_area']

@pytest.mark.asyncio
async def test_chat_get_messages(async_client, sample_message_data):
    session_id = 'test-session'
    # First post a message
    await async_client.post(f'/api/chat/{session_id}', json=sample_message_data)
    
    # Then get the chat history
    response = await async_client.get(f'/api/chat/{session_id}')
    assert response.status_code == 200
    data = await response.get_json()
    
    assert isinstance(data, list)
    assert len(data) >= 2  # Should have user message and AI response
    assert data[0]['content'] == sample_message_data['content']
    assert data[0]['topic_area'] == sample_message_data['topic_area']

@pytest.mark.asyncio
async def test_chat_invalid_request(async_client):
    session_id = 'test-session'
    response = await async_client.post(f'/api/chat/{session_id}', json={})
    assert response.status_code == 400
    data = await response.get_json()
    assert 'error' in data

@pytest.mark.asyncio
async def test_chat_ai_response(async_client, sample_message_data):
    session_id = 'test-session'
    response = await async_client.post(f'/api/chat/{session_id}', json=sample_message_data)
    assert response.status_code == 201
    data = await response.get_json()
    
    assert 'ai_response' in data
    assert data['ai_response']['is_ai'] == 1
    assert data['ai_response']['topic_area'] == sample_message_data['topic_area']

@pytest.mark.asyncio
async def test_message_analytics(async_client, sample_message_data):
    session_id = 'test-session'
    # Post multiple messages
    for _ in range(3):
        await async_client.post(f'/api/chat/{session_id}', json=sample_message_data)
    
    # Get analytics
    response = await async_client.get(f'/api/analytics/topics/{session_id}')
    assert response.status_code == 200
    data = await response.get_json()
    
    assert 'total_messages' in data
    assert data['total_messages'] >= 6  # 3 user messages + 3 AI responses
    assert 'topic_metrics' in data
    assert 'MATH' in data['topic_metrics']
    assert 'timeline' in data

@pytest.mark.asyncio
async def test_session_isolation(async_client, sample_message_data):
    session1 = 'test-session-1'
    session2 = 'test-session-2'
    
    # Post messages to both sessions
    await async_client.post(f'/api/chat/{session1}', json=sample_message_data)
    await async_client.post(f'/api/chat/{session2}', json=sample_message_data)
    
    # Check that messages are isolated
    response1 = await async_client.get(f'/api/chat/{session1}')
    response2 = await async_client.get(f'/api/chat/{session2}')
    
    data1 = await response1.get_json()
    data2 = await response2.get_json()
    
    assert len(data1) == 2  # User message + AI response
    assert len(data2) == 2  # User message + AI response
    assert data1[0]['session_id'] == session1
    assert data2[0]['session_id'] == session2

def test_send_message(client, session_id, sample_message):
    """Test sending a message and getting AI response"""
    response = client.post(f'/api/chat/{session_id}', json=sample_message)
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['content'] == sample_message['content']
    assert data['sender_type'] == SenderType.STUDENT.value
    assert data['topic'] == TopicArea.MATH.value
    
    # Check that message was saved to database
    messages = Message.query.filter_by(session_id=session_id).all()
    assert len(messages) >= 1  # Should be at least 1 (student message)
    
    # If AI response was generated, there should be 2 messages
    if len(messages) == 2:
        ai_msg = [m for m in messages if m.sender_type == SenderType.AI.value][0]
        assert ai_msg.topic == TopicArea.MATH.value
        assert isinstance(ai_msg.response_time, int)

def test_get_chat_history(client, session_id, sample_message):
    """Test retrieving chat history"""
    # First send a message
    client.post(f'/api/chat/{session_id}', json=sample_message)
    
    # Then get history
    response = client.get(f'/api/chat/{session_id}')
    assert response.status_code == 200
    
    messages = response.get_json()
    assert isinstance(messages, list)
    assert len(messages) >= 1
    
    # Verify message structure
    msg = messages[0]
    assert all(k in msg for k in ['content', 'sender_type', 'topic', 'analytics'])
    assert all(k in msg['analytics'] for k in ['complexity', 'engagement'])

def test_invalid_message(client, session_id):
    """Test sending invalid message data"""
    # Missing required fields
    response = client.post(f'/api/chat/{session_id}', json={})
    assert response.status_code != 200
    
    # Invalid sender type
    response = client.post(f'/api/chat/{session_id}', json={
        'content': 'test',
        'sender_type': 'INVALID',
        'topic': TopicArea.MATH.value
    })
    assert response.status_code != 200

def test_chat_post_message(client, session_id, sample_message_data):
    response = client.post(f'/api/chat/{session_id}', json=sample_message_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data['content'] == sample_message_data['content']
    assert data['topic_area'] == sample_message_data['topic_area']
    assert not data['is_ai']

def test_chat_get_messages(client, session_id, sample_message_data):
    # First post a message
    client.post(f'/api/chat/{session_id}', json=sample_message_data)
    
    # Then get all messages
    response = client.get(f'/api/chat/{session_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_chat_invalid_request(client, session_id):
    response = client.post(f'/api/chat/{session_id}', json={})
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_chat_ai_response(client, session_id, sample_message_data):
    response = client.post(f'/api/chat/{session_id}', json=sample_message_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data['is_ai']

def test_message_analytics(client, session_id, sample_message_data):
    # Post a message first
    client.post(f'/api/chat/{session_id}', json=sample_message_data)
    
    # Get analytics
    response = client.get(f'/api/analytics/messages/{session_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert 'complexity_score' in data
    assert 'engagement_score' in data

def test_session_isolation(client):
    session1 = "test_session_1"
    session2 = "test_session_2"
    message = {
        "content": "Test message",
        "topic_area": TopicArea.MATH.value,
        "is_ai": False
    }
    
    # Post message to session 1
    client.post(f'/api/chat/{session1}', json=message)
    
    # Check that session 2 doesn't have the message
    response = client.get(f'/api/chat/{session2}')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 0

def test_invalid_message(client, session_id):
    invalid_data = {
        "content": "",  # Empty content
        "topic_area": "invalid_topic",
        "is_ai": False
    }
    response = client.post(f'/api/chat/{session_id}', json=invalid_data)
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data 