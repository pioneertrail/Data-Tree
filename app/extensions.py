"""Flask extensions."""
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy with naming convention
db = SQLAlchemy()

def init_db(app):
    """Initialize the database and create tables."""
    with app.app_context():
        # Import models here to avoid circular imports
        from app.models import Teacher, User, Group, Interaction, SubjectProgress, LessonPlan, Suggestion
        
        # Drop all tables and recreate them
        db.drop_all()
        db.create_all()
        
        # Create default teacher
        default_teacher = Teacher(
            name='Ms. Emma',
            specialty='General Education'
        )
        db.session.add(default_teacher)
        db.session.commit() 