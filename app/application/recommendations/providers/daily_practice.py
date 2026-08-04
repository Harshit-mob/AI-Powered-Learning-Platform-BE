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
        from app.models.assessment.learning_session import LearningSession
        
        # Get subjects with completed daily sessions today
        completed_today_sessions = self.uow.session.query(
            Subject.name
        ).select_from(
            LearningSession
        ).join(
            Topic, Topic.id == LearningSession.content_id
        ).join(
            Chapter, Chapter.id == Topic.chapter_id
        ).join(
            Subject, Subject.id == Chapter.subject_id
        ).filter(
            LearningSession.student_id == student_id,
            LearningSession.session_type == "DAILY_PRACTICE",
            func.date(LearningSession.end_time) == today,
            LearningSession.completion_reason == "COMPLETED"
        ).all()
        
        completed_today_subjects = {s[0] for s in completed_today_sessions}
        
        pending_today_topics = defaultdict(list)
        past_pending_topics = defaultdict(list)
        past_completed_topics = defaultdict(list)
        
        for dl, subject_name in all_learnings:
            if dl.learning_date == today:
                if dl.status == "PENDING":
                    pending_today_topics[subject_name].append(str(dl.topic_id))
            else:
                if dl.status == "PENDING":
                    past_pending_topics[subject_name].append(str(dl.topic_id))
                elif dl.status == "COMPLETED":
                    past_completed_topics[subject_name].append(str(dl.topic_id))
                    
        recs = []
        
        # We can recommend daily practice for any subject that has active pending topics today,
        # OR has past pending/completed topics.
        all_subjects = set(pending_today_topics.keys()) | set(past_pending_topics.keys()) | set(past_completed_topics.keys())
        
        for subject_name in all_subjects:
            # Rule 1: If any daily session for this subject is finished today, skip it
            if subject_name in completed_today_subjects:
                continue
                
            # Rule 2: If there are active pending topics today, use them.
            if subject_name in pending_today_topics:
                topic_ids = pending_today_topics[subject_name]
            # Priority 1 fallback: Past check-ins but not completed
            elif subject_name in past_pending_topics:
                topic_ids = past_pending_topics[subject_name]
            # Priority 2 fallback: All past check-in topics
            else:
                topic_ids = past_completed_topics[subject_name]
                
            if not topic_ids:
                continue
                
            # De-duplicate topic_ids while preserving order
            unique_topic_ids = []
            seen = set()
            for tid in topic_ids:
                if tid not in seen:
                    unique_topic_ids.append(tid)
                    seen.add(tid)
            
            # Capped question counts: 15 for multi-topic, 10 for single-topic
            q_count = 15 if len(unique_topic_ids) > 1 else 10
                
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
                "content_ids": unique_topic_ids
            })
            
        return recs
