import uuid
from typing import Dict, Any, List
from app.repositories.base.unit_of_work import UnitOfWork

class ContentService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def get_subjects(self, student_id: uuid.UUID) -> List[Dict[str, Any]]:
        from app.models.course import Subject, Chapter, Topic, Subtopic, LearningUnit
        from app.models.quiz import Question
        from sqlalchemy import func
        with self.uow:
            student = self.uow.students.find_by_id(student_id)
            if not student or not student.grade_id:
                return []
                
            # Only return subjects that have active approved questions
            subjects = self.uow.session.query(
                Subject, 
                func.count(func.distinct(Chapter.id)).label('total_chapters')
            ).join(Chapter, Chapter.subject_id == Subject.id) \
             .join(Topic, Topic.chapter_id == Chapter.id) \
             .join(Subtopic, Subtopic.topic_id == Topic.id) \
             .join(LearningUnit, LearningUnit.subtopic_id == Subtopic.id) \
             .join(Question, Question.learning_unit_id == LearningUnit.id) \
             .filter(Subject.grade_id == student.grade_id, Question.is_active == True) \
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
        from app.models.quiz import Question
        from sqlalchemy import func
        
        with self.uow:
            from app.models.learning.student_daily_learning import StudentDailyLearning
            
            # Only fetch chapters that contain active approved questions
            chapters = self.uow.session.query(Chapter) \
             .join(Topic, Topic.chapter_id == Chapter.id) \
             .join(Subtopic, Subtopic.topic_id == Topic.id) \
             .join(LearningUnit, LearningUnit.subtopic_id == Subtopic.id) \
             .join(Question, Question.learning_unit_id == LearningUnit.id) \
             .filter(Chapter.subject_id == subject_id, Question.is_active == True) \
             .group_by(Chapter.id).all()
            
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
                # Only return topics that have active approved questions
                topics = self.uow.session.query(
                    Topic,
                    func.count(func.distinct(LearningUnit.id)).label('lu_count')
                ).join(Subtopic, Subtopic.topic_id == Topic.id) \
                 .join(LearningUnit, LearningUnit.subtopic_id == Subtopic.id) \
                 .join(Question, Question.learning_unit_id == LearningUnit.id) \
                 .filter(Topic.chapter_id == chapter.id, Question.is_active == True) \
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
                
                topics_data = []
                for t in topics:
                    tid_str = str(t.Topic.id)
                    is_comp = tid_str in completed_topic_ids
                    topics_data.append({
                        "id": tid_str,
                        "title": t.Topic.title,
                        "learning_units_count": t.lu_count,
                        "is_completed": is_comp,
                        "is_selected": (tid_str in selected_topic_ids) or is_comp
                    })
                
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

    def get_checked_in_curriculum(self, student_id: uuid.UUID, subject_name: str) -> List[Dict[str, Any]]:
        from app.models.course import Subject, Chapter
        from app.models.learning.student_daily_learning import StudentDailyLearning
        from sqlalchemy import func
        
        with self.uow:
            daily_learnings = self.uow.session.query(StudentDailyLearning).filter(
                StudentDailyLearning.student_id == student_id
            ).all()
            checked_in_topic_ids = {dl.topic_id for dl in daily_learnings}
            
            if not checked_in_topic_ids:
                return []
                
            chapters = self.uow.session.query(Chapter).join(
                Subject, Subject.id == Chapter.subject_id
            ).filter(
                func.lower(Subject.name) == func.lower(subject_name)
            ).all()
            
            result = []
            for chapter in chapters:
                chapter_topics = [
                    {
                        "id": str(t.id),
                        "title": t.title
                    }
                    for t in chapter.topics
                    if t.id in checked_in_topic_ids
                ]
                
                if chapter_topics:
                    result.append({
                        "chapter_id": str(chapter.id),
                        "title": chapter.title,
                        "topics": chapter_topics
                    })
                    
            return result
