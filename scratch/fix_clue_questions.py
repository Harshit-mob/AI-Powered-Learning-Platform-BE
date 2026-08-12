import os
import json
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
RENDER_DB_URL = os.getenv("DATABASE_URL")
LOCAL_DB_URL = "postgresql://harshitdarji:admin123@localhost:5432/microlearning_db"

def fix_clue_questions(db_url, db_name):
    print(f"\n=== Fixing Clue Questions in {db_name} ===")
    engine = create_engine(db_url)
    with engine.connect() as conn:
        res = conn.execute(text("""
            UPDATE questions
            SET text = 'Tom felt deep ______ (misery/happiness) on Monday mornings.',
                expected_answer = 'misery',
                acceptable_answers = CAST(:acc_json AS jsonb)
            WHERE text LIKE 'Tom felt deep % on Monday mornings.%'
        """), {
            "acc_json": json.dumps(["misery", "Misery"])
        })
        conn.commit()
        print(f"Updated {res.rowcount} questions in {db_name}.")

fix_clue_questions(RENDER_DB_URL, "Render DB")
fix_clue_questions(LOCAL_DB_URL, "Local DB")
