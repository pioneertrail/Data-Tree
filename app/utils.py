from functools import wraps
from flask import request, jsonify
import bleach
from enum import Enum
from datetime import datetime, timedelta
from app.models import LearningStyle
import re

class LearningStyle(Enum):
    VISUAL = 'visual'
    AUDITORY = 'auditory'
    KINESTHETIC = 'kinesthetic'
    READING_WRITING = 'reading_writing'

def validate_learning_style(style):
    """Validate and convert learning style string to enum."""
    try:
        return LearningStyle(style.lower())
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid learning style. Must be one of: {', '.join(s.value for s in LearningStyle)}")

def calculate_analytics(text):
    """Calculate analytics for a message."""
    if not text:
        return {'complexity_score': 0.0, 'engagement_score': 0.0}
    
    # Simple complexity score based on average word length and sentence length
    words = text.split()
    sentences = re.split(r'[.!?]+', text)
    
    if not words or not sentences:
        return {'complexity_score': 0.0, 'engagement_score': 0.0}
    
    avg_word_length = sum(len(word) for word in words) / len(words)
    avg_sentence_length = len(words) / len(sentences)
    
    # Normalize scores between 0 and 1
    complexity_score = min((avg_word_length / 10 + avg_sentence_length / 20) / 2, 1.0)
    
    # Simple engagement score based on question marks, exclamation points, and keywords
    engagement_markers = len(re.findall(r'[?!]', text))
    engagement_keywords = len(re.findall(r'\b(interesting|great|amazing|why|how|what|tell|explain)\b', text.lower()))
    
    engagement_score = min((engagement_markers / 5 + engagement_keywords / 10) / 2, 1.0)
    
    return {
        'complexity_score': complexity_score,
        'engagement_score': engagement_score
    }

def rate_limit(max_requests=100, window=timedelta(minutes=1)):
    """Rate limiting decorator."""
    def decorator(f):
        # Store request timestamps for each client
        requests = {}
        
        @wraps(f)
        def wrapped(*args, **kwargs):
            now = datetime.utcnow()
            client_ip = request.remote_addr
            
            # Get list of requests for this client
            client_requests = requests.get(client_ip, [])
            
            # Remove old requests outside the window
            client_requests = [ts for ts in client_requests if now - ts < window]
            
            if len(client_requests) >= max_requests:
                return jsonify({'error': 'Rate limit exceeded'}), 429
                
            client_requests.append(now)
            requests[client_ip] = client_requests
            
            return f(*args, **kwargs)
        return wrapped
    return decorator

def validate_session_id(session_id):
    """Validate session ID format."""
    if not session_id or not isinstance(session_id, str):
        return False
    return len(session_id) == 32 and session_id.isalnum()

def sanitize_input(text):
    """Sanitize user input to prevent XSS attacks."""
    return bleach.clean(text, strip=True)
