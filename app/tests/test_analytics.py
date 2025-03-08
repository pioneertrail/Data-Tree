import pytest
from ..models import Message, SenderType, TopicArea

@pytest.mark.asyncio
async def test_topic_analytics_empty(async_client):
    session_id = 'empty-session'
    response = await async_client.get(f'/api/analytics/topics/{session_id}')
    assert response.status_code == 404
    data = await response.get_json()
    assert 'error' in data

@pytest.mark.asyncio
async def test_topic_analytics_invalid_topic(async_client):
    response = await async_client.get('/api/analytics/topics/invalid-session')
    assert response.status_code == 404
    data = await response.get_json()
    assert 'error' in data

@pytest.mark.asyncio
async def test_topic_analytics_with_data(async_client, sample_message_data):
    session_id = 'test-session'
    # Post multiple messages
    for _ in range(3):
        await async_client.post(f'/api/chat/{session_id}', json=sample_message_data)
    
    response = await async_client.get(f'/api/analytics/topics/{session_id}')
    assert response.status_code == 200
    data = await response.get_json()
    
    assert data['session_id'] == session_id
    assert data['total_messages'] >= 6  # 3 user messages + 3 AI responses
    assert 'topic_metrics' in data
    assert 'MATH' in data['topic_metrics']
    assert 'timeline' in data
    
    math_metrics = data['topic_metrics']['MATH']
    assert 'message_count' in math_metrics
    assert 'avg_complexity' in math_metrics
    assert 'avg_engagement' in math_metrics

@pytest.mark.asyncio
async def test_multiple_topics(async_client):
    session_id = 'multi-topic-session'
    topics = ['MATH', 'SCIENCE', 'HISTORY']
    
    # Post messages with different topics
    for topic in topics:
        message_data = {
            'content': f'Test message for {topic}',
            'topic_area': topic,
            'complexity_score': 0.7,
            'engagement_score': 0.8
        }
        await async_client.post(f'/api/chat/{session_id}', json=message_data)
    
    response = await async_client.get(f'/api/analytics/topics/{session_id}')
    assert response.status_code == 200
    data = await response.get_json()
    
    assert len(data['topic_metrics']) == len(topics)
    for topic in topics:
        assert topic in data['topic_metrics']
        topic_data = data['topic_metrics'][topic]
        assert topic_data['message_count'] >= 2  # User message + AI response

@pytest.mark.asyncio
async def test_analytics_aggregation(async_client, sample_message_data):
    # Create multiple sessions with messages
    sessions = ['session1', 'session2', 'session3']
    for session_id in sessions:
        await async_client.post(f'/api/chat/{session_id}', json=sample_message_data)
    
    response = await async_client.get('/api/analytics/aggregate')
    assert response.status_code == 200
    data = await response.get_json()
    
    assert data['total_sessions'] == len(sessions)
    assert data['total_messages'] >= len(sessions) * 2  # Each session has user message + AI response
    assert 'topic_metrics' in data
    assert 'overall_metrics' in data
    assert 'avg_complexity' in data['overall_metrics']
    assert 'avg_engagement' in data['overall_metrics']

@pytest.mark.asyncio
async def test_analytics_no_messages(async_client):
    response = await async_client.get('/api/analytics/aggregate')
    assert response.status_code == 404
    data = await response.get_json()
    assert 'error' in data

def test_topic_analytics_empty(client, session_id):
    response = client.get(f'/api/analytics/topics/{session_id}')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data

def test_topic_analytics_invalid_topic(client):
    response = client.get('/api/analytics/topics/invalid-session')
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_topic_analytics_with_data(client, session_id, sample_message_data):
    # Create some messages first
    client.post(f'/api/chat/{session_id}', json=sample_message_data)
    
    # Get analytics
    response = client.get(f'/api/analytics/topics/{session_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['topic'] == TopicArea.MATH.value
    assert data['total_messages'] > 0
    assert 'complexity_score' in data
    assert 'engagement_score' in data
    assert 'timeline' in data

def test_analytics_no_messages(client):
    response = client.get(f'/api/analytics/topic/{TopicArea.MATH.value}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['total_messages'] == 0
    assert data['total_sessions'] == 0
    assert len(data['topic_stats']) == 0

def test_analytics_aggregation(client, session_id, sample_message_data):
    # Create messages for different topics
    math_message = sample_message_data
    science_message = dict(sample_message_data)
    science_message['topic_area'] = TopicArea.SCIENCE.value
    
    client.post(f'/api/chat/{session_id}', json=math_message)
    client.post(f'/api/chat/{session_id}', json=science_message)
    
    # Get aggregate analytics
    response = client.get('/api/analytics')
    assert response.status_code == 200
    data = response.get_json()
    assert data['total_messages'] > 0
    assert data['total_sessions'] > 0
    assert len(data['topic_stats']) > 0
    
    # Check topic stats
    for topic_stat in data['topic_stats']:
        assert topic_stat['topic'] in [TopicArea.MATH.value, TopicArea.SCIENCE.value]
        assert topic_stat['message_count'] > 0
        assert 'avg_complexity' in topic_stat
        assert 'avg_engagement' in topic_stat

def test_multiple_topics(client, db_session, session_id):
    """Test analytics across different topics"""
    # Create messages for different topics
    topics = [TopicArea.MATH, TopicArea.SCIENCE]
    for topic in topics:
        msg = Message(
            content=f'Question about {topic.value}',
            topic_area=topic,
            session_id=session_id,
            is_ai=False,
            complexity_score=0.5,
            engagement_score=0.5
        )
        db_session.add(msg)
    db_session.commit()
    
    # Check each topic's analytics
    for topic in topics:
        response = client.get(f'/api/analytics/topic/{topic.value}')
        assert response.status_code == 200
        data = response.get_json()
        assert data['total_messages'] == 1
        assert 'avg_complexity' in data
        assert 'avg_engagement' in data

def test_analytics_aggregation(client, db_session, session_id):
    """Test analytics aggregation with multiple messages"""
    # Create multiple messages with varying scores
    scores = [
        (0.5, 0.6),
        (0.7, 0.8),
        (0.9, 0.7)
    ]
    
    for complexity, engagement in scores:
        msg = Message(
            content='Test message',
            topic_area=TopicArea.MATH,
            session_id=session_id,
            is_ai=False,
            complexity_score=complexity,
            engagement_score=engagement
        )
        db_session.add(msg)
    db_session.commit()
    
    response = client.get(f'/api/analytics/topic/{TopicArea.MATH.value}')
    assert response.status_code == 200
    data = response.get_json()
    
    # Check averages
    expected_complexity = sum(s[0] for s in scores) / len(scores)
    expected_engagement = sum(s[1] for s in scores) / len(scores)
    
    assert abs(data['avg_complexity'] - expected_complexity) < 0.01
    assert abs(data['avg_engagement'] - expected_engagement) < 0.01
    assert data['total_messages'] == len(scores) 