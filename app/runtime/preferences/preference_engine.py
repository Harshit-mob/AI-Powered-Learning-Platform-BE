import uuid
from typing import Dict, Any
from app.repositories.base.unit_of_work import UnitOfWork

class PreferenceEngine:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def get_preference_adjustments(self, student_id: uuid.UUID) -> Dict[str, Any]:
        """
        Loads student preferences to influence the UI or session generation rules.
        """
        with self.uow:
            student = self.uow.students.find_with_preferences(student_id)
            if student and student.preferences:
                return {
                    "preferred_scheduler": student.preferences.preferred_scheduler,
                    "difficulty_preference": student.preferences.difficulty_preference,
                    "voice_mode_enabled": student.preferences.voice_mode_enabled
                }
        return {}
