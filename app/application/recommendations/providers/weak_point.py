import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from collections import defaultdict

from app.application.recommendations.providers.base import RecommendationProvider
from app.models.learning.student_mastery import StudentMastery
from app.models.course import Subject, Chapter, Topic, Subtopic, LearningUnit

class WeakPointProvider(RecommendationProvider):
    def get_recommendation(self, student_id: uuid.UUID) -> Optional[List[Dict[str, Any]]]:
        # Get masteries with subject details by joining LearningUnit
        masteries = self.uow.session.query(
            StudentMastery,
            Subject.name.label("subject_name")
        ).join(
            LearningUnit, LearningUnit.id == StudentMastery.concept_id
        ).join(
            Subtopic, Subtopic.id == LearningUnit.subtopic_id
        ).join(
            Topic, Topic.id == Subtopic.topic_id
        ).join(
            Chapter, Chapter.id == Topic.chapter_id
        ).join(
            Subject, Subject.id == Chapter.subject_id
        ).filter(
            StudentMastery.student_id == student_id
        ).all()
        
        if not masteries:
            return None
            
        now = datetime.now(timezone.utc)
        subject_masteries = defaultdict(list)
        for m, subject_name in masteries:
            subject_masteries[subject_name].append(m)
            
        recs = []
        for subject_name, m_list in subject_masteries.items():
            scored_masteries = []
            for m in m_list:
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
            if top_score >= 0.3:
                q_count = min(8, len(scored_masteries))
                if q_count < 3:
                    q_count = 3
                xp = q_count * 8 + 20 + 25
                
                # Fetch topic IDs corresponding to the weak learning units of this subject
                weak_lu_ids = [item[1].concept_id for item in scored_masteries[:q_count]]
                topic_ids = [
                    row[0] for row in self.uow.session.query(Subtopic.topic_id)
                    .join(LearningUnit, LearningUnit.subtopic_id == Subtopic.id)
                    .filter(LearningUnit.id.in_(weak_lu_ids))
                    .distinct()
                    .all()
                ]
                
                recs.append({
                    "title": f"Weak point booster ({subject_name.lower()})",
                    "priority": 2,
                    "estimated_duration": q_count,
                    "question_count": q_count,
                    "xp_reward": xp,
                    "status": "NEEDS_ATTENTION",
                    "reason": f"Targeted practice on {subject_name} concepts you struggled with recently",
                    "session_type": "WEAK_POINT",
                    "content_type": "MULTI_TOPIC",
                    "content_ids": [str(tid) for tid in topic_ids]
                })
                
        return recs if recs else None
