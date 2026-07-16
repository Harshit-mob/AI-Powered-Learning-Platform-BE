import uuid
from typing import List
from app.repositories.base.unit_of_work import UnitOfWork
from app.runtime.models.dto import RecommendationItem

class LearningPathEngine:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def generate_path(self, student_id: uuid.UUID, recommendations: List[RecommendationItem]) -> List[str]:
        """
        Generates the sequential learning path steps based on the highest priority recommendation.
        """
        if not recommendations:
            return ["PRACTICE", "PRACTICE", "ASSESSMENT"]
            
        top_rec = recommendations[0]
        
        if top_rec.recommended_session_type == "RECOVERY":
            # Knowledge Graph usage theoretically injected here to find prerequisites
            # e.g. prereq_ids = self.uow.concepts.prerequisite_concepts(top_rec.target_content_id)
            return ["PREREQUISITE_REVISION", "RECOVERY", "PRACTICE", "ASSESSMENT"]
            
        elif top_rec.recommended_session_type == "CHALLENGE":
            return ["CHALLENGE", "NEXT_TOPIC"]
            
        elif top_rec.recommended_session_type == "REVISION":
            return ["REVISION", "PRACTICE"]
            
        return ["PRACTICE", "ASSESSMENT"]
