from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import openai
from dotenv import load_dotenv
import time
import re
import bleach
from functools import wraps

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///education.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Import models after db initialization to avoid circular imports
from app.models import Message, LearningProfile, SenderType, TopicArea

# Configure OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Rate limiting configuration
RATE_LIMIT = 10  # requests
RATE_WINDOW = 60  # seconds
rate_limit_store = {}

def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        now = time.time()
        ip = request.remote_addr
        
        if ip in rate_limit_store:
            requests = [t for t in rate_limit_store[ip] if now - t < RATE_WINDOW]
            if len(requests) >= RATE_LIMIT:
                return jsonify({'error': 'Too many requests'}), 429
            rate_limit_store[ip] = requests + [now]
        else:
            rate_limit_store[ip] = [now]
        
        return f(*args, **kwargs)
    return decorated_function

def sanitize_input(content):
    """Sanitize user input"""
    # Remove any script tags and dangerous content
    cleaned = bleach.clean(content)
    # Basic validation
    if len(cleaned) > 5000:  # Limit message length
        return None
    return cleaned

def validate_session_token(session_id):
    """Validate session token format"""
    if not session_id or len(session_id) > 100:
        return False
    # Only allow alphanumeric and underscore
    return bool(re.match(r'^[a-zA-Z0-9_]+$', session_id))

@app.route('/api/chat/<session_id>', methods=['GET'])
def get_chat_history(session_id):
    """Get chat history for a session"""
    if not validate_session_token(session_id):
        return jsonify({'error': 'Invalid session ID'}), 400
    
    messages = Message.query.filter_by(session_id=session_id).order_by(Message.timestamp).all()
    return jsonify([msg.to_dict() for msg in messages])

@app.route('/api/chat/<session_id>', methods=['POST'])
@rate_limit
def send_message(session_id):
    """Send a new message"""
    if not validate_session_token(session_id):
        return jsonify({'error': 'Invalid session ID'}), 400
    
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400
    
    data = request.get_json()
    content = data.get('content')
    sender_type = data.get('sender_type')
    topic = data.get('topic')
    
    # Validate input
    if not all([content, sender_type, topic]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Sanitize content
    cleaned_content = sanitize_input(content)
    if not cleaned_content:
        return jsonify({'error': 'Invalid message content'}), 400
    
    # Create and save message
    message = Message(
        content=cleaned_content,
        sender_type=sender_type,
        topic=topic,
        session_id=session_id,
        complexity_score=data.get('complexity_score', 0.0),
        engagement_score=data.get('engagement_score', 0.0)
    )
    db.session.add(message)
    db.session.commit()
    
    # Generate AI response if message is from student
    if sender_type == SenderType.STUDENT.value:
        try:
            # Get context from previous messages
            context = Message.query.filter_by(session_id=session_id).order_by(Message.timestamp.desc()).limit(5).all()
            context_text = "\n".join([msg.content for msg in reversed(context)])
            
            # Generate AI response
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful educational AI assistant."},
                    {"role": "user", "content": f"Context:\n{context_text}\n\nStudent message: {cleaned_content}"}
                ]
            )
            
            # Save AI response
            ai_message = Message(
                content=response.choices[0].message.content,
                sender_type=SenderType.AI.value,
                topic=topic,
                session_id=session_id,
                complexity_score=0.7,  # Example scores
                engagement_score=0.8
            )
            db.session.add(ai_message)
            db.session.commit()
            
        except Exception as e:
            print(f"Error generating AI response: {e}")
            # Still return success for the student message
    
    return jsonify(message.to_dict())

@app.route('/api/profile/<student_id>', methods=['GET'])
def get_profile(student_id):
    """Get a student's learning profile"""
    profile = LearningProfile.query.get(student_id)
    if not profile:
        return jsonify({'message': 'Profile not found'}), 200
    return jsonify(profile.to_dict())

@app.route('/api/profile/<student_id>', methods=['PUT'])
def update_profile(student_id):
    """Create or update a student's learning profile"""
    data = request.get_json()
    
    profile = LearningProfile.query.get(student_id)
    if not profile:
        profile = LearningProfile(student_id=student_id)
    
    # Update profile fields
    for key, value in data.items():
        if hasattr(profile, key):
            setattr(profile, key, value)
    
    db.session.add(profile)
    db.session.commit()
    return jsonify(profile.to_dict())

@app.route('/api/analytics/topic/<topic>', methods=['GET'])
def topic_analytics(topic):
    """Get analytics for a specific topic"""
    messages = Message.query.filter_by(topic=topic).all()
    
    if not messages:
        return jsonify({
            'total_messages': 0,
            'avg_complexity': 0,
            'avg_engagement': 0
        })
    
    total = len(messages)
    avg_complexity = sum(msg.complexity_score for msg in messages) / total
    avg_engagement = sum(msg.engagement_score for msg in messages) / total
    
    return jsonify({
        'total_messages': total,
        'avg_complexity': avg_complexity,
        'avg_engagement': avg_engagement
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000) 