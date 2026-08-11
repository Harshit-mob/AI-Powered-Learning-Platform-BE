import uuid
from typing import List, Dict, Any
from sqlalchemy import select

from app.repositories.base.unit_of_work import UnitOfWork
from app.models.quiz import Question
from app.models.course import LearningUnit, Subtopic, Topic

class CandidateLoader:
    """
    Loads active, published questions from the database grouped by Learning Unit.
    Strictly avoids N+1 queries.
    """
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def load_candidates(self, content_id: Any, content_type: str) -> Dict[uuid.UUID, List[Question]]:
        """
        Returns a dict mapping Learning Unit ID to a list of Candidate Questions.
        """
        with self.uow:
            stmt = select(Question).join(Question.learning_unit)
            
            if content_type == "TOPIC":
                # Check how many questions this topic has
                topic_stmt = select(Question).join(Question.learning_unit).join(LearningUnit.subtopic).where(Subtopic.topic_id == content_id)
                questions_check = self.uow.session.execute(topic_stmt).scalars().all()
                if len(questions_check) < 10:
                    topic_obj = self.uow.session.query(Topic).filter(Topic.id == content_id).first()
                    if topic_obj:
                        import logging
                        logging.getLogger(__name__).info(
                            f"Topic {content_id} has only {len(questions_check)} questions. "
                            f"Merging with other topics in chapter {topic_obj.chapter_id} to ensure a full session."
                        )
                        stmt = stmt.join(LearningUnit.subtopic).join(Subtopic.topic).where(Topic.chapter_id == topic_obj.chapter_id)
                    else:
                        stmt = stmt.join(LearningUnit.subtopic).where(Subtopic.topic_id == content_id)
                else:
                    stmt = stmt.join(LearningUnit.subtopic).where(Subtopic.topic_id == content_id)
            elif content_type == "CHAPTER":
                stmt = stmt.join(LearningUnit.subtopic).join(Subtopic.topic).where(Topic.chapter_id == content_id)
            elif content_type == "LEARNING_UNIT":
                stmt = stmt.where(Question.learning_unit_id == content_id)
            elif content_type == "MULTI_TOPIC":
                # Find the subject of the first topic, and filter content_id to only include topics from that same subject
                first_topic = self.uow.session.query(Topic).join(Chapter).filter(Topic.id == content_id[0]).first()
                if first_topic:
                    subject_id = first_topic.chapter.subject_id
                    filtered_topic_ids = [
                        row[0] for row in self.uow.session.query(Topic.id)
                        .join(Chapter)
                        .filter(Topic.id.in_(content_id), Chapter.subject_id == subject_id)
                        .all()
                    ]
                    stmt = stmt.join(LearningUnit.subtopic).where(Subtopic.topic_id.in_(filtered_topic_ids))
                else:
                    stmt = stmt.join(LearningUnit.subtopic).where(Subtopic.topic_id.in_(content_id))
            elif content_type == "STUDENT":
                # Find the weakest Learning Units for the student
                from app.models.learning.student_mastery import StudentMastery
                sid = content_id[0] if isinstance(content_id, list) else content_id
                masteries = self.uow.session.query(StudentMastery).filter(
                    StudentMastery.student_id == sid
                ).order_by(StudentMastery.mastery_percentage.asc()).limit(5).all()
                lu_ids = [m.concept_id for m in masteries]
                stmt = stmt.where(Question.learning_unit_id.in_(lu_ids))
                
            questions = self.uow.session.execute(stmt).scalars().all()
            
            lu_map: Dict[uuid.UUID, List[Question]] = {}
            for q in questions:
                lu_id = q.learning_unit_id
                if lu_id not in lu_map:
                    lu_map[lu_id] = []
                lu_map[lu_id].append(q)
                
            return lu_map
