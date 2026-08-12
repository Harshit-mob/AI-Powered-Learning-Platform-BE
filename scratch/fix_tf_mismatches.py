import os
import json
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
RENDER_DB_URL = os.getenv("DATABASE_URL")
LOCAL_DB_URL = "postgresql://harshitdarji:admin123@localhost:5432/microlearning_db"

def fix_tf_mismatches(db_url, db_name):
    print(f"\n=== Fixing TRUE_FALSE Mismatches in {db_name} ===")
    engine = create_engine(db_url)
    with engine.connect() as conn:
        # Get all questions that start with True or False variations
        rows = conn.execute(text("""
            SELECT id, text, expected_answer, correct_option
            FROM questions
            WHERE text ILIKE 'True or False:%'
               OR text ILIKE 'True/False:%'
               OR text ILIKE 'सत्य या असत्य:%'
               OR text ILIKE 'સાચું કે ખોટું:%'
        """)).fetchall()
        
        updated_count = 0
        for r in rows:
            q_id, q_text, exp_ans, corr_opt = r
            
            # Detect language
            is_hindi = any(ord(c) in range(0x0900, 0x097F) for c in q_text)
            is_gujarati = any(ord(c) in range(0x0A80, 0x0AFF) for c in q_text)
            
            if is_hindi:
                opts = ["हाँ (True)", "नहीं (False)"]
            elif is_gujarati:
                opts = ["સાચું (True)", "ખોટું (False)"]
            else:
                opts = ["True", "False"]
                
            ans_str = str(exp_ans or corr_opt).lower()
            if "हाँ" in ans_str or "true" in ans_str or "સાચું" in ans_str:
                correct_val = opts[0]
            else:
                correct_val = opts[1]
                
            conn.execute(text("""
                UPDATE questions
                SET question_type = 'TRUE_FALSE',
                    mcq_options = CAST(:opts AS jsonb),
                    correct_option = :correct,
                    expected_answer = :correct,
                    supported_answer_modes = ARRAY['MCQ']::varchar[],
                    evaluation_method = 'MCQ'
                WHERE id = :q_id
            """), {
                "opts": json.dumps(opts),
                "correct": correct_val,
                "q_id": q_id
            })
            updated_count += 1
            
        conn.commit()
        print(f"Successfully converted and fixed {updated_count} True/False questions in {db_name}.")

fix_tf_mismatches(RENDER_DB_URL, "Render DB")
fix_tf_mismatches(LOCAL_DB_URL, "Local DB")
