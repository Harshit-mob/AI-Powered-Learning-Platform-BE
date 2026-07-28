import uuid
from typing import Dict, Any, List
from app.repositories.base.unit_of_work import UnitOfWork

class ContentService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def get_subjects(self, student_id: uuid.UUID) -> List[Dict[str, Any]]:
        from app.models.course import Subject, Chapter
        from sqlalchemy import func
        with self.uow:
            student = self.uow.students.find_by_id(student_id)
            if not student or not student.grade_id:
                return []
                
            subjects = self.uow.session.query(
                Subject, 
                func.count(Chapter.id).label('total_chapters')
            ).outerjoin(Chapter, Chapter.subject_id == Subject.id) \
             .filter(Subject.grade_id == student.grade_id) \
             .group_by(Subject.id).all()
            
            return [
                {
                    "subject_id": str(s.Subject.id),
                    "subject_name": s.Subject.name,
                    "icon": f"https://ui-avatars.com/api/?name={s.Subject.name}&background=random&format=png", 
                    "total_chapters": s.total_chapters
                }
                for s in subjects
            ]

    def get_chapters(self, student_id: uuid.UUID, subject_id: uuid.UUID) -> List[Dict[str, Any]]:
        from app.models.course import Chapter, Topic, Subtopic, LearningUnit
        from sqlalchemy import func
        
        with self.uow:
            from app.models.learning.student_daily_learning import StudentDailyLearning
            
            chapters = self.uow.session.query(Chapter).filter(Chapter.subject_id == subject_id).all()
            
            masteries = self.uow.mastery.get_by_student(student_id)
            mastery_by_concept = {m.concept_id: m for m in masteries}
            
            from app.models.assessment.learning_session import LearningSession
            
            completed_sessions = self.uow.session.query(LearningSession.content_id).filter(
                LearningSession.student_id == student_id,
                LearningSession.content_type.in_(["TOPIC", "MULTI_TOPIC"]),
                LearningSession.completion_reason == "COMPLETED"
            ).all()
            completed_session_topic_ids = {str(s[0]) for s in completed_sessions}

            daily_learnings = self.uow.session.query(StudentDailyLearning).filter(
                StudentDailyLearning.student_id == student_id,
                StudentDailyLearning.status == "COMPLETED"
            ).all()
            completed_daily_topic_ids = {str(dl.topic_id) for dl in daily_learnings}
            
            # Fetch all daily learnings history (selected topics)
            all_daily_learnings = self.uow.session.query(StudentDailyLearning).filter(
                StudentDailyLearning.student_id == student_id
            ).all()
            selected_topic_ids = {str(dl.topic_id) for dl in all_daily_learnings}
            
            completed_topic_ids = completed_session_topic_ids.union(completed_daily_topic_ids)
            
            result = []
            for chapter in chapters:
                topics = self.uow.session.query(
                    Topic,
                    func.count(LearningUnit.id).label('lu_count')
                ).outerjoin(Subtopic, Subtopic.topic_id == Topic.id) \
                 .outerjoin(LearningUnit, LearningUnit.subtopic_id == Subtopic.id) \
                 .filter(Topic.chapter_id == chapter.id) \
                 .group_by(Topic.id).all()
                
                lus = self.uow.session.query(LearningUnit.id).join(Subtopic).join(Topic).filter(Topic.chapter_id == chapter.id).all()
                chapter_lu_ids = [lu[0] for lu in lus]
                
                mastery_sum = 0
                completed_lus = 0
                for lu_id in chapter_lu_ids:
                    if lu_id in mastery_by_concept:
                        mastery_sum += mastery_by_concept[lu_id].mastery_percentage
                        if mastery_by_concept[lu_id].mastery_percentage >= 0.85:
                            completed_lus += 1
                            
                avg_mastery = int((mastery_sum / len(chapter_lu_ids)) * 100) if chapter_lu_ids else 0
                
                topics_data = [
                    {
                        "id": str(t.Topic.id),
                        "title": t.Topic.title,
                        "learning_units_count": t.lu_count,
                        "is_completed": str(t.Topic.id) in completed_topic_ids,
                        "is_selected": str(t.Topic.id) in selected_topic_ids
                    }
                    for t in topics
                ]
                
                total_topics = len(topics)
                completed_topics = sum(1 for t in topics_data if t["is_completed"])
                
                result.append({
                    "chapter_id": str(chapter.id),
                    "title": chapter.title,
                    "description": chapter.description or "",
                    "estimated_duration": sum(t.lu_count for t in topics) * 15,
                    "progress": {
                        "completed_topics": completed_topics,
                        "total_topics": total_topics,
                        "mastery": avg_mastery,
                        "revision_unlocked": avg_mastery > 80,
                        "daily_completed": False
                    },
                    "topics": topics_data
                })
            
            return result

    def get_full_curriculum(self, student_id: uuid.UUID) -> List[Dict[str, Any]]:
        subjects = self.get_subjects(student_id)
        result = []
        for s in subjects:
            subject_id = uuid.UUID(s["subject_id"])
            chapters = self.get_chapters(student_id, subject_id)
            s_copy = dict(s)
            s_copy["chapters"] = chapters
            result.append(s_copy)
        return result
