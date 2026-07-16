import asyncio
from app.database.session import SessionLocal
from app.repositories.base.unit_of_work import UnitOfWork
from app.runtime.session.session_generator import SessionGenerator
from app.runtime.session.session_types import SessionType
import uuid

def run():
    # Pass the factory, not an instance
    uow = UnitOfWork(SessionLocal)
    db = SessionLocal()
    
    from app.models.core.student import Student
    from app.models.quiz import Question
    from app.models.course import LearningUnit, Subtopic, Topic
    
    student = db.query(Student).first()
    # Find a topic that has questions
    question = db.query(Question).filter(Question.learning_unit_id.isnot(None)).first()
    
    if not student or not question:
        print("No student or question found in DB")
        db.close()
        return
        
    lu = db.query(LearningUnit).filter(LearningUnit.id == question.learning_unit_id).first()
    subtopic = db.query(Subtopic).filter(Subtopic.id == lu.subtopic_id).first()
    topic = db.query(Topic).filter(Topic.id == subtopic.topic_id).first()
    
    topic_id = topic.id
    
    print(f"Testing with Student: {student.id}, Topic: {topic_id}")
    db.close()
    
    generator = SessionGenerator(uow)
    try:
        payload = generator.generate(
            student_id=student.id,
            content_id=topic_id,
            content_type="TOPIC",
            session_type=SessionType.DAILY_PRACTICE
        )
        print("Success! Generated questions:")
        for q in payload.questions:
            print(f"- {q.question_id} ({q.difficulty})")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run()
