"""Chat routes for message handling."""
from flask import Blueprint, request, jsonify
from ..models import db, Message, TopicArea

# Create blueprint
bp = Blueprint('chat', __name__, url_prefix='/api/chat')

@bp.route('/<session_id>', methods=['GET'])
def get_messages(session_id):
    """Get all messages for a session."""
    messages = Message.query.filter_by(session_id=session_id).order_by(Message.timestamp).all()
    return jsonify([msg.to_dict() for msg in messages])

@bp.route('/<session_id>', methods=['POST'])
def post_message(session_id):
    """Post a new message to the chat."""
    data = request.get_json()
    
    if not data or 'content' not in data or 'topic_area' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
        
    try:
        # Validate topic area
        if data['topic_area'] not in [topic.value for topic in TopicArea]:
            return jsonify({'error': 'Invalid topic area'}), 400
            
        # Create and save the user message
        message = Message(
            content=data['content'],
            topic_area=data['topic_area'],
            session_id=session_id,
            is_ai=data.get('is_ai', False)
        )
        db.session.add(message)
        db.session.commit()
        
        return jsonify(message.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Export the blueprint directly
__all__ = ['bp'] 