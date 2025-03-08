"""Profile routes for managing student profiles."""
from flask import Blueprint, request, jsonify
from ..models import db, Profile, LearningStyle

# Create blueprint
bp = Blueprint('profiles', __name__, url_prefix='/api/profiles')

@bp.route('/<student_id>', methods=['GET'])
def get_profile(student_id):
    """Get a student's profile."""
    profile = Profile.query.get(student_id)
    if not profile:
        return jsonify({'error': 'Profile not found'}), 404
    return jsonify(profile.to_dict()), 200

@bp.route('/<student_id>', methods=['PUT'])
def update_profile(student_id):
    """Create or update a student's profile."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
        
    try:
        profile = Profile.query.get(student_id)
        if not profile:
            profile = Profile(student_id=student_id)
            
        # Update profile fields
        if 'learning_style' in data:
            if data['learning_style'] not in [style.value for style in LearningStyle]:
                return jsonify({'error': 'Invalid learning style'}), 400
            profile.learning_style = data['learning_style']
        if 'topic_preferences' in data:
            profile.topic_preferences = data['topic_preferences']
        if 'topic_mastery' in data:
            profile.topic_mastery = data['topic_mastery']
        if 'interaction_history' in data:
            profile.interaction_history = data['interaction_history']
            
        db.session.add(profile)
        db.session.commit()
        
        return jsonify(profile.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Export the blueprint directly
__all__ = ['bp']