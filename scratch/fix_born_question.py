import os
import json
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
RENDER_DB_URL = os.getenv("DATABASE_URL")
LOCAL_DB_URL = "postgresql://harshitdarji:admin123@localhost:5432/microlearning_db"

def fix_born_question(db_url, db_name):
    print(f"\n=== Fixing Born Question in {db_name} ===")
    engine = create_engine(db_url)
    with engine.connect() as conn:
        res = conn.execute(text("""
            UPDATE questions
            SET text = 'Fill in the blank: Sudha Murty ______ (was/is) born in 1950.',
                expected_answer = 'was',
                acceptable_answers = CAST(:acc_json AS jsonb)
            WHERE text = 'Fill in the blank: Sudha Murty ______ (born) in 1950.'
        """), {
            "acc_json": json.dumps(["was", "was born"])
        })
        conn.commit()
        print(f"Updated {res.rowcount} questions in {db_name}.")

fix_born_question(RENDER_DB_URL, "Render DB")
fix_born_question(LOCAL_DB_URL, "Local DB")
