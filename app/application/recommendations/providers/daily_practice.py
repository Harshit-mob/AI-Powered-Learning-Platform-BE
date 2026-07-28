import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from collections import defaultdict

from sqlalchemy import func
from app.application.recommendations.providers.base import RecommendationProvider
from app.models.learning.student_daily_learning import StudentDailyLearning
from app.models.course import Topic, Chapter, Subject, LearningUnit, Subtopic

class DailyPracticeProvider(RecommendationProvider):
    def get_recommendation(self, student_id: uuid.UUID) -> Optional[List[Dict[str, Any]]]:
        today = datetime.now(timezone.utc).date()
        
        # Get all daily learnings (both today's and past) for this student
        all_learnings = self.uow.session.query(
            StudentDailyLearning,
            Subject.name.label("subject_name")
        ).join(
            Topic, Topic.id == StudentDailyLearning.topic_id
        ).join(
            Chapter, Chapter.id == Topic.chapter_id
        ).join(
            Subject, Subject.id == Chapter.subject_id
        ).filter(
            StudentDailyLearning.student_id == student_id
        ).order_by(
            StudentDailyLearning.learning_date.desc()
        ).all()
        
        if not all_learnings:
            return None
            
        # Group topic IDs by subject, separating today's pending from past
        subject_today_topics = defaultdict(list)
        subject_past_topics = defaultdict(list)
        
        for dl, subject_name in all_learnings:
            if dl.learning_date == today and dl.status == "PENDING":
                subject_today_topics[subject_name].append(str(dl.topic_id))
            else:
                subject_past_topics[subject_name].append(str(dl.topic_id))
                
        # Resolve which topic IDs to use for each subject
        subject_topics = {}
        all_subjects = set(subject_today_topics.keys()) | set(subject_past_topics.keys())
        for subject_name in all_subjects:
            if subject_name in subject_today_topics:
                # Prioritize today's check-ins
                subject_topics[subject_name] = list(set(subject_today_topics[subject_name]))
            else:
                # Fall back to past check-ins
                subject_topics[subject_name] = list(set(subject_past_topics[subject_name]))
            
        recs = []
        for subject_name, topic_set in subject_topics.items():
            topic_ids = list(topic_set)
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
