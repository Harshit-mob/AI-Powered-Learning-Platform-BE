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
            
        subject_topics = defaultdict(list)
        for dl, subject_name in daily_learnings:
            subject_topics[subject_name].append(str(dl.topic_id))
            
        recs = []
        for subject_name, topic_ids in subject_topics.items():
            recs.append({
                "title": f"Daily session ({subject_name.lower()})",
                "priority": 1,
                "estimated_duration": 10 + (len(topic_ids) * 2),
                "question_count": 10 + (len(topic_ids) * 2),
                "xp_reward": 50,
                "status": "READY",
                "reason": f"Daily practice for {subject_name}",
                "session_type": "DAILY_PRACTICE",
                "content_type": "MULTI_TOPIC",
                "content_ids": topic_ids
            })
            
        return recs
