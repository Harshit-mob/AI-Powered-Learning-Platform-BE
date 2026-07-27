import uuid
from typing import Dict, Any, Optional

from app.application.recommendations.providers.base import RecommendationProvider
from app.models.course import Topic, Chapter, LearningUnit
from app.models.learning.student_mastery import StudentMastery

class ChapterRevisionProvider(RecommendationProvider):
    def get_recommendation(self, student_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        # For phase 1, find the chapter containing the most recently practiced topic
        # As a heuristic, we'll just pull the student's recent mastery record and find its chapter
        recent_mastery = self.uow.session.query(StudentMastery).filter(
            StudentMastery.student_id == student_id
        ).order_by(StudentMastery.updated_at.desc()).first()
        
        if not recent_mastery:
            return None
            
        # lu_id is stored in concept_id in Phase 1
        lu_id = recent_mastery.concept_id
        
        # Find the LU, then Topic, then Chapter
        lu = self.uow.session.query(LearningUnit).filter(LearningUnit.id == lu_id).first()
        if not lu:
            return None
            
        from app.models.course import Subtopic
        subtopic = self.uow.session.query(Subtopic).filter(Subtopic.id == lu.subtopic_id).first()
        if not subtopic:
            return None
            
        topic = self.uow.session.query(Topic).filter(Topic.id == subtopic.topic_id).first()
        if not topic:
            return None
            
        chapter = self.uow.session.query(Chapter).filter(Chapter.id == topic.chapter_id).first()
        if not chapter:
            return None
            
        # Check unlock condition: Are all topics in this chapter completed?
        # For Phase 1, we consider a topic completed if its average mastery across LUs > 60%
        # Let's get all LUs for all topics in this chapter
        chapter_topics = self.uow.session.query(Topic).filter(Topic.chapter_id == chapter.id).all()
        topic_ids = [t.id for t in chapter_topics]
        
        chapter_lus = self.uow.session.query(LearningUnit).join(Subtopic).filter(Subtopic.topic_id.in_(topic_ids)).all()
        lu_ids = [lu.id for lu in chapter_lus]
        
        masteries = self.uow.session.query(StudentMastery).filter(
            StudentMastery.student_id == student_id,
            StudentMastery.concept_id.in_(lu_ids)
        ).all()
        
        # Calculate coverage
        is_locked = True
        reason = "Complete all topics in this chapter to unlock"
        status = "LOCKED"
        
        if len(masteries) >= len(lu_ids) and len(lu_ids) > 0:
            avg_mastery = sum(m.mastery_percentage for m in masteries) / len(masteries)
            if avg_mastery >= 0.6:
                is_locked = False
                status = "READY"
                reason = "You've mastered the basics. Time for a chapter review!"
            else:
                reason = "Average mastery too low to unlock chapter review."
                
        q_count = min(20, len(lu_ids))
        if q_count < 3:
            q_count = 3
        xp = q_count * 8 + 30 + 30

        return {
            "title": "Chapter Revision",
            "priority": 3,
            "estimated_duration": q_count,
            "question_count": q_count,
            "xp_reward": xp,
            "status": status,
            "reason": reason,
            "session_type": "CHAPTER_REVISION",
            "content_type": "CHAPTER",
            "content_ids": [str(chapter.id)]
        }
