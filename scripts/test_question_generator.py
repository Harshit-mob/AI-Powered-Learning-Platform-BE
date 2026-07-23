import os
import sys
import json
import logging

# Add the project root to the sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.content.ai_provider import default_ai_provider
from app.content.question_generator import QuestionGenerationService

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger(__name__)

def test_question_generation():
    """
    Dry-run orchestrator to test the Refactored Question Generation module independently.
    It reads existing learning units from disk, passes them through the robust
    AI payload builder, generates via string-parsing, validates them, and saves the output JSON.
    """
    
    print("\n=== Starting Refactored Question Generation Pipeline ===")
    
    # 1. Load Learning Units from PostgreSQL
    from app.database.session import SessionLocal
    from app.models.course import Chapter
    
    db = SessionLocal()
    try:
        print("\n[1/3] Fetching Chapter 1 and its Learning Units from the database...")
        chapter = db.query(Chapter).first()
        
        if not chapter:
            print("Error: No Chapter found in the database. Run the main pipeline first.")
            return
            
        subject = chapter.subject
        grade = subject.grade
        board = grade.board
        
        print(f"Context: {board.name} | Grade {grade.name} | {subject.name} | {chapter.title}")
        
        # 2. Initialize the Generator
        generator = QuestionGenerationService(ai_provider=default_ai_provider)
        
        all_questions = []
        total_generated = 0
        total_validated = 0
        total_failures = 0
        total_time = 0
        quality_reports = []
        
        # 3. Generate Questions
        print("\n[2/3] Generating & Validating Questions (Batching Strategy Active)...")
        
        for topic in chapter.topics:
            for subtopic in topic.subtopics:
                if not subtopic.learning_units:
                    continue
                
                db_units = subtopic.learning_units[:1] # ONLY ONE UNIT
                test_subset = [
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
                
                print(f"\nProcessing Subtopic: '{subtopic.title}' with {len(test_subset)} units...")
                stats = generator.generate_question_bank(
                    subject=subject.name,
                    grade=int(grade.name) if grade.name.isdigit() else 6,
                    board=board.name,
                    chapter=chapter.title,
                    topic=topic.title,
                    sub_topic=subtopic.title,
                    learning_units=test_subset
                )
                
                all_questions.extend(stats["questions"])
                total_generated += stats["total_generated"]
                total_validated += stats["total_validated"]
                total_failures += stats["total_failures_or_dupes"]
                total_time += stats["execution_time_seconds"]
                quality_reports.append(stats.get("quality_report", ""))
                break # ONLY ONE SUBTOPIC
            break # ONLY ONE TOPIC

        print("\n[3/4] Saving Questions to Database...")
        saved_count = generator.save_question_bank(all_questions, db)
        print(f"Successfully saved {saved_count} questions to the database.")
    except Exception as e:
        print(f"\n[X] Question generation failed: {e}")
        return
    finally:
        db.close()
        
    # 4. Save Output Artifact
    print("\n[4/4] Saving Output...")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(base_dir, "generated", "questions")
    os.makedirs(out_dir, exist_ok=True)
    
    out_file = os.path.join(out_dir, "questions.json")
    with open(out_file, "w") as f:
        # Dump the valid questions
        json.dump([q.model_dump() for q in all_questions], f, indent=2)
        
    # --- SUMMARY ---
    for report in quality_reports:
        print("\n" + report)
        
    print(f"Total Time Elapsed:          {total_time:.2f} seconds")
    print(f"Artifact Saved At:           {out_file}")
    print("="*49 + "\n")


if __name__ == "__main__":
    test_question_generation()
