import os
import sys
import json
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.content.ai_provider import default_ai_provider
from app.services.content.question_generator import QuestionGenerationService
from app.database.session import SessionLocal
from app.models.course import Chapter
from app.models.quiz import Question

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger(__name__)

def regenerate():
    print("\n=== Starting Complete Regeneration of Chapter 1 Questions ===")
    
    db = SessionLocal()
    try:
        # 1. Delete all existing questions
        print("\n[1/4] Deleting existing questions from the database...")
        deleted_count = db.query(Question).delete()
        db.commit()
        print(f"Deleted {deleted_count} questions.")
        
        # 2. Fetch Chapter 1
        print("\n[2/4] Fetching Chapter 1 and Learning Units...")
        chapter = db.query(Chapter).first()
        
        if not chapter:
            print("Error: No Chapter found in the database.")
            return
            
        subject = chapter.subject
        grade = subject.grade
        board = grade.board
        
        print(f"Context: {board.name} | Grade {grade.name} | {subject.name} | {chapter.title}")
        
        # 3. Generate Questions
        generator = QuestionGenerationService(ai_provider=default_ai_provider)
        
        all_questions = []
        total_generated = 0
        total_validated = 0
        total_failures = 0
        total_time = 0
        quality_reports = []
        
        print("\n[3/4] Generating & Validating Questions for all Learning Units...")
        
        for topic in chapter.topics:
            for subtopic in topic.subtopics:
                if not subtopic.learning_units:
                    continue
                
                db_units = subtopic.learning_units
                subset = [
                    {
                        "id": str(lu.id),
                        "title": lu.title,
                        "learning_objective": lu.learning_objective,
                        "content": lu.content,
                        "keywords": lu.keywords,
                        "difficulty": lu.difficulty,
                        "source_pages": lu.source_pages
                    } for lu in db_units
                ]
                
                print(f"\nProcessing Subtopic: '{subtopic.title}' with {len(subset)} units...")
                stats = generator.generate_question_bank(
                    subject=subject.name,
                    grade=int(grade.name) if grade.name.isdigit() else 6,
                    board=board.name,
                    chapter=chapter.title,
                    topic=topic.title,
                    sub_topic=subtopic.title,
                    learning_units=subset
                )
                
                all_questions.extend(stats["questions"])
                total_generated += stats["total_generated"]
                total_validated += stats["total_validated"]
                total_failures += stats["total_failures_or_dupes"]
                total_time += stats["execution_time_seconds"]
                quality_reports.append(stats.get("quality_report", ""))

        print("\n[4/4] Saving Questions to Database...")
        saved_count = generator.save_question_bank(all_questions, db)
        print(f"Successfully saved {saved_count} questions to the database.")
        
        # Dump to questions.json
        print("\n[4/4] Dumping to questions.json...")
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        out_dir = os.path.join(base_dir, "generated", "questions")
        os.makedirs(out_dir, exist_ok=True)
        out_file = os.path.join(out_dir, "questions.json")
        
        with open(out_file, "w") as f:
            json.dump([q.model_dump() for q in all_questions], f, indent=2)
            
        print(f"Successfully dumped to {out_file}")
        
    except Exception as e:
        print(f"\n[X] Question generation failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    regenerate()
