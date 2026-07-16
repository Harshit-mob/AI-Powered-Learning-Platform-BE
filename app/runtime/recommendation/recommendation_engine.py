from typing import List
from app.repositories.base.unit_of_work import UnitOfWork
from app.learning.models.dto import LearningOutcome
from app.runtime.models.dto import RecommendationItem
from app.runtime.recommendation.recommendation_rules import RecommendationRules

class RecommendationEngine:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.rules = RecommendationRules()

    def process(self, outcome: LearningOutcome) -> List[RecommendationItem]:
        """
        Generates and persists recommendations based on learning outcomes.
        """
        recommendations = self.rules.generate(outcome)
        
        # Persist through repository
        with self.uow:
            # Take top 3 highest priority recommendations to persist
            top_recs = recommendations[:3]
            for rec in top_recs:
                self.uow.recommendations.create_recommendation({
                    "student_id": outcome.student_id,
                    "target_content_id": rec.target_content_id,
                    "target_content_type": rec.target_content_type,
                    "recommended_session_type": rec.recommended_session_type,
                    "reason": rec.reason,
                    "priority_score": rec.priority,
                    "completion_status": "PENDING"
                })
            self.uow.commit()
            
        return recommendations
