"""AI Teacher Service for managing educational interactions."""
from datetime import datetime
import openai
from app.extensions import db
from app.models import Teacher, User, Interaction, SubjectProgress, LessonPlan, Group, Suggestion

class AITeacher:
    def __init__(self, teacher_id):
        self.teacher = Teacher.query.get(teacher_id)
        if not self.teacher:
            raise ValueError("Teacher not found")
            
    async def generate_response(self, user_id, content, subject):
        """Generate an AI response with potential 'aha moment' detection."""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
            
        # Create system message based on user's profile
        system_message = self._create_system_message(user, subject)
        
        try:
            # Get AI response
            response = await self._get_ai_response(system_message, content)
            
            # Analyze for "aha moment"
            aha_analysis = await self._analyze_aha_potential(response, user)
            
            # Record interaction
            interaction = Interaction(
                user_id=user_id,
                teacher_id=self.teacher.teacher_id,
                content=response,
                type='lesson' if not aha_analysis['is_aha'] else 'aha',
                subject=subject,
                aha_trigger=aha_analysis.get('trigger'),
                aha_confidence=aha_analysis.get('confidence')
            )
            db.session.add(interaction)
            
            # Update user's aha count if applicable
            if aha_analysis['is_aha']:
                user.aha_count += 1
                
            # Update subject progress
            self._update_subject_progress(user, subject, aha_analysis)
            
            # Generate improvement suggestions
            await self._generate_suggestions(user, aha_analysis)
            
            db.session.commit()
            
            return {
                'content': response,
                'analytics': {
                    'is_aha': aha_analysis['is_aha'],
                    'confidence': aha_analysis['confidence'],
                    'trigger': aha_analysis.get('trigger')
                }
            }
            
        except Exception as e:
            db.session.rollback()
            raise
            
    def create_lesson_plan(self, user_id, subject):
        """Create a personalized lesson plan."""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
            
        # Get current progress
        progress = SubjectProgress.query.filter_by(
            user_id=user_id,
            subject=subject
        ).first()
        
        # Generate lesson plan based on progress
        plan = LessonPlan(
            teacher_id=self.teacher.teacher_id,
            user_id=user_id,
            date=datetime.utcnow().date(),
            subject=subject,
            content=self._generate_lesson_content(user, progress),
            goal=self._determine_next_goal(progress),
            aha_strategy=self._select_aha_strategy(user)
        )
        
        db.session.add(plan)
        db.session.commit()
        
        return plan.to_dict()
        
    def create_group_activity(self, user_ids, subject):
        """Create a collaborative learning activity."""
        # Verify all users exist
        users = User.query.filter(User.user_id.in_(user_ids)).all()
        if len(users) != len(user_ids):
            raise ValueError("One or more users not found")
            
        # Generate appropriate group task
        task = self._generate_group_task(users, subject)
        
        group = Group(
            user_ids=','.join(map(str, user_ids)),
            task=task,
            subject=subject
        )
        
        db.session.add(group)
        db.session.commit()
        
        return group.to_dict()
        
    async def _get_ai_response(self, system_message, content):
        """Get response from OpenAI API."""
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": content}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
        
    async def _analyze_aha_potential(self, response, user):
        """Analyze if the response might trigger an 'aha moment'."""
        analysis_prompt = f"""
        Analyze this educational response for potential "aha moment" characteristics.
        Response: {response}
        Student profile: {user.to_dict()}
        
        Rate the following on a scale of 0-1:
        1. Insight potential
        2. Relevance to student
        3. Clarity of explanation
        """
        
        analysis = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an educational insight analyzer."},
                {"role": "user", "content": analysis_prompt}
            ],
            temperature=0.3
        )
        
        # Parse the analysis
        result = analysis.choices[0].message.content
        confidence = self._calculate_aha_confidence(result)
        
        return {
            'is_aha': confidence > 0.7,
            'confidence': confidence,
            'trigger': self._identify_trigger(result)
        }
        
    def _create_system_message(self, user, subject):
        """Create a personalized system message based on user profile."""
        return f"""
        You are Ms. Emma, an expert {subject} teacher. 
        Student profile:
        - Age: {user.age}
        - Learning style: {user.learning_style}
        - Language: {user.language}
        - Disabilities: {user.disabilities}
        
        Adapt your teaching style accordingly and aim for "aha moments".
        """
        
    def _update_subject_progress(self, user, subject, aha_analysis):
        """Update the user's progress in the subject."""
        progress = SubjectProgress.query.filter_by(
            user_id=user.user_id,
            subject=subject
        ).first()
        
        if not progress:
            progress = SubjectProgress(
                user_id=user.user_id,
                subject=subject,
                progress_level='beginner',
                goals_achieved='[]'
            )
            db.session.add(progress)
            
        # Update progress based on aha moment
        if aha_analysis['is_aha']:
            self._advance_progress(progress)
            
    async def _generate_suggestions(self, user, aha_analysis):
        """Generate system improvement suggestions based on interaction."""
        if aha_analysis['confidence'] < 0.5:
            suggestion = Suggestion(
                teacher_id=self.teacher.teacher_id,
                content=f"Consider adding more {user.learning_style} elements for this topic"
            )
            db.session.add(suggestion)
            
    def _calculate_aha_confidence(self, analysis_result):
        """Calculate confidence score from analysis."""
        # Implementation would parse the analysis result
        # and return a confidence score between 0 and 1
        return 0.85  # Placeholder
        
    def _identify_trigger(self, analysis_result):
        """Identify what triggered the potential aha moment."""
        # Implementation would analyze the result
        # and return the trigger type
        return "analogy"  # Placeholder
        
    def _generate_lesson_content(self, user, progress):
        """Generate personalized lesson content."""
        # Implementation would create lesson content
        # based on user profile and progress
        return "Lesson content placeholder"
        
    def _determine_next_goal(self, progress):
        """Determine the next learning goal."""
        # Implementation would analyze progress
        # and return appropriate next goal
        return "Next goal placeholder"
        
    def _select_aha_strategy(self, user):
        """Select an appropriate strategy for triggering aha moments."""
        # Implementation would choose strategy
        # based on user profile and past success
        return "visualization"  # Placeholder
        
    def _generate_group_task(self, users, subject):
        """Generate an appropriate group task."""
        # Implementation would create collaborative task
        # based on users' profiles and subject
        return "Group task placeholder"
        
    def _advance_progress(self, progress):
        """Advance the user's progress level."""
        # Implementation would update progress
        # based on achievements and goals
        progress.progress_level = 'intermediate'  # Placeholder 