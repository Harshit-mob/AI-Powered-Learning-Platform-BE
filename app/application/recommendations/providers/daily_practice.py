import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from collections import defaultdict

from app.application.recommendations.providers.base import RecommendationProvider
from app.models.learning.student_daily_learning import StudentDailyLearning
from app.models.course import Topic, Chapter, Subject

class DailyPracticeProvider(RecommendationProvider):
    def get_recommendation(self, student_id: uuid.UUID) -> Optional[List[Dict[str, Any]]]:
        today = datetime.now(timezone.utc).date()
        
        # Get today's uncompleted daily learnings with subject details
        daily_learnings = self.uow.session.query(
            StudentDailyLearning,
            Subject.name.label("subject_name")
        ).join(
            Topic, Topic.id == StudentDailyLearning.topic_id
        ).join(
            Chapter, Chapter.id == Topic.chapter_id
        ).join(
            Subject, Subject.id == Chapter.subject_id
        ).filter(
            StudentDailyLearning.student_id == student_id,
            StudentDailyLearning.learning_date == today,
            StudentDailyLearning.status == "PENDING"
        ).all()
        
        if not daily_learnings:
            return None
            
        from sqlalchemy import func
        from app.models.course import LearningUnit, Subtopic

        subject_topics = defaultdict(list)
        for dl, subject_name in daily_learnings:
            subject_topics[subject_name].append(str(dl.topic_id))
            
        recs = []
        for subject_name, topic_ids in subject_topics.items():
            total_lus = self.uow.session.query(func.count(LearningUnit.id))\
                .join(Subtopic, Subtopic.id == LearningUnit.subtopic_id)\
                .filter(Subtopic.topic_id.in_(topic_ids)).scalar() or 0
            
            q_count = min(10, total_lus)
            if q_count < 3:
                q_count = 3
                
            xp = q_count * 5 + 20 + 15
            
            recs.append({
                "title": f"Daily session ({subject_name.lower()})",
                "priority": 1,
                "estimated_duration": q_count,
                "question_count": q_count,
                "xp_reward": xp,
                "status": "READY",
                "reason": f"Daily practice for {subject_name}",
                "session_type": "DAILY_PRACTICE",
                "content_type": "MULTI_TOPIC",
                "content_ids": topic_ids
            })
            
        return recs
