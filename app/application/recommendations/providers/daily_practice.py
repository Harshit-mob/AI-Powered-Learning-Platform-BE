import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from app.application.recommendations.providers.base import RecommendationProvider
from app.models.learning.student_daily_learning import StudentDailyLearning

class DailyPracticeProvider(RecommendationProvider):
    def get_recommendation(self, student_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        today = datetime.now(timezone.utc).date()
        
        # Get today's uncompleted daily learnings
        daily_learnings = self.uow.session.query(StudentDailyLearning).filter(
            StudentDailyLearning.student_id == student_id,
            StudentDailyLearning.learning_date == today,
            StudentDailyLearning.status == "PENDING"
        ).all()
        
        if not daily_learnings:
            return None
            
        topic_ids = [str(dl.topic_id) for dl in daily_learnings]
        
        return {
            "title": "Daily Practice",
            "priority": 1,
            "estimated_duration": 10 + (len(topic_ids) * 2),
            "question_count": 10 + (len(topic_ids) * 2),
            "xp_reward": 50,
            "status": "READY",
            "reason": "Based on today's school topics",
            "session_type": "DAILY_PRACTICE",
            "content_type": "MULTI_TOPIC",
            "content_ids": topic_ids
        }
