import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.application.recommendations.providers.base import RecommendationProvider
from app.models.learning.student_mastery import StudentMastery

class WeakPointProvider(RecommendationProvider):
    def get_recommendation(self, student_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        masteries = self.uow.session.query(StudentMastery).filter(
            StudentMastery.student_id == student_id
        ).all()
        
        if not masteries:
            return None
            
        now = datetime.now(timezone.utc)
        
        # Calculate Priority Score for each mastery record
        # Priority = Low Mastery + Time Since Practice + Recent Wrong Answers
        scored_masteries = []
        for m in masteries:
            mastery_score = 1.0 - m.mastery_percentage # High priority if mastery is low
            
            days_since = 0
            if m.updated_at:
                days_since = (now - m.updated_at).days
            time_score = min(1.0, days_since / 14.0) # Caps at 14 days
            
            wrong_ratio = 0
            total = m.correct_count + m.wrong_count
            if total > 0:
                wrong_ratio = m.wrong_count / total
                
            priority_score = (mastery_score * 0.5) + (time_score * 0.3) + (wrong_ratio * 0.2)
            
            scored_masteries.append((priority_score, m))
            
        # Sort by highest priority
        scored_masteries.sort(key=lambda x: x[0], reverse=True)
        top_weak = scored_masteries[0][1]
        top_score = scored_masteries[0][0]
        
        # Only recommend if the score is somewhat high, meaning they actually need it
        if top_score < 0.3:
            return None
            
        return {
            "title": "Weak Point Booster",
            "priority": 2,
            "estimated_duration": 8,
            "question_count": 8,
            "xp_reward": 80,
            "status": "NEEDS_ATTENTION",
            "reason": "Targeted practice on concepts you struggled with recently",
            "session_type": "WEAK_POINT",
            "content_type": "STUDENT",
            "content_ids": [str(student_id)]
        }
