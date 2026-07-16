import uuid
from typing import Dict, Any
from app.repositories.base.unit_of_work import UnitOfWork
from app.services.analytics.models.dto import QuestionQualityReport

class QuestionQualityMonitor:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def analyze_quality(self, question_id: uuid.UUID) -> QuestionQualityReport:
        """
        Monitors question health. Flags it if it falls outside acceptable bounds.
        """
        with self.uow:
            analytics = self.uow.question_analytics.get_by_question_id(question_id)
            if not analytics or analytics.total_attempts < 10:
                # Not enough data
                return QuestionQualityReport(question_id=question_id, flagged=False, reason="", metrics={})
                
            flagged = False
            reasons = []
            
            if analytics.accuracy_rate < 0.15:
                flagged = True
                reasons.append("Accuracy too low (< 15%).")
            elif analytics.accuracy_rate > 0.98 and analytics.total_attempts > 50:
                flagged = True
                reasons.append("Accuracy abnormally high (> 98%). Too easy.")
                
            if analytics.skip_rate > 0.30:
                flagged = True
                reasons.append("Skip rate too high (> 30%).")
                
            return QuestionQualityReport(
                question_id=question_id,
                flagged=flagged,
                reason=" | ".join(reasons),
                metrics={
                    "accuracy": analytics.accuracy_rate,
                    "skip_rate": analytics.skip_rate,
                    "attempts": analytics.total_attempts
                }
            )
