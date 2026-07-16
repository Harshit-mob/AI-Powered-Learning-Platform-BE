import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import SessionLocal
from app.models.quiz import Question
from app.services.content.question_intelligence.intelligence_engine import IntelligenceEngine

def audit():
    db = SessionLocal()
    engine = IntelligenceEngine()
    questions = db.query(Question).all()
    print(f"Auditing {len(questions)} questions...\n")
    
    stats = {"PASS": 0, "REPAIRED": 0, "REJECTED": 0}
    
    for q in questions:
        q_dict = {
            "question": q.text,
            "text": q.text,
            "question_type": q.question_type,
            "concept": q.concept,
            "expected_answer": q.expected_answer,
            "difficulty": q.difficulty,
            "learning_unit_id": str(q.learning_unit_id) if q.learning_unit_id else "",
            "mcq_options": q.mcq_options,
            "correct_option": q.correct_option,
            "evaluation_method": q.evaluation_method,
            "answer_complexity": q.answer_complexity,
            "keywords": q.keywords or [],
            "hint_level_1": q.hint_level_1,
            "hint_level_2": q.hint_level_2,
            "full_explanation": q.full_explanation,
            "acceptable_answers": q.acceptable_answers or []
        }
        
        unit_dict = None
        if q.learning_unit:
            unit_dict = {
                "keywords": q.learning_unit.keywords or [],
                "learning_objective": q.learning_unit.learning_objective
            }
            
        print(f"--- Question ID: {q.id} ---")
        try:
            intel = engine.enrich_question(q_dict, 100, unit_dict)
            # If we get here, it means is_valid is True inside intelligence_engine
            # But we want to know if repairs/warnings happened. 
            # In our current engine, validate() returns warns, but enrich_question doesn't return warns, just the intel object.
            # To get warns, we'll manually call validator just for the report.
            is_valid, _, warns = engine.validator.validate(intel, q_dict, unit_dict)
            
            if not is_valid:
                print("Final Decision: REJECTED")
                print(f"Reason: {warns}")
                stats["REJECTED"] += 1
            else:
                if warns:
                    print("Final Decision: REPAIRED")
                    print(f"Score: {intel.metadata_score}")
                    print(f"Warnings/Repairs:\n{warns}")
                    stats["REPAIRED"] += 1
                else:
                    print("Final Decision: PASS")
                    print(f"Score: {intel.metadata_score}")
                    print("Warnings:\nNone")
                    stats["PASS"] += 1
                    
        except ValueError as e:
            print("Final Decision: REJECTED")
            print(f"Reason: {e}")
            stats["REJECTED"] += 1
            
        print("\n")
        
    print("=== AUDIT SUMMARY ===")
    print(f"Total: {len(questions)}")
    print(f"PASS: {stats['PASS']}")
    print(f"REPAIRED: {stats['REPAIRED']}")
    print(f"REJECTED: {stats['REJECTED']}")
    
    db.close()

if __name__ == "__main__":
    audit()
