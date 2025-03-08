"""AI routes for generating responses and managing context.

This module provides the API endpoints for AI-powered educational interactions,
including response generation, lesson planning, and group activity creation.
"""
from flask import Blueprint, request, jsonify, current_app
from app.extensions import db
from app.models import User, Teacher
import openai
import os
import logging

# Create blueprint
bp = Blueprint('ai', __name__)
logger = logging.getLogger(__name__)

# Configure OpenAI
openai.api_key = os.environ.get('OPENAI_API_KEY')

@bp.route('/api/ai/generate', methods=['POST'])
def generate_response():
    """Generate an AI response with analytics.
    
    This endpoint accepts a question and topic area, then generates an educational
    response using OpenAI's GPT-3.5 model. It also provides analytics about the
    response's complexity, engagement level, and topic relevance.
    
    Request Body:
        {
            "content": str,       # The user's question
            "topic_area": str     # The subject area (e.g., "science", "math")
        }
    
    Returns:
        JSON response with the following structure:
        {
            "content": str,       # The AI-generated response
            "analytics": {
                "complexity_score": float,    # 0.0 to 1.0
                "engagement_score": float,    # 0.0 to 1.0
                "topic_relevance": float      # 0.0 to 1.0
            }
        }
        
    Raises:
        400 - Missing required fields
        500 - Internal server error or OpenAI API error
    """
    try:
        data = request.get_json()
        content = data.get('content')
        subject = data.get('topic_area')  # Using topic_area from frontend
        
        if not content or not subject:
            return jsonify({
                'error': 'Missing required fields: content and topic_area'
            }), 400
            
        # Get or create default teacher (Ms. Emma)
        teacher = Teacher.query.filter_by(name='Ms. Emma').first()
        if not teacher:
            teacher = Teacher(name='Ms. Emma', specialty='General Education')
            db.session.add(teacher)
            db.session.commit()
            
        # Get or create user (temporary user for web interface)
        user = User.query.filter_by(username='Web User').first()
        if not user:
            user = User(
                username='Web User',
                email='web.user@example.com'
            )
            db.session.add(user)
            db.session.commit()
            
        # Generate response using OpenAI
        system_prompt = f"""You are Ms. Emma, an expert teacher specialized in {subject}. 
        Your goal is to provide clear, engaging, and educational responses that help students understand complex topics.
        Adapt your explanation style based on the question's complexity and maintain an encouraging, supportive tone."""
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        ai_response = response.choices[0].message['content']
        
        # Calculate analytics based on the response
        complexity_score = min(len(ai_response.split()) / 200, 1.0)  # Simple complexity measure based on length
        engagement_score = 0.8  # Default engagement score
        topic_relevance = 0.9  # Default topic relevance
        
        return jsonify({
            'content': ai_response,
            'analytics': {
                'complexity_score': complexity_score,
                'engagement_score': engagement_score,
                'topic_relevance': topic_relevance
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/ai/lesson-plan', methods=['POST'])
def create_lesson_plan():
    """Create a personalized lesson plan.
    
    This endpoint generates a customized lesson plan based on the user's profile
    and the specified subject area.
    
    Request Body:
        {
            "user_id": str,    # The ID of the user
            "subject": str     # The subject area for the lesson
        }
    
    Returns:
        JSON response containing the lesson plan details
        
    Raises:
        400 - Missing required fields
        500 - Internal server error
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        subject = data.get('subject')
        
        if not user_id or not subject:
            return jsonify({
                'error': 'Missing required fields: user_id and subject'
            }), 400
            
        teacher = Teacher.query.filter_by(name='Ms. Emma').first()
        ai_teacher = AITeacher(teacher.teacher_id)
        
        plan = ai_teacher.create_lesson_plan(user_id, subject)
        return jsonify(plan)
        
    except Exception as e:
        logger.error(f"Error creating lesson plan: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/ai/group-activity', methods=['POST'])
def create_group_activity():
    """Create a collaborative learning activity.
    
    This endpoint generates a group activity that promotes collaborative learning
    among multiple students in a specific subject area.
    
    Request Body:
        {
            "user_ids": list[str],   # List of user IDs for the group
            "subject": str           # The subject area for the activity
        }
    
    Returns:
        JSON response containing the group activity details
        
    Raises:
        400 - Missing required fields
        500 - Internal server error
    """
    try:
        data = request.get_json()
        user_ids = data.get('user_ids')
        subject = data.get('subject')
        
        if not user_ids or not subject:
            return jsonify({
                'error': 'Missing required fields: user_ids and subject'
            }), 400
            
        teacher = Teacher.query.filter_by(name='Ms. Emma').first()
        ai_teacher = AITeacher(teacher.teacher_id)
        
        activity = ai_teacher.create_group_activity(user_ids, subject)
        return jsonify(activity)
        
    except Exception as e:
        logger.error(f"Error creating group activity: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Export the blueprint directly
__all__ = ['bp'] 