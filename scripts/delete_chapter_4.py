import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import SessionLocal
from app.models.course import Subject, Chapter, Topic, Subtopic, LearningUnit
from app.models.quiz import Question
from app.models.core.student import Student
from app.models.learning.student_mastery import StudentMastery
from app.models.learning.student_daily_learning import StudentDailyLearning
from app.models.assessment.learning_session import LearningSession
from app.models.assessment.student_response import StudentResponse

db = SessionLocal()
try:
    # 1. Find Chapter 4 "Exploring Magnets"
    chapter = db.query(Chapter).filter(Chapter.title.ilike('%Timeline and Sources of History%')).first()
    if not chapter:
        print("Chapter 'Timeline and Sources of History India' not found.")
        sys.exit(0)
        
    print(f"Found Chapter: {chapter.title} (ID: {chapter.id})")
    
    # Get all components
    topics = db.query(Topic).filter(Topic.chapter_id == chapter.id).all()
    topic_ids = [t.id for t in topics]
    
    subtopics = db.query(Subtopic).filter(Subtopic.topic_id.in_(topic_ids)).all() if topic_ids else []
    subtopic_ids = [s.id for s in subtopics]
    
    learning_units = db.query(LearningUnit).filter(LearningUnit.subtopic_id.in_(subtopic_ids)).all() if subtopic_ids else []
    lu_ids = [lu.id for lu in learning_units]
    
    questions = db.query(Question).filter(Question.learning_unit_id.in_(lu_ids)).all() if lu_ids else []
    question_ids = [q.id for q in questions]
    
    print(f"Found {len(topics)} topics, {len(subtopics)} subtopics, {len(learning_units)} learning units, and {len(questions)} questions to delete.")
    
    # 2. Delete Student Responses
    if question_ids:
        deleted_responses = db.query(StudentResponse).filter(StudentResponse.question_id.in_(question_ids)).delete(synchronize_session=False)
        print(f"Deleted {deleted_responses} student responses.")
        
    # 3. Delete Student Mastery records
    if lu_ids:
        deleted_masteries = db.query(StudentMastery).filter(StudentMastery.concept_id.in_(lu_ids)).delete(synchronize_session=False)
        print(f"Deleted {deleted_masteries} student mastery records.")
        
    # 4. Delete Student Daily Learning records
    if topic_ids:
        deleted_dl = db.query(StudentDailyLearning).filter(StudentDailyLearning.topic_id.in_(topic_ids)).delete(synchronize_session=False)
        print(f"Deleted {deleted_dl} student daily learning records.")
        
    # 5. Delete Questions
    if question_ids:
        deleted_questions = db.query(Question).filter(Question.id.in_(question_ids)).delete(synchronize_session=False)
        print(f"Deleted {deleted_questions} questions.")
        
    # 6. Delete Chapter (cascades to Topics, Subtopics, LearningUnits)
    db.delete(chapter)
    db.commit()
    print("Chapter deleted successfully.")
    
except Exception as e:
    db.rollback()
    print(f"Error during deletion: {e}")
finally:
    db.close()
