import uuid
from typing import Dict, Any, Optional, List

from app.application.recommendations.providers.base import RecommendationProvider
from app.models.assessment.learning_session import LearningSession


class RevisionProvider(RecommendationProvider):
    """
    Recommends a revision session for each subject where the student has ever
    added daily check-in topics.
    """

    def get_recommendation(self, student_id: uuid.UUID) -> Optional[List[Dict[str, Any]]]:
        from app.models.learning.student_daily_learning import StudentDailyLearning
        from app.models.course import Subject, Chapter, Topic, LearningUnit, Subtopic
        from app.models.quiz import Question
        from sqlalchemy import func
        
        # 1. Fetch all daily check-in topics for the student
        checkins = self.uow.session.query(
            StudentDailyLearning.topic_id,
            Subject.name.label("subject_name")
        ).join(
            Topic, Topic.id == StudentDailyLearning.topic_id
        ).join(
            Chapter, Chapter.id == Topic.chapter_id
        ).join(
            Subject, Subject.id == Chapter.subject_id
        ).filter(
            StudentDailyLearning.student_id == student_id
        ).all()
        
        if not checkins:
            return None
            
        # Group topic IDs by subject name
        subject_topics = {}
        for row in checkins:
            subj_name = row.subject_name
            topic_id = row.topic_id
            if subj_name not in subject_topics:
                subject_topics[subj_name] = set()
            subject_topics[subj_name].add(topic_id)
            
        results = []
        for subject_name, topic_ids in subject_topics.items():
            topic_uuid_list = list(topic_ids)
            
            # Count the total unique questions under these topics
            total_questions = self.uow.session.query(func.count(Question.id)).join(
                LearningUnit, LearningUnit.id == Question.learning_unit_id
            ).join(
                Subtopic, Subtopic.id == LearningUnit.subtopic_id
            ).filter(
                Subtopic.topic_id.in_(topic_uuid_list)
            ).scalar() or 0
            
            if total_questions == 0:
                continue
                
            max_xp = (total_questions * 6) + 20 + 20
            
            results.append({
                "title": "Revision",
                "subject": subject_name,
                "priority": 2, # Sits between Daily Practice (1) and Chapter Revision (3)
                "estimated_duration": total_questions,
                "question_count": total_questions,
                "xp_reward": max_xp,
                "status": "READY",
                "reason": f"Revise {total_questions} questions from your past topics. Earn up to {max_xp} XP!",
                "session_type": "REVISION",
                "content_type": "MULTI_TOPIC",
                "content_ids": [str(tid) for tid in topic_uuid_list],
                "scope": "multi_topic",
                "content_label": f"{subject_name} Revision",
                "weak_concepts": [],
            })
            
        return results if results else None
