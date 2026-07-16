import os
import sys
import uuid

# Ensure app path is loaded
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import SessionLocal
from app.repositories.base.unit_of_work import UnitOfWork
from app.models.course import Chapter, LearningUnit
from app.models.core.student import Student
from app.runtime.session.session_engine import SessionEngine
from app.runtime.session.session_types import SessionType, LearningContext

def verify_distribution():
    db = SessionLocal()
    uow = UnitOfWork(lambda: db)
    
    topic_id = None
    with uow:
        first_chapter = uow.session.query(Chapter).first()
        if not first_chapter or not first_chapter.topics:
            print("No topics found.")
            return
            
        topic_id = first_chapter.topics[0].id
    
    # Create or get dummy student
    student_id = uuid.uuid4()
    with uow:
        uow.session.add(Student(id=student_id, name="Test Student"))
        uow.commit()
        
    engine = SessionEngine(uow)
    payload = engine.generate(
        student_id=student_id,
        content_id=topic_id,
        content_type="TOPIC",
        session_type=SessionType.DAILY_PRACTICE,
        context=LearningContext.TODAY_SCHOOL_TOPIC
    )
    
    print("\n--- SESSION DISTRIBUTION REPORT ---")
    print(f"Target Duration: 600s | Actual Expected: {payload.expected_time_seconds}s")
    print(f"Total Questions: {len(payload.questions)}\n")
    
    total_time = 0
    lu_counts = {}
    
    for i, q in enumerate(payload.questions):
        # Fetch the real question to get the LU (DTO doesn't have it by default)
        real_q = db.query(LearningUnit).join(LearningUnit.questions).filter(LearningUnit.questions.any(id=q.question_id)).first()
        lu_title = real_q.title if real_q else "Unknown"
        lu_counts[lu_title] = lu_counts.get(lu_title, 0) + 1
        
        total_time += q.expected_time
        
        print(f"Question {i+1}")
        print(f"Learning Unit: {lu_title}")
        print(f"Difficulty: {q.difficulty}")
        print(f"Bloom: {q.taxonomy}")
        print(f"Expected Time: {q.expected_time}s\n")
        
    print("--- SUMMARY ---")
    print(f"Total Expected Time: {total_time}s")
    print(f"Unique Learning Units Hit: {len(lu_counts)}")
    for lu, count in lu_counts.items():
        print(f"  - {lu}: {count} questions")
        
if __name__ == "__main__":
    verify_distribution()
