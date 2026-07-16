import uuid
from typing import List, Dict, Any
from app.repositories.base.unit_of_work import UnitOfWork
from app.learning.models.dto import MasteryUpdatePayload

class ProgressTracker:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def generate_summary(self, student_id: uuid.UUID, updates: List[MasteryUpdatePayload]) -> Dict[str, Any]:
        """
        Calculates short-term progress summaries without running heavy queries.
        This provides instant feedback for the UI or Personalization engine.
        """
        mastered_this_session = 0
        total_gain = 0.0
        
        for update in updates:
            total_gain += max(0, update.new_mastery - update.old_mastery)
            if update.new_status == "MASTERED" and update.old_status != "MASTERED":
                mastered_this_session += 1
                
        return {
            "concepts_mastered_this_session": mastered_this_session,
            "net_mastery_gain": total_gain,
            "concepts_practiced": len(updates)
        }
