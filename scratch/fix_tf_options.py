import os
import json
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
RENDER_DB_URL = os.getenv("DATABASE_URL")
LOCAL_DB_URL = "postgresql://harshitdarji:admin123@localhost:5432/microlearning_db"

def fix_tf_questions(db_url, db_name):
    print(f"\n=== Fixing TRUE_FALSE Question Options in {db_name} ===")
    engine = create_engine(db_url)
    with engine.connect() as conn:
        # Get all TRUE_FALSE questions
        rows = conn.execute(text("""
            SELECT id, text, mcq_options, expected_answer, correct_option
            FROM questions
            WHERE question_type = 'TRUE_FALSE'
        """)).fetchall()
        
        updated_count = 0
        for r in rows:
            q_id, q_text, mcq_opts, exp_ans, corr_opt = r
            
            # Detect language
            is_hindi = any(ord(c) in range(0x0900, 0x097F) for c in q_text)
            is_gujarati = any(ord(c) in range(0x0A80, 0x0AFF) for c in q_text)
            
            if is_hindi:
                correct_options = ["हाँ (True)", "नहीं (False)"]
            elif is_gujarati:
                correct_options = ["સાચું (True)", "ખોટું (False)"]
            else:
                correct_options = ["True", "False"]
                
            # Check if expected_answer/correct_option is True-like or False-like
            ans_str = str(exp_ans or corr_opt).lower()
            if "हाँ" in ans_str or "true" in ans_str or "સાચું" in ans_str:
                correct_val = correct_options[0]
            else:
                correct_val = correct_options[1]
                
            # Perform update
            conn.execute(text("""
                UPDATE questions
                SET mcq_options = CAST(:opts AS jsonb),
                    correct_option = :correct,
                    expected_answer = :correct,
                    supported_answer_modes = ARRAY['MCQ']::varchar[],
                    evaluation_method = 'MCQ'
                WHERE id = :q_id
            """), {
                "opts": json.dumps(correct_options),
                "correct": correct_val,
                "q_id": q_id
            })
            updated_count += 1
            
        conn.commit()
        print(f"Successfully verified/fixed {updated_count} TRUE_FALSE questions in {db_name}.")

fix_tf_questions(RENDER_DB_URL, "Render DB")
fix_tf_questions(LOCAL_DB_URL, "Local DB")
