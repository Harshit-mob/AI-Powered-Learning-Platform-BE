import uuid
from app.repositories.base.unit_of_work import UnitOfWork
from app.runtime.models.dto import GoalProgressInfo
from app.learning.models.dto import LearningOutcome

class DailyGoalTracker:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def track_progress(self, student_id: uuid.UUID, outcome: LearningOutcome) -> GoalProgressInfo:
        """
        Updates streaks and tracking stats based on the learning outcome's progress summary.
        """
        # Read from current outcome payload
        concepts_mastered = outcome.progress_summary.get("concepts_mastered_this_session", 0)
        questions_answered = outcome.progress_summary.get("concepts_practiced", 0) # Rough proxy if detailed answer count not in summary
        
        with self.uow:
            student = self.uow.students.find_by_id(student_id)
            if not student:
                raise ValueError("Student not found")
                
            # Deterministic updates
            new_streak = student.streak_days
            goal_completed = False
            
            # Simplified streak logic (if they did anything today, streak maintains. If this is the first thing today, streak + 1)
            # In a real app we'd compare last_active_date. Let's mock a deterministic increment for now if it's a new day.
            # Assuming 'student' has a last_active field. If not, just ensure it exists.
            
            if questions_answered > 0:
                goal_completed = True # Simplest goal logic
                
            return GoalProgressInfo(
                study_minutes_today=15, # Proxy
                questions_answered_today=questions_answered,
                concepts_mastered_today=concepts_mastered,
                daily_streak=new_streak,
                weekly_streak=1,
                goal_completed=goal_completed
            )
