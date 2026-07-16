import os
import sys
import uuid
import collections

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import SessionLocal
from app.repositories.base.unit_of_work import UnitOfWork
from app.models.course import Chapter, LearningUnit
from app.models.quiz import Question
from app.models.core.student import Student
from app.runtime.session.session_engine import SessionEngine
from app.runtime.session.session_types import SessionType, LearningContext

def run_audit():
    db = SessionLocal()
    uow = UnitOfWork(lambda: db)
    
    # ---------------------------------------------------------
    # PHASE 1 & 2: Content Validation
    # ---------------------------------------------------------
    lus = db.query(LearningUnit).all()
    questions = db.query(Question).all()
    
    print("--- PHASE 1 & 2: Content Validation ---")
    print(f"Total LUs: {len(lus)}")
    print(f"Total Questions: {len(questions)}")
    
    lu_issues = 0
    for lu in lus:
        if not lu.title or not lu.learning_objective:
            lu_issues += 1
            
    q_issues = []
    q_texts = set()
    for q in questions:
        if not q.text or not q.correct_option or not q.mcq_options:
            q_issues.append("MISSING_FIELDS")
        if q.text in q_texts:
            q_issues.append("DUPLICATE_TEXT")
        q_texts.add(q.text)
        
    print(f"LU Issues: {lu_issues}")
    print(f"Question Issues: {collections.Counter(q_issues)}")
    
    # ---------------------------------------------------------
    # PHASE 3: Session Engine Validation (20 Sessions)
    # ---------------------------------------------------------
    print("\n--- PHASE 3: Session Engine Validation ---")
    first_chapter = db.query(Chapter).first()
    if not first_chapter or not first_chapter.topics:
        print("No topics found for session generation.")
        return
        
    topic_id = first_chapter.topics[0].id
    student_id = uuid.uuid4()
    with uow:
        uow.session.add(Student(id=student_id, name="QA Student"))
        uow.commit()
        
    engine = SessionEngine(uow)
    
    session_stats = {
        "total_sessions": 0,
        "empty_sessions": 0,
        "duplicate_questions": 0,
        "avg_duration": 0,
        "avg_questions": 0
    }
    
    total_q_count = 0
    total_expected_time = 0
    
    for i in range(20):
        payload = engine.generate(
            student_id=student_id,
            content_id=topic_id,
            content_type="TOPIC",
            session_type=SessionType.DAILY_PRACTICE,
            context=LearningContext.TODAY_SCHOOL_TOPIC
        )
        
        session_stats["total_sessions"] += 1
        
        if not payload.questions:
            session_stats["empty_sessions"] += 1
            continue
            
        total_q_count += len(payload.questions)
        q_ids = [q.question_id for q in payload.questions]
        
        if len(q_ids) != len(set(q_ids)):
            session_stats["duplicate_questions"] += 1
            
        time_for_session = sum(q.expected_time for q in payload.questions)
        total_expected_time += time_for_session
        
    if session_stats["total_sessions"] > 0:
        session_stats["avg_questions"] = total_q_count / session_stats["total_sessions"]
        session_stats["avg_duration"] = total_expected_time / session_stats["total_sessions"]
        
    print(session_stats)

if __name__ == "__main__":
    run_audit()
