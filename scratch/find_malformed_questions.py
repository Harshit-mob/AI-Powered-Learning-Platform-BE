import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
RENDER_DB_URL = os.getenv("DATABASE_URL")
LOCAL_DB_URL = "postgresql://harshitdarji:admin123@localhost:5432/microlearning_db"

def inspect_questions(db_url, db_name):
    print(f"\n=== Inspecting Questions in {db_name} ===")
    engine = create_engine(db_url)
    with engine.connect() as conn:
        # 1. Non-MCQ questions containing "Which of these" / "Which of the following" / "Which one of"
        res_which = conn.execute(text("""
            SELECT id, text, question_type, expected_answer, mcq_options
            FROM questions
            WHERE (
                text ILIKE '%which of these%' OR
                text ILIKE '%which of the following%' OR
                text ILIKE '%which one of%' OR
                text ILIKE '%कौन सा%' OR
                text ILIKE '%कौन-सा%' OR
                text ILIKE '%कौनसी%'
            ) AND question_type NOT IN ('MCQ', 'TRUE_FALSE')
        """)).fetchall()
        
        print(f"Found {len(res_which)} non-MCQ questions with choice phrasing:")
        for r in res_which[:15]:
            print(f"  - ID: {r[0]} | Type: {r[2]} | Answer: {r[3]} | Text: {r[1]}")
            
        # 2. FILL_BLANK questions containing parenthetical lists like (x/y)
        res_fb = conn.execute(text("""
            SELECT id, text, question_type, expected_answer
            FROM questions
            WHERE question_type = 'FILL_BLANK' AND text LIKE '%/%' AND text LIKE '%(%'
        """)).fetchall()
        
        print(f"\nFound {len(res_fb)} FILL_BLANK questions with slashes/parentheses:")
        for r in res_fb[:15]:
            print(f"  - ID: {r[0]} | Answer: {r[3]} | Text: {r[1]}")

inspect_questions(RENDER_DB_URL, "Render DB")
