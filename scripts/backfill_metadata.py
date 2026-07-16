import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import SessionLocal
from app.models.quiz import Question
from app.services.content.question_intelligence.intelligence_engine import IntelligenceEngine

def backfill():
    db = SessionLocal()
    engine = IntelligenceEngine()
    questions = db.query(Question).all()
    print(f"Found {len(questions)} questions to backfill.")
    
    updated = 0
    for q in questions:
        # Convert DB object to dictionary suitable for the intelligence engine
        q_dict = {
            "question": q.text,
            "question_type": q.question_type,
            "concept": q.concept,
            "expected_answer": q.expected_answer,
            "difficulty": q.difficulty,
            "learning_unit_id": str(q.learning_unit_id) if q.learning_unit_id else "",
            "mcq_options": q.mcq_options,
            "correct_option": q.correct_option,
            "evaluation_method": q.evaluation_method,
            "answer_complexity": q.answer_complexity,
            "keywords": q.keywords or []
        }
        
        # We need the LearningUnit keywords for prerequisites
        unit_dict = None
        if q.learning_unit:
            unit_dict = {
                "keywords": q.learning_unit.keywords or []
            }
            
        # Re-run the engine
        try:
            intel = engine.enrich_question(q_dict, 100, unit_dict)
        except ValueError as e:
            print(f"Skipping Q {q.id}: {e}")
            continue
        
        # Update DB fields
        q.coverage_weight = intel.coverage_weight
        q.metadata_score = intel.metadata_score
        q.estimated_time = intel.estimated_time
        q.normalized_concept = intel.normalized_concept
        q.cluster_name = intel.cluster_name
        q.question_purpose = intel.question_purpose
        q.progression_level = intel.progression_level
        q.prerequisite_concepts = intel.prerequisite_concepts
        q.misconception_tags = intel.misconception_tags
        q.supported_answer_modes = intel.supported_answer_modes
        q.session_tags = intel.session_tags
        
        updated += 1
        
    db.commit()
    print(f"Successfully backfilled {updated} questions!")
    db.close()

if __name__ == "__main__":
    backfill()
