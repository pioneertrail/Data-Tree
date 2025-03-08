from flask import Blueprint, jsonify, request, abort, make_response, current_app
from .models import (
    db, User, Teacher, Interaction, SubjectProgress, LessonPlan,
    Group, Suggestion, InteractionType, SubjectArea, Message, LearningProfile, Profile, Session, TopicArea
)
from .enums import SenderType, LearningStyle
from .ai_service import (
    detect_aha_moment, generate_personalized_response,
    create_interaction, update_subject_progress, generate_parent_report,
    generate_response, analyze_learning_style
)
from .utils import rate_limit, validate_session_id, sanitize_input, validate_learning_style, calculate_analytics
from datetime import datetime, timedelta
from collections import defaultdict
import time
import re
from functools import wraps
import html
import werkzeug
import logging
import bleach
import json
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, func

# Rate limiting configuration
message_timestamps = defaultdict(list)
RATE_LIMIT = 30  # messages per minute
RATE_WINDOW = 60  # seconds

def check_rate_limit(session_id):
    """Check if the session has exceeded the rate limit."""
    now = time.time()
    timestamps = message_timestamps[session_id]
    
    # Remove timestamps older than the window
    while timestamps and timestamps[0] < now - RATE_WINDOW:
        timestamps.pop(0)
    
    # Check if we've exceeded the rate limit
    if len(timestamps) >= RATE_LIMIT:
        return True
        
    # Add current timestamp
    timestamps.append(now)
    return False

bp = Blueprint('main', __name__)

# Create blueprints with API prefixes
chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')
profile_bp = Blueprint('profile', __name__, url_prefix='/api/profile')
analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')
teacher_bp = Blueprint('teacher', __name__, url_prefix='/api/teacher')
student_bp = Blueprint('student', __name__, url_prefix='/api/student')
interaction_bp = Blueprint('interaction', __name__, url_prefix='/api/interaction')
progress_bp = Blueprint('progress', __name__, url_prefix='/api/progress')
group_bp = Blueprint('group', __name__, url_prefix='/api/group')

def validate_session_id_decorator(f):
    """Decorator to validate session ID."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_id = kwargs.get('session_id')
        if not session_id or not isinstance(session_id, str):
            return jsonify({'error': 'Invalid session ID'}), 400
            
        if len(session_id) > 50:
            return jsonify({'error': 'Session ID too long'}), 400
            
        if not re.match(r'^[a-zA-Z0-9_-]+$', session_id):
            return jsonify({'error': 'Invalid session ID format'}), 400
            
        if ';' in session_id or '../' in session_id or '<' in session_id:
            return jsonify({'error': 'Invalid session ID'}), 400
            
        # Check rate limit
        if check_rate_limit(session_id):
            return jsonify({'error': 'Rate limit exceeded'}), 429
            
        return f(*args, **kwargs)
    return decorated_function

def validate_json_request():
    """Validate that the request has JSON content."""
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 415
    if not request.get_json(silent=True):
        return jsonify({'error': 'Request body must be valid JSON'}), 400
    return None

def validate_message_data(data):
    """Validate message data."""
    required_fields = ['content', 'sender_type', 'topic_area']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    if len(data['content']) > 5000:
        return jsonify({'error': 'Message content must be less than 5000 characters'}), 400
    
    try:
        SenderType(data['sender_type'])
    except ValueError:
        return jsonify({'error': f'Invalid sender type. Must be one of: {", ".join(t.value for t in SenderType)}'}), 400
    
    try:
        TopicArea(data['topic_area'])
    except ValueError:
        return jsonify({'error': f'Invalid topic area. Must be one of: {", ".join(t.value for t in TopicArea)}'}), 400
    
    return None

def validate_teacher(teacher_id):
    """Validate teacher exists."""
    teacher = Teacher.query.get(teacher_id)
    if not teacher:
        return jsonify({'error': 'Teacher not found'}), 404
    return teacher

def validate_student(student_id):
    """Validate student exists."""
    student = User.query.get(student_id)
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    return student

def validate_subject(subject):
    """Validate subject area."""
    try:
        return SubjectArea(subject)
    except ValueError:
        return jsonify({'error': f'Invalid subject. Must be one of: {", ".join(s.value for s in SubjectArea)}'}), 400

@bp.route('/')
def index():
    """Landing page."""
    return jsonify({"message": "Welcome to the Educational Chat System"})

@chat_bp.route('/chat/<session_id>', methods=['GET'])
async def get_chat_history(session_id):
    try:
        stmt = select(Message).filter_by(session_id=session_id).order_by(Message.timestamp)
        result = await db.session.execute(stmt)
        messages = result.scalars().all()
        return jsonify([msg.to_dict() for msg in messages]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chat_bp.route('/chat/<session_id>', methods=['POST'])
async def send_message(session_id):
    try:
        data = request.get_json()
        if not data or 'content' not in data or 'topic_area' not in data:
            return jsonify({'error': 'Missing required fields'}), 400

        # Validate and sanitize input
        content = sanitize_input(data['content'])
        try:
            topic_area = TopicArea(data['topic_area'])
        except ValueError:
            return jsonify({'error': 'Invalid topic area'}), 400

        # Create user message
        message = Message(
            session_id=session_id,
            content=content,
            is_ai=False,
            topic_area=topic_area
        )
        
        # Calculate analytics
        analytics = calculate_analytics(content)
        message.complexity_score = analytics.get('complexity_score')
        message.engagement_score = analytics.get('engagement_score')
        
        db.session.add(message)
        await db.session.commit()

        # Generate AI response
        ai_response = "This is a placeholder AI response"  # Replace with actual AI response generation
        ai_message = Message(
            session_id=session_id,
            content=ai_response,
            is_ai=True,
            topic_area=topic_area
        )
        
        # Calculate analytics for AI response
        ai_analytics = calculate_analytics(ai_response)
        ai_message.complexity_score = ai_analytics.get('complexity_score')
        ai_message.engagement_score = ai_analytics.get('engagement_score')
        
        db.session.add(ai_message)
        await db.session.commit()

        return jsonify({
            'user_message': message.to_dict(),
            'ai_response': ai_message.to_dict()
        }), 201
    except Exception as e:
        await db.session.rollback()
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/profile/<student_id>', methods=['GET'])
async def get_profile(student_id):
    try:
        stmt = select(Profile).filter_by(student_id=student_id)
        result = await db.session.execute(stmt)
        profile = result.scalar_one_or_none()
        
        if not profile:
            return jsonify({'error': 'Profile not found'}), 404
            
        return jsonify(profile.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/profile/<student_id>', methods=['PUT'])
async def update_profile(student_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        stmt = select(Profile).filter_by(student_id=student_id)
        result = await db.session.execute(stmt)
        profile = result.scalar_one_or_none()

        if not profile:
            profile = Profile(student_id=student_id)
            db.session.add(profile)

        # Update learning style if provided
        if 'learning_style' in data:
            try:
                learning_style = validate_learning_style(data['learning_style'])
                profile.learning_style = learning_style
            except ValueError as e:
                return jsonify({'error': str(e)}), 400

        # Update other fields if provided
        if 'topic_preferences' in data:
            profile.topic_preferences = data['topic_preferences']
        if 'topic_mastery' in data:
            profile.topic_mastery = data['topic_mastery']
        if 'interaction_history' in data:
            profile.interaction_history = data['interaction_history']

        await db.session.commit()
        return jsonify(profile.to_dict()), 200
    except Exception as e:
        await db.session.rollback()
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/', methods=['POST'])
async def create_profile():
    data = request.get_json()
    
    if not data or 'student_id' not in data:
        return jsonify({'error': 'Student ID is required'}), 400
        
    try:
        existing = await db.session.execute(
            db.select(Profile).filter_by(student_id=data['student_id'])
        )
        if existing.scalar():
            return jsonify({'error': 'Profile already exists'}), 409
            
        if 'learning_style' in data and not validate_learning_style(data['learning_style']):
            return jsonify({'error': 'Invalid learning style'}), 400
            
        profile = Profile(
            student_id=data['student_id'],
            learning_style=data.get('learning_style'),
            preferences=data.get('preferences', {})
        )
        
        db.session.add(profile)
        await db.session.commit()
        return jsonify(profile.to_dict()), 201
    except SQLAlchemyError as e:
        await db.session.rollback()
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/profile/<student_id>/metrics', methods=['GET'])
def get_profile_metrics(student_id):
    """Get profile metrics."""
    try:
        profile = LearningProfile.query.filter_by(student_id=student_id).first()
        if not profile:
            return jsonify({'message': 'Profile not found'}), 404
            
        # Calculate metrics
        messages = Message.query.filter_by(sender_id=student_id).all()
        if not messages:
            return jsonify({'message': 'No data available'}), 404
            
        # Calculate average complexity and engagement
        avg_complexity = sum(msg.analytics.get('complexity_score', 0) for msg in messages) / len(messages)
        avg_engagement = sum(msg.analytics.get('engagement_score', 0) for msg in messages) / len(messages)
        
        # Count topics mastered (topics with high engagement and complexity)
        topics_mastered = sum(1 for topic in profile.preferred_topics 
                            if avg_complexity > 0.7 and avg_engagement > 0.7)
        
        # Detect learning style based on interaction patterns
        learning_style = profile.learning_style
        if avg_engagement > 0.8:
            if any('visual' in msg.content.lower() for msg in messages):
                learning_style = 'visual'
            elif any('audio' in msg.content.lower() for msg in messages):
                learning_style = 'auditory'
                
        return jsonify({
            'avg_complexity': avg_complexity,
            'avg_engagement': avg_engagement,
            'topics_mastered': topics_mastered,
            'learning_style': learning_style
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error calculating metrics: {str(e)}")
        return jsonify({'message': 'Failed to calculate metrics'}), 500

@analytics_bp.route('/analytics/topic/<topic>', methods=['GET'])
async def topic_analytics(topic):
    try:
        topic_area = TopicArea(topic)
        stmt = select(Message).filter_by(topic_area=topic_area)
        result = await db.session.execute(stmt)
        messages = result.scalars().all()

        if not messages:
            return jsonify({'error': 'No messages found for this topic'}), 404

        # Calculate analytics
        total_messages = len(messages)
        avg_complexity = sum(m.complexity_score or 0 for m in messages) / total_messages
        avg_engagement = sum(m.engagement_score or 0 for m in messages) / total_messages

        # Create timeline of messages
        timeline = [
            {
                'timestamp': msg.timestamp.isoformat(),
                'complexity': msg.complexity_score,
                'engagement': msg.engagement_score,
                'is_ai': msg.is_ai
            }
            for msg in sorted(messages, key=lambda x: x.timestamp)
        ]

        return jsonify({
            'topic': topic,
            'total_messages': total_messages,
            'average_complexity': avg_complexity,
            'average_engagement': avg_engagement,
            'timeline': timeline
        }), 200
    except ValueError:
        return jsonify({'error': 'Invalid topic area'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/analytics/aggregate', methods=['GET'])
async def aggregate_analytics():
    try:
        # Get total messages and sessions
        msg_count = await db.session.execute(select(func.count(Message.id)))
        total_messages = msg_count.scalar()
        
        session_count = await db.session.execute(
            select(func.count(func.distinct(Message.session_id)))
        )
        total_sessions = session_count.scalar()

        # Get analytics by topic
        topic_stats = {}
        for topic in TopicArea:
            stmt = select(Message).filter_by(topic_area=topic)
            result = await db.session.execute(stmt)
            messages = result.scalars().all()
            
            if messages:
                topic_stats[topic.value] = {
                    'message_count': len(messages),
                    'avg_complexity': sum(m.complexity_score or 0 for m in messages) / len(messages),
                    'avg_engagement': sum(m.engagement_score or 0 for m in messages) / len(messages)
                }

        return jsonify({
            'total_messages': total_messages,
            'total_sessions': total_sessions,
            'topic_statistics': topic_stats
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Teacher routes
@teacher_bp.route('/', methods=['POST'])
def create_teacher():
    """Create a new teacher."""
    data = request.get_json()
    if not data or 'name' not in data:
        abort(400, description='Name is required')
    
    teacher = Teacher(
        name=data['name'],
        specialty=data.get('specialty')
    )
    db.session.add(teacher)
    db.session.commit()
    return jsonify(teacher.to_dict()), 201

@teacher_bp.route('/<int:teacher_id>/students', methods=['GET'])
def get_teacher_students(teacher_id):
    """Get all students for a teacher."""
    teacher = validate_teacher(teacher_id)
    return jsonify([student.to_dict() for student in teacher.students]), 200

# Student routes
@student_bp.route('/', methods=['POST'])
def create_student():
    """Create a new student."""
    data = request.get_json()
    if not data or 'name' not in data:
        abort(400, description='Name is required')
    
    student = User(
        name=data['name'],
        email=data.get('email'),
        age=data.get('age'),
        sex=data.get('sex'),
        location=data.get('location'),
        religion=data.get('religion'),
        learning_style=data.get('learning_style'),
        language=data.get('language'),
        disabilities=data.get('disabilities'),
        teacher_id=data.get('teacher_id')
    )
    db.session.add(student)
    db.session.commit()
    return jsonify(student.to_dict()), 201

@student_bp.route('/<int:student_id>', methods=['GET'])
def get_student(student_id):
    """Get student details."""
    student = validate_student(student_id)
    return jsonify(student.to_dict()), 200

# Interaction routes
@interaction_bp.route('/', methods=['POST'])
@rate_limit
def create_interaction():
    """Create a new interaction."""
    data = request.get_json()
    if not data or not all(k in data for k in ['student_id', 'teacher_id', 'content', 'subject']):
        abort(400, description='Missing required fields')
    
    student = validate_student(data['student_id'])
    teacher = validate_teacher(data['teacher_id'])
    subject = validate_subject(data['subject'])
    
    # Get previous interactions for context
    previous = Interaction.query.filter_by(
        user_id=student.id
    ).order_by(
        Interaction.timestamp.desc()
    ).limit(5).all()
    
    # Detect if this is an "aha moment"
    aha_confidence, aha_trigger = detect_aha_moment(data['content'], previous)
    
    # Create student's interaction
    interaction = create_interaction(
        user_id=student.id,
        teacher_id=teacher.id,
        content=bleach.clean(data['content']),
        interaction_type=InteractionType.QUESTION.value,
        subject=subject.value,
        is_private=data.get('is_private', False),
        aha_trigger=aha_trigger,
        aha_confidence=aha_confidence
    )
    db.session.add(interaction)
    
    # Generate AI response
    try:
        response_content, tokens = generate_personalized_response(
            user=student,
            content=data['content'],
            subject=subject.value,
            previous_interactions=previous
        )
        
        # Create AI's response interaction
        ai_interaction = create_interaction(
            user_id=student.id,
            teacher_id=teacher.id,
            content=response_content,
            interaction_type=InteractionType.LESSON.value,
            subject=subject.value,
            is_private=data.get('is_private', False)
        )
        db.session.add(ai_interaction)
        
        # Update progress if this was an "aha moment"
        if aha_confidence > 0.7:
            progress = update_subject_progress(student.id, subject.value, aha_confidence)
            db.session.add(progress)
            
            # Increment student's aha count
            student.aha_count += 1
            
            # Create a suggestion if this was a strong "aha moment"
            if aha_confidence > 0.9:
                suggestion = Suggestion(
                    teacher_id=teacher.id,
                    content=f"Strong 'aha moment' detected using {aha_trigger}. Consider using similar approaches."
                )
                db.session.add(suggestion)
        
        db.session.commit()
        
        return jsonify({
            'student_interaction': interaction.to_dict(),
            'ai_response': ai_interaction.to_dict(),
            'aha_detected': aha_confidence > 0.7,
            'aha_confidence': aha_confidence
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in create_interaction: {str(e)}")
        abort(500, description='Error generating AI response')

@interaction_bp.route('/student/<int:student_id>', methods=['GET'])
def get_student_interactions(student_id):
    """Get all interactions for a student."""
    student = validate_student(student_id)
    interactions = Interaction.query.filter_by(
        user_id=student.id
    ).order_by(
        Interaction.timestamp.desc()
    ).all()
    return jsonify([i.to_dict() for i in interactions]), 200

# Progress routes
@progress_bp.route('/student/<int:student_id>', methods=['GET'])
def get_student_progress(student_id):
    """Get progress for all subjects for a student."""
    student = validate_student(student_id)
    progress = SubjectProgress.query.filter_by(user_id=student.id).all()
    return jsonify([p.to_dict() for p in progress]), 200

@progress_bp.route('/student/<int:student_id>/report', methods=['GET'])
def get_parent_report(student_id):
    """Generate a parent report for a student."""
    student = validate_student(student_id)
    date = request.args.get('date')
    if date:
        try:
            date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            abort(400, description='Invalid date format. Use YYYY-MM-DD')
    
    try:
        report = generate_parent_report(student.id, date)
        return jsonify({'report': report}), 200
    except Exception as e:
        current_app.logger.error(f"Error generating parent report: {str(e)}")
        abort(500, description='Error generating parent report')

# Group routes
@group_bp.route('/', methods=['POST'])
def create_group():
    """Create a new group for collaborative learning."""
    data = request.get_json()
    if not data or not all(k in data for k in ['user_ids', 'task', 'subject']):
        abort(400, description='Missing required fields')
    
    # Validate all users exist
    for user_id in data['user_ids']:
        validate_student(user_id)
    
    subject = validate_subject(data['subject'])
    
    group = Group(
        task=data['task'],
        subject=subject.value
    )
    group.set_user_ids(data['user_ids'])
    
    db.session.add(group)
    db.session.commit()
    
    return jsonify(group.to_dict()), 201

@group_bp.route('/<int:group_id>', methods=['GET'])
def get_group(group_id):
    """Get group details."""
    group = Group.query.get_or_404(group_id)
    return jsonify(group.to_dict()), 200

# Error handlers
@chat_bp.errorhandler(400)
@profile_bp.errorhandler(400)
@analytics_bp.errorhandler(400)
@teacher_bp.errorhandler(400)
@student_bp.errorhandler(400)
@interaction_bp.errorhandler(400)
@progress_bp.errorhandler(400)
@group_bp.errorhandler(400)
def bad_request(e):
    return jsonify({
        'error': 'Bad Request',
        'message': str(e.description)
    }), 400

@chat_bp.errorhandler(404)
@profile_bp.errorhandler(404)
@analytics_bp.errorhandler(404)
@teacher_bp.errorhandler(404)
@student_bp.errorhandler(404)
@interaction_bp.errorhandler(404)
@progress_bp.errorhandler(404)
@group_bp.errorhandler(404)
def not_found(e):
    return jsonify({
        'error': 'Not Found',
        'message': str(e.description)
    }), 404

@chat_bp.errorhandler(415)
@profile_bp.errorhandler(415)
@analytics_bp.errorhandler(415)
@teacher_bp.errorhandler(415)
@student_bp.errorhandler(415)
@interaction_bp.errorhandler(415)
@progress_bp.errorhandler(415)
@group_bp.errorhandler(415)
def unsupported_media_type(e):
    return jsonify({
        'error': 'Unsupported Media Type',
        'message': str(e.description)
    }), 415

@chat_bp.errorhandler(429)
@profile_bp.errorhandler(429)
@analytics_bp.errorhandler(429)
@teacher_bp.errorhandler(429)
@student_bp.errorhandler(429)
@interaction_bp.errorhandler(429)
@progress_bp.errorhandler(429)
@group_bp.errorhandler(429)
def too_many_requests(e):
    return jsonify({
        'error': 'Too Many Requests',
        'message': 'Rate limit exceeded'
    }), 429

@chat_bp.errorhandler(500)
@profile_bp.errorhandler(500)
@analytics_bp.errorhandler(500)
@teacher_bp.errorhandler(500)
@student_bp.errorhandler(500)
@interaction_bp.errorhandler(500)
@progress_bp.errorhandler(500)
@group_bp.errorhandler(500)
def internal_server_error(e):
    return jsonify({
        'error': 'Internal Server Error',
        'message': str(e.description)
    }), 500