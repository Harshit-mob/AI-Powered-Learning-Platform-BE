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
            
        # Group by subject and check daily status
        completed_today_subjects = set()
        pending_today_topics = defaultdict(list)
        past_pending_topics = defaultdict(list)
        past_completed_topics = defaultdict(list)
        
        for dl, subject_name in all_learnings:
            if dl.learning_date == today:
                if dl.status == "COMPLETED":
                    completed_today_subjects.add(subject_name)
                elif dl.status == "PENDING":
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
            
            total_lus = self.uow.session.query(func.count(LearningUnit.id))\
                .join(Subtopic, Subtopic.id == LearningUnit.subtopic_id)\
                .filter(Subtopic.topic_id.in_(unique_topic_ids)).scalar() or 0
            
            if total_lus == 0:
                continue
                
            # Target 10-15 questions
            q_count = min(15, total_lus)
            if q_count < 10 and total_lus >= 10:
                q_count = 10
            elif q_count < 3:
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
                "content_ids": unique_topic_ids
            })
            
        return recs
