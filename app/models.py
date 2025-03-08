"""Database models for the AI Educational Assistant."""
from datetime import datetime
from enum import Enum
import json
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.extensions import db

class SenderType(Enum):
    STUDENT = 'STUDENT'
    AI = 'AI'

class TopicArea(str, Enum):
    SCIENCE = 'science'
    MATH = 'math'
    HISTORY = 'history'
    LITERATURE = 'literature'
    ART = 'art'
    MUSIC = 'music'
    TECHNOLOGY = 'technology'

class SubjectArea(Enum):
    MATH = 'MATH'
    SCIENCE = 'SCIENCE'
    ENGLISH = 'ENGLISH'
    HISTORY = 'HISTORY'
    LANGUAGE = 'LANGUAGE'
    OTHER = 'OTHER'

class InteractionType(Enum):
    QUESTION = 'question'
    LESSON = 'lesson'
    AHA = 'aha'
    ONBOARDING = 'onboarding'
    GROUP = 'group'

class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_type = db.Column(db.String(50), nullable=False)
    response_time = db.Column(db.Integer, nullable=False)  # in milliseconds
    memory_usage = db.Column(db.Integer, nullable=False)   # in MB
    ops_per_sec = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'test_type': self.test_type,
            'response_time': self.response_time,
            'memory_usage': self.memory_usage,
            'ops_per_sec': self.ops_per_sec,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }

class Message(db.Model):
    """Message model for chat interactions."""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    topic_area = db.Column(db.String(50), nullable=False)
    session_id = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_ai = db.Column(db.Boolean, default=False)
    complexity_score = db.Column(db.Float)
    engagement_score = db.Column(db.Float)
    
    def __init__(self, content, topic_area, session_id, is_ai=False, complexity_score=None, engagement_score=None):
        self.content = content
        self.topic_area = topic_area
        self.session_id = session_id
        self.is_ai = is_ai
        self.complexity_score = complexity_score
        self.engagement_score = engagement_score
        self.timestamp = datetime.utcnow()
    
    def to_dict(self):
        """Convert message to dictionary."""
        return {
            'id': self.id,
            'content': self.content,
            'topic_area': self.topic_area,
            'session_id': self.session_id,
            'timestamp': self.timestamp.isoformat(),
            'is_ai': self.is_ai,
            'complexity_score': self.complexity_score,
            'engagement_score': self.engagement_score
        }

    def __repr__(self):
        return f'<Message {self.id}: {self.sender_type} - {self.topic_area}>'

class LearningProfile(db.Model):
    """Learning profile model for storing student preferences and metrics."""
    __tablename__ = 'learning_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False)
    preferred_topics = db.Column(JSON, default=list)
    learning_style = db.Column(db.String(50))
    pace = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Analytics fields
    question_frequency = db.Column(db.Float, default=0.0)
    topics_mastered = db.Column(db.Integer, default=0)
    total_sessions = db.Column(db.Integer, default=0)
    last_active = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    avg_complexity = db.Column(db.Float, default=0.0)
    avg_engagement = db.Column(db.Float, default=0.0)
    
    def __init__(self, student_id, preferred_topics=None):
        self.student_id = student_id
        self.preferred_topics = preferred_topics or []
        if not self.created_at:
            self.created_at = datetime.utcnow()
        if not self.updated_at:
            self.updated_at = datetime.utcnow()
        if not self.last_active:
            self.last_active = datetime.utcnow()
    
    def to_dict(self):
        """Convert profile to dictionary."""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'preferred_topics': json.loads(self.preferred_topics) if self.preferred_topics else [],
            'learning_style': self.learning_style,
            'pace': self.pace,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'question_frequency': self.question_frequency,
            'topics_mastered': self.topics_mastered,
            'total_sessions': self.total_sessions,
            'last_active': self.last_active.isoformat(),
            'avg_complexity': self.avg_complexity,
            'avg_engagement': self.avg_engagement
        }

    def __repr__(self):
        return f'<LearningProfile {self.student_id}>'

class Teacher(db.Model):
    """Teacher model for managing multiple AI teachers."""
    __tablename__ = 'teachers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    specialty = db.Column(db.String(100))

    # Relationships
    groups = db.relationship('Group', backref='teacher', lazy=True)
    lesson_plans = db.relationship('LessonPlan', backref='teacher', lazy=True)
    suggestions = db.relationship('Suggestion', backref='teacher', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'specialty': self.specialty
        }

class User(db.Model):
    """User model for students."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    interactions = db.relationship('Interaction', backref='user', lazy=True)
    progress = db.relationship('SubjectProgress', backref='user', lazy=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Interaction(db.Model):
    """Model for tracking all interactions including 'aha moments'."""
    __tablename__ = 'interactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    topic_area = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'content': self.content,
            'response': self.response,
            'topic_area': self.topic_area,
            'created_at': self.created_at.isoformat()
        }

class SubjectProgress(db.Model):
    """Model for tracking student progress in each subject."""
    __tablename__ = 'subject_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    level = db.Column(db.Integer, default=1)
    progress = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'subject': self.subject,
            'level': self.level,
            'progress': self.progress,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class LessonPlan(db.Model):
    """Model for managing lesson plans."""
    __tablename__ = 'lesson_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    subject = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'teacher_id': self.teacher_id,
            'title': self.title,
            'content': self.content,
            'subject': self.subject,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Group(db.Model):
    """Model for managing group activities."""
    __tablename__ = 'groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='group', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'teacher_id': self.teacher_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Suggestion(db.Model):
    """Model for AI-generated system improvement suggestions."""
    __tablename__ = 'suggestions'
    
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    implemented = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'teacher_id': self.teacher_id,
            'content': self.content,
            'implemented': self.implemented,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class LearningStyle(str, Enum):
    VISUAL = 'visual'
    AUDITORY = 'auditory'
    KINESTHETIC = 'kinesthetic'
    READING_WRITING = 'reading_writing'

class Profile(db.Model):
    """Student profile model."""
    __tablename__ = 'profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    learning_style = db.Column(db.String(50), nullable=False)
    interests = db.Column(db.Text)
    grade_level = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, name, learning_style, interests=None, grade_level=None):
        self.name = name
        self.learning_style = learning_style
        self.interests = interests
        self.grade_level = grade_level
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        """Convert profile to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'learning_style': self.learning_style,
            'interests': self.interests,
            'grade_level': self.grade_level,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Session(db.Model):
    """Model for chat sessions."""
    id = db.Column(db.String(36), primary_key=True)
    student_id = db.Column(db.String(36), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.String(20), default='active')  # active, completed, archived 