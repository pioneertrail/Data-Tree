"""AI routes for generating responses and managing context."""
from flask import Blueprint, request, jsonify, current_app
from app.extensions import db
from app.models import Message, TopicArea
from datetime import datetime
import uuid
import logging
import openai
from os import getenv
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create blueprint
bp = Blueprint('ai', __name__)
logger = logging.getLogger(__name__)

# Configure OpenAI
openai.api_key = getenv('OPENAI_API_KEY')

def generate_ai_response(content, topic_area):
    """Generate an AI response using OpenAI's API."""
    try:
        # Create a system message that sets the context for the AI
        system_message = f"You are an educational AI assistant specializing in {topic_area}. Provide detailed, accurate, and engaging responses that are appropriate for students learning about {topic_area}."
        
        # Create the conversation messages
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": content}
        ]
        
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        # Extract the AI's response
        ai_content = response.choices[0].message['content']
        
        # Calculate scores based on response characteristics
        complexity_score = min(len(ai_content.split()) / 200, 1.0)  # Based on response length
        engagement_score = 0.9  # Default high engagement for GPT responses
        topic_relevance = 0.95  # Default high relevance
        
        return {
            'content': ai_content,
            'complexity_score': complexity_score,
            'engagement_score': engagement_score,
            'topic_relevance': topic_relevance
        }
        
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {str(e)}")
        raise

@bp.route('/generate', methods=['POST'])
@bp.route('/generate/<session_id>', methods=['POST'])
def generate_response(session_id=None):
    """Generate an AI response for a message."""
    try:
        data = request.get_json()
        if not data or 'content' not in data or 'topic_area' not in data:
            return jsonify({'error': 'Missing required fields'}), 400

        # Validate topic area
        topic_area = data['topic_area']
        if topic_area not in [area.value for area in TopicArea]:
            return jsonify({'error': 'Invalid topic area'}), 400

        # Generate session_id if not provided
        if session_id is None:
            session_id = data.get('session_id', str(uuid.uuid4()))

        # Generate AI response
        ai_response = generate_ai_response(data['content'], topic_area)

        # Create and save message
        message = Message(
            content=ai_response['content'],
            topic_area=topic_area,
            session_id=session_id,
            is_ai=True,
            complexity_score=ai_response['complexity_score'],
            engagement_score=ai_response['engagement_score']
        )
        
        db.session.add(message)
        db.session.commit()

        return jsonify({
            'content': ai_response['content'],
            'topic_area': topic_area,
            'analytics': {
                'complexity_score': ai_response['complexity_score'],
                'engagement_score': ai_response['engagement_score'],
                'topic_relevance': ai_response['topic_relevance']
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error generating response: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/context', methods=['GET'])
@bp.route('/context/<session_id>', methods=['GET'])
def get_context(session_id=None):
    """Get the conversation context for a session."""
    try:
        if session_id is None:
            # Return empty list if no session_id provided
            return jsonify([]), 200

        messages = Message.query.filter_by(session_id=session_id).order_by(Message.timestamp).all()
        return jsonify([{
            'content': msg.content,
            'topic_area': msg.topic_area,
            'timestamp': msg.timestamp.isoformat(),
            'is_ai': msg.is_ai,
            'metrics': {
                'complexity': msg.complexity_score,
                'engagement': msg.engagement_score
            } if msg.is_ai else None
        } for msg in messages]), 200

    except Exception as e:
        logger.error(f"Error retrieving context: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Export the blueprint directly
__all__ = ['bp'] 