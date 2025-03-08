"""Analytics routes for data analysis."""
from flask import Blueprint, request, jsonify
from sqlalchemy import func
from ..models import db, Message, TopicArea

# Create blueprint
bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

@bp.route('/topic/<session_id>', methods=['GET'])
def get_topic_analytics(session_id):
    """Get analytics for topics in a session."""
    topic = request.args.get('topic')
    
    # Base query for messages in the session
    query = Message.query.filter_by(session_id=session_id)
    
    # Filter by topic if specified
    if topic:
        if topic not in [t.value for t in TopicArea]:
            return jsonify({'error': 'Invalid topic'}), 400
        query = query.filter_by(topic_area=topic)
    
    # Get all messages
    messages = query.all()
    
    if not messages:
        return jsonify({'message': 'No messages found for analysis'}), 404
    
    # Analyze messages
    analytics = {
        'total_messages': len(messages),
        'topics': {},
        'average_length': sum(len(msg.content) for msg in messages) / len(messages)
    }
    
    # Analyze by topic
    for msg in messages:
        topic = msg.topic_area.value
        if topic not in analytics['topics']:
            analytics['topics'][topic] = {'count': 0, 'total_length': 0}
        analytics['topics'][topic]['count'] += 1
        analytics['topics'][topic]['total_length'] += len(msg.content)
        analytics['topics'][topic]['average_length'] = (
            analytics['topics'][topic]['total_length'] / analytics['topics'][topic]['count']
        )
    
    return jsonify(analytics), 200

@bp.route('/messages/<session_id>', methods=['GET'])
def get_message_analytics(session_id):
    """Get analytics for messages in a session."""
    messages = Message.query.filter_by(session_id=session_id).all()
    
    if not messages:
        return jsonify({'error': 'No messages found'}), 404
        
    analytics = {
        'complexity_score': sum(m.complexity_score or 0 for m in messages) / len(messages),
        'engagement_score': sum(m.engagement_score or 0 for m in messages) / len(messages),
        'total_messages': len(messages)
    }
    
    return jsonify(analytics)

# Export the blueprint directly
__all__ = ['bp'] 