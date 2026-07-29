import os
import sys
import json
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.content.ai_provider import default_ai_provider
from app.content.question_generator import QuestionGenerationService
from app.database.session import SessionLocal
from app.models.course import Chapter
from app.models.quiz import Question

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger(__name__)

def generate_questions_for_chapter(chapter_title):
    print(f"\n=== Starting Question Generation for Chapter: {chapter_title} ===")
    
    db = SessionLocal()
    try:
        # 1. Fetch Chapter
        print("\n[1/3] Fetching Chapter and Learning Units...")
        chapter = db.query(Chapter).filter(Chapter.title == chapter_title).first()
        
        if not chapter:
            # Try partial match
            chapter = db.query(Chapter).filter(Chapter.title.ilike(f"%{chapter_title}%")).first()
            
        if not chapter:
            print(f"Error: Chapter '{chapter_title}' not found in the database.")
            return
            
        subject = chapter.subject
        grade = subject.grade
        board = grade.board
        
        print(f"Context: {board.name} | Grade {grade.name} | {subject.name} | {chapter.title}")
        
        # 2. Generate Questions
        generator = QuestionGenerationService(ai_provider=default_ai_provider)
        
        all_questions = []
        total_generated = 0
        total_validated = 0
        total_failures = 0
        total_time = 0
        quality_reports = []
        
        print("\n[2/3] Generating & Validating Questions for all Learning Units...")
        
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

        # 3. Save Questions to Database
        print("\n[3/3] Saving Questions to Database...")
        saved_count = generator.save_question_bank(all_questions, db)
        print(f"Successfully saved {saved_count} questions to the database.")
        
        # Cleanup Learning Units, Subtopics, and Topics with 0 questions under this chapter
        print("\n[Cleanup] Removing learning units, subtopics, and topics with 0 questions...")
        from app.models.course import Topic, Subtopic, LearningUnit
        
        # 1. Delete learning units with 0 questions under this chapter
        lus_to_delete = db.query(LearningUnit).filter(
            LearningUnit.subtopic.has(Subtopic.topic.has(chapter_id=chapter.id))
        ).filter(
            ~LearningUnit.questions.any()
        ).all()
        for lu in lus_to_delete:
            db.delete(lu)
        db.flush()
        
        # 2. Delete subtopics with 0 learning units left under this chapter
        subtopics_to_delete = db.query(Subtopic).filter(
            Subtopic.topic.has(chapter_id=chapter.id)
        ).filter(
            ~Subtopic.learning_units.any()
        ).all()
        for st in subtopics_to_delete:
            db.delete(st)
        db.flush()
        
        # 3. Delete topics with 0 subtopics left under this chapter
        topics_to_delete = db.query(Topic).filter(
            Topic.chapter_id == chapter.id
        ).filter(
            ~Topic.subtopics.any()
        ).all()
        for t in topics_to_delete:
            db.delete(t)
        db.commit()
        print("Cleanup completed successfully.")
        
        # Dump to questions_chapter.json
        print("\n[4/4] Dumping to generated/questions/ ...")
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        out_dir = os.path.join(base_dir, "generated", "questions")
        os.makedirs(out_dir, exist_ok=True)
        out_file = os.path.join(out_dir, f"questions_{chapter.id}.json")
        
        with open(out_file, "w") as f:
            json.dump([q.model_dump() for q in all_questions], f, indent=2)
            
        print(f"Successfully dumped to {out_file}")
        
    except Exception as e:
        print(f"\n[X] Question generation failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_chapter_questions.py <chapter_title>")
        sys.exit(1)
    generate_questions_for_chapter(sys.argv[1])
