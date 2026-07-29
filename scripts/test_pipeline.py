import sys
import os
import time
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.content.loader import ContentLoader
from app.content.ocr_service import OCRService
from app.content.pdf_extractor import PDFExtractor
from app.content.cleaner import ContentCleaner
from app.content.normalizer import ContentNormalizer
from app.content.validator import ContentValidator
from app.content.ai_provider import default_ai_provider, BatchManager, TokenEstimator
from app.content.curriculum_parser import CurriculumParser
from app.content.learning_unit_builder import LearningUnitBuilder
from app.content.importer import ContentImporter
from app.database.session import SessionLocal, engine
from app.models.course import Base
# Import other models so SQLAlchemy maps relationships correctly
from app.models.quiz import Question
from app.models.core.student import Student
from app.models.learning.student_mastery import StudentMastery
from app.models.learning.student_daily_learning import StudentDailyLearning
from app.models.assessment.learning_session import LearningSession
from app.models.assessment.student_response import StudentResponse

def test_pipeline():
    start_time = time.time()
    
    # Track metrics
    ai_request_count = 0
    total_tokens_estimated = 0
    total_learning_units = 0
    
    # 0. Setup DB
    Base.metadata.create_all(bind=engine)
    
    # Accept PDF path from command-line arguments, default to chapter_1.pdf
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "content/cbse/grade_6/science/chapter_1/chapter_1.pdf"
    print(f"\n=== Starting Optimized AI Content Pipeline for: {pdf_path} ===")
    
    if not os.path.exists(pdf_path):
        print(f"Error: File does not exist at {pdf_path}")
        return
        
    # Step 1: Loader
    print("\n[1/6] Loading content metadata...")
    loader = ContentLoader()
    metadata = loader.load(pdf_path)
    metadata_hints = {
        "board": metadata.board,
        "grade": metadata.grade,
        "subject": metadata.subject,
        "chapter_number": metadata.chapter_number,
        "chapter_title": metadata.chapter_title
    }
    
    ocr_service = OCRService()
    extractor = PDFExtractor(ocr_service=ocr_service)
    cleaner = ContentCleaner()
    normalizer = ContentNormalizer()
    validator = ContentValidator()
    
    # Step 2: Extraction
    print("\n[2/6] Extracting text/images...")
    ocr_start = time.time()
    pages = extractor.extract(pdf_path)
    ocr_end = time.time()
    print(f"Extracted {len(pages)} pages.")
    
    # Option A page filtering for Hindi/Gujarati
    meta_json_path = os.path.join(os.path.dirname(pdf_path), "metadata.json")
    if os.path.exists(meta_json_path):
        try:
            with open(meta_json_path, 'r', encoding='utf-8') as f:
                meta_data = json.load(f)
                glossary_pages = meta_data.get("glossary_pages", [])
                assignment_pages = meta_data.get("assignment_pages", [])
                if (glossary_pages or assignment_pages) and metadata.subject.lower() in ("hindi", "gujarati"):
                    target_pages = set(glossary_pages + assignment_pages)
                    print(f"\n[Option A] Filtering extraction to target pages: {sorted(list(target_pages))}")
                    pages = [p for p in pages if p.page_number in target_pages]
                    print(f"Filtered pages count: {len(pages)}")
        except Exception as e:
            print(f"Warning: Failed to load/parse metadata.json for page filtering: {e}")
    
    # Step 3: Cleaning & Normalization
    print("\n[3/6] Cleaning and Normalizing text...")
    norm_start = time.time()
    cleaned_text = cleaner.clean(pages)
    normalized_text, norm_stats = normalizer.normalize(cleaned_text)
    norm_end = time.time()
    
    is_valid, val_report = validator.validate(normalized_text)
    if not is_valid:
        print("Validation Failed! See report.")
        print(json.dumps(val_report, indent=2))
        return
    
    # Step 4: Curriculum Parsing (AI Request #1)
    print("\n[4/6] AI Request #1: Parsing Curriculum Structure (Batch)...")
    curriculum_parser = CurriculumParser(ai_provider=default_ai_provider)
    
    input_tokens = TokenEstimator.estimate_tokens(normalized_text)
    total_tokens_estimated += input_tokens
    print(f"Estimated Input Tokens: {input_tokens}")
    
    parsed_curriculum = curriculum_parser.parse(normalized_text, metadata_hints=metadata_hints)
    ai_request_count += 1
    
    # Step 5: Learning Unit Generation (AI Request #2)
    print("\n[5/6] AI Request #2: Building Learning Units (Batch)...")
    unit_builder = LearningUnitBuilder(ai_provider=default_ai_provider)
    
    # Use BatchManager to split only if it exceeds e.g. 500,000 tokens (Gemini handles 1M comfortably)
    def serialize_topic(topic):
        return topic.model_dump_json()
        
    batches = BatchManager.create_batches(
        items=parsed_curriculum.chapter.topics,
        max_tokens=500000, 
        serialize_func=serialize_topic
    )
    
    print(f"Divided curriculum into {len(batches)} optimal batch(es).")
    
    all_learning_units = []
    
    for idx, batch in enumerate(batches):
        print(f"  -> Processing Batch {idx + 1}/{len(batches)}...")
        batch_json = json.dumps([t.model_dump() for t in batch])
        
        batch_tokens = TokenEstimator.estimate_tokens(batch_json)
        total_tokens_estimated += batch_tokens
        print(f"  -> Estimated Batch Tokens: {batch_tokens}")
        
        units = unit_builder.build_from_curriculum(batch_json)
        all_learning_units.extend(units)
        ai_request_count += 1
        
    total_learning_units = len(all_learning_units)
            
    # Step 6: Import to DB
    print("\n[6/6] Importing structured content to PostgreSQL...")
    importer = ContentImporter()
    db = SessionLocal()
    total_units_inserted = 0
    try:
        db_chapter = importer.import_curriculum(db, parsed_curriculum)
        
        # Quick map of subtopic titles to DB IDs
        subtopic_id_map = {}
        for db_topic in db_chapter.topics:
            for db_subtopic in db_topic.subtopics:
                subtopic_id_map[db_subtopic.title] = db_subtopic.id
                
        # Group generated units by subtopic_id
        units_by_subtopic_id = {}
        for unit in all_learning_units:
            sub_id = subtopic_id_map.get(unit.subtopic_title)
            if sub_id:
                if sub_id not in units_by_subtopic_id:
                    units_by_subtopic_id[sub_id] = []
                units_by_subtopic_id[sub_id].append(unit)
            else:
                print(f"Warning: Could not map generated unit '{unit.title}' to any Subtopic.")
                
        # Insert them
        for sub_id, units in units_by_subtopic_id.items():
            inserted = importer.import_learning_units(db, sub_id, units)
            total_units_inserted += len(inserted)
            
        print(f"Successfully inserted Curriculum and {total_units_inserted} Learning Units.")
        
        # Cleanup Empty Topics & Subtopics
        print("\n[Cleanup] Removing topics and subtopics with 0 learning units...")
        from app.models.course import Topic, Subtopic
        
        # Delete subtopics with 0 learning units under this chapter
        subtopics_to_delete = db.query(Subtopic).filter(
            Subtopic.topic.has(chapter_id=db_chapter.id)
        ).filter(
            ~Subtopic.learning_units.any()
        ).all()
        for st in subtopics_to_delete:
            db.delete(st)
        db.flush()
        
        # Delete topics with 0 subtopics under this chapter
        topics_to_delete = db.query(Topic).filter(
            Topic.chapter_id == db_chapter.id
        ).filter(
            ~Topic.subtopics.any()
        ).all()
        for t in topics_to_delete:
            db.delete(t)
            
        db.commit()
        print("Cleanup completed successfully.")
    finally:
        db.close()
        
    # Save Generated Artifacts
    print("\n[Saving Output Artifacts to generated/ ...]")
    gen_dir = os.path.join(os.path.dirname(__file__), "..", "generated")
    os.makedirs(os.path.join(gen_dir, "curriculum"), exist_ok=True)
    os.makedirs(os.path.join(gen_dir, "learning_units"), exist_ok=True)
    os.makedirs(os.path.join(gen_dir, "future_questions"), exist_ok=True)
    
    with open(os.path.join(gen_dir, "curriculum", "parsed_curriculum.json"), "w") as f:
        f.write(parsed_curriculum.model_dump_json(indent=2))
        
    with open(os.path.join(gen_dir, "learning_units", "learning_units.json"), "w") as f:
        json.dump([u.model_dump() for u in all_learning_units], f, indent=2)
    
    end_time = time.time()
    
    # Final Validation Summary exactly as requested
    print("\n=== PIPELINE VALIDATION SUMMARY ===")
    print(f"OCR Time: {ocr_end - ocr_start:.2f} seconds")
    print(f"Normalization Time: {norm_end - norm_start:.2f} seconds")
    print(f"AI Requests: {ai_request_count}")
    print(f"Tokens Estimated: {total_tokens_estimated}")
    print(f"Learning Units Generated: {total_learning_units}")
    print(f"Database Inserts: Curriculum Tree + {total_units_inserted} Units")
    print(f"Warnings: {len(val_report['warnings'])}")
    print("Errors: 0")
    print(f"Execution Time: {end_time - start_time:.2f} seconds")
    print("===================================\n")

if __name__ == "__main__":
    test_pipeline()
