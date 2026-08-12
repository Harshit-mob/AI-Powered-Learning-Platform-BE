import os
import sys
import json
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()
RENDER_DB_URL = os.getenv("DATABASE_URL")
LOCAL_DB_URL = "postgresql://harshitdarji:admin123@localhost:5432/microlearning_db"

def apply_updates(db_url, db_name, json_data):
    print(f"\n=== Applying Improvements to {db_name} ===")
    engine = create_engine(db_url)
    with engine.connect() as conn:
        update_count = 0
        for item in json_data:
            q_id = item.get("id")
            if not q_id:
                continue
                
            q_type = item.get("question_type", "MCQ")
            if q_type in ["MCQ", "TRUE_FALSE", "DEFINITION", "RECALL"]:
                modes = ["MCQ"]
                eval_method = "MCQ"
            elif q_type == "FILL_BLANK":
                modes = ["TEXT"]
                eval_method = "WORD_MATCH"
            else:
                modes = ["VOICE", "TEXT"]
                eval_method = "SEMANTIC_MATCH"
                
            mcq_options = item.get("mcq_options", [])
            acc_answers = item.get("acceptable_answers", [item.get("expected_answer")])
            
            res = conn.execute(text("""
                UPDATE questions
                SET text = :text,
                    expected_answer = :expected_answer,
                    mcq_options = CAST(:mcq_options AS jsonb),
                    correct_option = :correct_option,
                    acceptable_answers = CAST(:acceptable_answers AS jsonb),
                    hint_level_1 = :hint1,
                    hint_level_2 = :hint2,
                    full_explanation = :explanation,
                    supported_answer_modes = CAST(:modes AS varchar[]),
                    evaluation_method = :eval_method
                WHERE id = :q_id
            """), {
                "text": item.get("question"),
                "expected_answer": item.get("expected_answer"),
                "mcq_options": json.dumps(mcq_options),
                "correct_option": item.get("correct_option"),
                "acceptable_answers": json.dumps(acc_answers),
                "hint1": item.get("hint_level_1"),
                "hint2": item.get("hint_level_2"),
                "explanation": item.get("full_explanation"),
                "modes": modes,
                "eval_method": eval_method,
                "q_id": q_id
            })
            update_count += res.rowcount
            
        conn.commit()
        print(f"Successfully overwrote {update_count} questions in {db_name}.")

def main():
    json_path = "scratch/proposed_improvements.json"
    if not os.path.exists(json_path):
        print(f"Error: Proposed improvements file '{json_path}' not found! Run bulk_question_improver.py first.")
        return
        
    with open(json_path, "r") as f:
        json_data = json.load(f)
        
    print(f"Loaded {len(json_data)} approved improvements.")
    
    # Confirm
    confirm = input("Are you sure you want to write these changes to the databases? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("Aborted.")
        return
        
    apply_updates(RENDER_DB_URL, "Render DB", json_data)
    apply_updates(LOCAL_DB_URL, "Local DB", json_data)
    print("\nComplete! All approved questions updated.")

if __name__ == "__main__":
    main()
