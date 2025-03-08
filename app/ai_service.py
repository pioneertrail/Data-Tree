from flask import current_app
from openai import OpenAI
from .models import (
    Interaction, User, Teacher, SubjectProgress,
    InteractionType, SubjectArea
)
import os
import logging
import json
from datetime import datetime
from unittest.mock import MagicMock

# Initialize the OpenAI client with proper error handling and test mode support
def get_openai_client():
    if os.getenv('TESTING') == 'true':
        mock_client = MagicMock()
        mock_response = {
            'choices': [{
                'message': {
                    'content': 'This is a mock response for testing'
                }
            }]
        }
        mock_client.chat.completions.create.return_value = mock_response
        return mock_client
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
    
    return OpenAI(api_key=api_key)

client = get_openai_client()

def detect_aha_moment(content, previous_interactions):
    """
    Detect if the student has experienced an "aha moment" using NLP analysis.
    Returns a confidence score between 0 and 1.
    """
    try:
        # Analyze the current message for signs of sudden understanding
        messages = [
            {"role": "system", "content": "You are an AI that detects 'aha moments' in student responses. "
             "Look for signs of sudden understanding, excitement, or insight. "
             "Return a JSON with fields: confidence (0-1), trigger (what caused the insight)."},
            {"role": "user", "content": f"Analyze this student response for signs of an 'aha moment': {content}"}
        ]
        
        # Add context from previous interactions if available
        if previous_interactions:
            context = "\n".join([f"Previous: {inter.content}" for inter in previous_interactions[-3:]])
            messages.append({"role": "user", "content": f"Previous context:\n{context}"})
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.3,
            max_tokens=100
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get('confidence', 0.0), result.get('trigger', None)
        
    except Exception as e:
        logging.error(f"Error in aha moment detection: {str(e)}")
        return 0.0, None

def generate_personalized_response(user, content, subject, previous_interactions=None):
    """
    Generate a personalized response based on the user's profile and learning history.
    """
    try:
        # Build system message with user context
        system_message = {
            "role": "system",
            "content": f"You are Ms. Emma, an expert teacher specialized in {subject}. "
                      f"Student profile:\n"
                      f"- Age: {user.age or 'unknown'}\n"
                      f"- Learning style: {user.learning_style or 'unknown'}\n"
                      f"- Language: {user.language or 'English'}\n"
                      f"- Disabilities: {user.disabilities or 'none'}\n"
                      f"Adapt your response accordingly and aim to create 'aha moments'."
        }
        
        # Build conversation history
        messages = [system_message]
        if previous_interactions:
            for inter in previous_interactions[-5:]:  # Last 5 interactions
                role = "assistant" if inter.type == "AI" else "user"
                messages.append({"role": role, "content": inter.content})
        
        # Add current message
        messages.append({"role": "user", "content": content})
        
        # Generate response
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=300
        )
        
        return response.choices[0].message.content, response.usage.total_tokens
        
    except Exception as e:
        logging.error(f"Error generating personalized response: {str(e)}")
        raise

def create_interaction(user_id, teacher_id, content, interaction_type, subject,
                      is_private=False, aha_trigger=None, aha_confidence=None):
    """Create a new interaction record."""
    interaction = Interaction(
        user_id=user_id,
        teacher_id=teacher_id,
        content=content,
        type=interaction_type,
        subject=subject,
        is_private=is_private,
        aha_trigger=aha_trigger,
        aha_confidence=aha_confidence,
        timestamp=datetime.utcnow()
    )
    return interaction

def update_subject_progress(user_id, subject, aha_confidence):
    """Update the user's progress in a subject based on their interactions."""
    progress = SubjectProgress.query.filter_by(
        user_id=user_id,
        subject=subject
    ).first()
    
    if not progress:
        progress = SubjectProgress(user_id=user_id, subject=subject)
    
    # Update progress level based on aha moments
    if aha_confidence and aha_confidence > 0.8:
        # High confidence aha moment increases progress
        current_goals = json.loads(progress.goals_achieved) if progress.goals_achieved else []
        current_goals.append({
            'type': 'aha_moment',
            'confidence': aha_confidence,
            'timestamp': datetime.utcnow().isoformat()
        })
        progress.goals_achieved = json.dumps(current_goals)
    
    return progress

def generate_parent_report(user_id, date=None):
    """Generate a detailed report for parents."""
    try:
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
            
        # Get today's interactions if date not specified
        query = Interaction.query.filter_by(user_id=user_id)
        if date:
            query = query.filter(db.func.date(Interaction.timestamp) == date)
            
        interactions = query.order_by(Interaction.timestamp).all()
        
        # Group interactions by subject
        subjects = {}
        for inter in interactions:
            if inter.subject not in subjects:
                subjects[inter.subject] = []
            subjects[inter.subject].append(inter)
        
        # Generate report content
        report = f"Daily Learning Report for {user.name}\n\n"
        
        for subject, subject_interactions in subjects.items():
            aha_moments = [i for i in subject_interactions if i.aha_confidence and i.aha_confidence > 0.7]
            report += f"{subject}:\n"
            report += f"- Total interactions: {len(subject_interactions)}\n"
            report += f"- 'Aha moments': {len(aha_moments)}\n"
            if aha_moments:
                report += "- Highlights:\n"
                for aha in aha_moments:
                    report += f"  * {aha.content} ({aha.aha_confidence*100:.0f}% confidence)\n"
            report += "\n"
        
        return report
        
    except Exception as e:
        logging.error(f"Error generating parent report: {str(e)}")
        raise 

# AI service functions
async def generate_response(message, context=None):
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful AI teacher."},
                {"role": "user", "content": message}
            ] + (context or [])
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error generating AI response: {str(e)}")
        return "I apologize, but I'm having trouble processing your request right now."

async def analyze_learning_style(messages):
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "system",
                "content": "Analyze the learning style from these messages and provide insights."
            }] + messages
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error analyzing learning style: {str(e)}")
        return "Unable to analyze learning style at this time." 