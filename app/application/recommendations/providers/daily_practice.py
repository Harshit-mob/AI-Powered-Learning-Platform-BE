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
        
        from app.models.learning.student_mastery import StudentMastery
        from app.models.course import LearningUnit, Subtopic
        
        pending_today_topics = defaultdict(list)
        past_pending_topics = defaultdict(list)
        past_completed_topics = defaultdict(list)
        
        for dl, subject_name in all_learnings:
            # Check if this topic has any unmastered LUs (mastery < 1.0)
            topic_lus = self.uow.session.query(LearningUnit.id).join(
                Subtopic, Subtopic.id == LearningUnit.subtopic_id
            ).filter(Subtopic.topic_id == dl.topic_id).all()
            
            lu_ids = [lu[0] for lu in topic_lus]
            if lu_ids:
                mastery_records = self.uow.session.query(StudentMastery).filter(
                    StudentMastery.student_id == student_id,
                    StudentMastery.concept_id.in_(lu_ids)
                ).all()
                mastery_map = {m.concept_id: m.mastery_percentage for m in mastery_records}
                
                # Check if all LUs are 100% mastered
                all_mastered = True
                for lu_id in lu_ids:
                    if float(mastery_map.get(lu_id, 0.0)) < 1.0:
                        all_mastered = False
                        break
                
                if all_mastered:
                    # Topic is 100% mastered, do not recommend it again
                    continue
            
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
