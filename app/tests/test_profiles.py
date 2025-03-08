import pytest
from ..models import Profile, TopicArea, LearningStyle

@pytest.mark.asyncio
async def test_create_profile(async_client, sample_profile_data):
    student_id = 'test-student'
    response = await async_client.put(f'/api/profile/{student_id}', json=sample_profile_data)
    assert response.status_code == 200
    data = await response.get_json()
    
    assert data['student_id'] == student_id
    assert data['learning_style'] == sample_profile_data['learning_style']
    assert data['topic_preferences'] == sample_profile_data['topic_preferences']
    assert data['engagement_metrics'] == sample_profile_data['engagement_metrics']

@pytest.mark.asyncio
async def test_get_profile(async_client, sample_profile_data):
    student_id = 'test-student'
    # First create a profile
    await async_client.put(f'/api/profile/{student_id}', json=sample_profile_data)
    
    # Then get the profile
    response = await async_client.get(f'/api/profile/{student_id}')
    assert response.status_code == 200
    data = await response.get_json()
    
    assert data['student_id'] == student_id
    assert data['learning_style'] == sample_profile_data['learning_style']
    assert data['topic_preferences'] == sample_profile_data['topic_preferences']

@pytest.mark.asyncio
async def test_update_profile(async_client, sample_profile_data):
    student_id = 'test-student'
    # First create a profile
    await async_client.put(f'/api/profile/{student_id}', json=sample_profile_data)
    
    # Update the profile
    updated_data = {
        'learning_style': 'KINESTHETIC',
        'topic_preferences': {
            'MATH': 0.9,
            'SCIENCE': 0.7
        }
    }
    
    response = await async_client.put(f'/api/profile/{student_id}', json=updated_data)
    assert response.status_code == 200
    data = await response.get_json()
    
    assert data['learning_style'] == updated_data['learning_style']
    assert data['topic_preferences'] == updated_data['topic_preferences']

@pytest.mark.asyncio
async def test_get_nonexistent_profile(async_client):
    response = await async_client.get('/api/profile/nonexistent')
    assert response.status_code == 404
    data = await response.get_json()
    assert 'error' in data

@pytest.mark.asyncio
async def test_invalid_profile_data(async_client):
    student_id = 'test-student'
    invalid_data = {
        'learning_style': 'INVALID_STYLE',
        'topic_preferences': 'not_a_dict'
    }
    
    response = await async_client.put(f'/api/profile/{student_id}', json=invalid_data)
    assert response.status_code == 400
    data = await response.get_json()
    assert 'error' in data

@pytest.mark.asyncio
async def test_profile_validation(async_client):
    student_id = 'test-student'
    profiles = [
        {
            'learning_style': style.value,
            'topic_preferences': {'MATH': 0.8}
        }
        for style in LearningStyle
    ]
    
    for profile in profiles:
        response = await async_client.put(f'/api/profile/{student_id}', json=profile)
        assert response.status_code == 200
        data = await response.get_json()
        assert data['learning_style'] == profile['learning_style']

@pytest.mark.asyncio
async def test_profile_metrics_update(async_client, sample_message_data):
    student_id = 'test-student'
    session_id = 'test-session'
    
    # Create initial profile
    sample_profile = {
        'learning_style': 'VISUAL',
        'topic_preferences': {'MATH': 0.5},
        'engagement_metrics': {'total_messages': 0}
    }
    await async_client.put(f'/api/profile/{student_id}', json=sample_profile)
    
    # Send some messages
    for _ in range(3):
        await async_client.post(f'/api/chat/{session_id}', json={
            **sample_message_data,
            'student_id': student_id
        })
    
    # Check updated metrics
    response = await async_client.get(f'/api/profile/{student_id}')
    assert response.status_code == 200
    data = await response.get_json()
    
    metrics = data['engagement_metrics']
    assert metrics['total_messages'] >= 3
    assert 'avg_engagement' in metrics

@pytest.mark.asyncio
async def test_profile_topic_mastery(async_client, sample_message_data):
    student_id = 'test-student'
    session_id = 'test-session'
    
    # Create initial profile
    initial_profile = {
        'learning_style': 'VISUAL',
        'topic_preferences': {
            'MATH': 0.5,
            'SCIENCE': 0.3
        }
    }
    await async_client.put(f'/api/profile/{student_id}', json=initial_profile)
    
    # Send messages in different topics
    topics = ['MATH', 'SCIENCE']
    for topic in topics:
        message = {
            **sample_message_data,
            'topic_area': topic,
            'student_id': student_id,
            'complexity_score': 0.9
        }
        await async_client.post(f'/api/chat/{session_id}', json=message)
    
    # Check updated topic preferences
    response = await async_client.get(f'/api/profile/{student_id}')
    assert response.status_code == 200
    data = await response.get_json()
    
    preferences = data['topic_preferences']
    for topic in topics:
        assert preferences[topic] > initial_profile['topic_preferences'][topic]

@pytest.mark.asyncio
async def test_profile_learning_style_detection(async_client, sample_message_data):
    student_id = 'test-student'
    session_id = 'test-session'
    
    # Create initial profile without learning style
    initial_profile = {
        'topic_preferences': {'MATH': 0.5}
    }
    await async_client.put(f'/api/profile/{student_id}', json=initial_profile)
    
    # Send messages with different patterns
    messages = [
        "Can you show me a diagram?",
        "I prefer step-by-step explanations",
        "Let me try solving it myself"
    ]
    
    for msg in messages:
        await async_client.post(f'/api/chat/{session_id}', json={
            **sample_message_data,
            'content': msg,
            'student_id': student_id
        })
    
    # Check if learning style was detected
    response = await async_client.get(f'/api/profile/{student_id}')
    assert response.status_code == 200
    data = await response.get_json()
    
    assert data['learning_style'] is not None 

def test_create_profile(client, student_id, sample_profile_data):
    response = client.put(f'/api/profile/{student_id}', json=sample_profile_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == sample_profile_data['name']
    assert data['grade_level'] == sample_profile_data['grade_level']
    assert data['preferred_learning_style'] == sample_profile_data['preferred_learning_style']

def test_get_profile(client, student_id, sample_profile_data):
    # First check that profile doesn't exist
    response = client.get(f'/api/profile/{student_id}')
    assert response.status_code == 404
    
    # Create profile
    client.put(f'/api/profile/{student_id}', json=sample_profile_data)
    
    # Get profile
    response = client.get(f'/api/profile/{student_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == sample_profile_data['name']

def test_update_profile(client, student_id, sample_profile_data):
    # Create initial profile
    client.put(f'/api/profile/{student_id}', json=sample_profile_data)
    
    # Update profile
    updated_data = dict(sample_profile_data)
    updated_data['name'] = "Updated Name"
    response = client.put(f'/api/profile/{student_id}', json=updated_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == "Updated Name"

def test_get_nonexistent_profile(client):
    response = client.get('/api/profile/nonexistent')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data

def test_invalid_profile_data(client, student_id):
    invalid_data = {
        "name": "",  # Empty name
        "grade_level": "invalid",  # Should be integer
        "preferred_learning_style": "invalid_style"
    }
    response = client.put(f'/api/profile/{student_id}', json=invalid_data)
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_profile_validation(client, student_id):
    valid_styles = [style.value for style in LearningStyle]
    for style in valid_styles:
        profile_data = {
            "name": "Test Student",
            "grade_level": 8,
            "preferred_learning_style": style,
            "interests": ["math"]
        }
        response = client.put(f'/api/profile/{student_id}', json=profile_data)
        assert response.status_code == 200

def test_profile_metrics_update(client, student_id, sample_profile_data, sample_message_data):
    # Create initial profile
    client.put(f'/api/profile/{student_id}', json=sample_profile_data)
    
    # Send some messages
    session_id = "test_session"
    for _ in range(3):
        client.post(f'/api/chat/{session_id}', json=sample_message_data)
    
    # Check profile metrics
    response = client.get(f'/api/profile/{student_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert 'topic_mastery' in data
    assert TopicArea.MATH.value in data['topic_mastery']
    assert data['topic_mastery'][TopicArea.MATH.value] > 0

def test_profile_topic_mastery(client, student_id):
    initial_profile = {
        "name": "Test Student",
        "grade_level": 8,
        "preferred_learning_style": "visual",
        "interests": ["math"],
        "topic_mastery": {
            TopicArea.MATH.value: 0.5
        }
    }
    
    # Create profile
    client.put(f'/api/profile/{student_id}', json=initial_profile)
    
    # Simulate interactions
    session_id = "test_session"
    message = {
        "content": "Great explanation! I understand now.",
        "topic_area": TopicArea.MATH.value,
        "is_ai": False
    }
    
    # Send multiple positive interactions
    for _ in range(3):
        client.post(f'/api/chat/{session_id}', json=message)
    
    # Check if mastery increased
    response = client.get(f'/api/profile/{student_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['topic_mastery'][TopicArea.MATH.value] > 0.5

def test_profile_learning_style_detection(client, student_id, sample_profile_data):
    # Create initial profile without learning style
    initial_profile = dict(sample_profile_data)
    initial_profile.pop('preferred_learning_style', None)
    
    # Create profile
    client.put(f'/api/profile/{student_id}', json=initial_profile)
    
    # Simulate interactions that suggest a learning style
    session_id = "test_session"
    messages = [
        {
            "content": "Can you show me a diagram?",
            "topic_area": TopicArea.MATH.value,
            "is_ai": False
        },
        {
            "content": "I learn better with visual examples",
            "topic_area": TopicArea.SCIENCE.value,
            "is_ai": False
        }
    ]
    
    for message in messages:
        client.post(f'/api/chat/{session_id}', json=message)
    
    # Check if learning style was detected
    response = client.get(f'/api/profile/{student_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert 'preferred_learning_style' in data
    assert data['preferred_learning_style'] == 'visual' 