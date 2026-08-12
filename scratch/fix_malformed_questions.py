import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
RENDER_DB_URL = os.getenv("DATABASE_URL")
LOCAL_DB_URL = "postgresql://harshitdarji:admin123@localhost:5432/microlearning_db"

def fix_questions(db_url, db_name):
    print(f"\n=== Fixing Questions in {db_name} ===")
    engine = create_engine(db_url)
    with engine.connect() as conn:
        # Fix 1: Update "Which of these is the positive degree of 'most beautiful'?"
        r1 = conn.execute(text("""
            UPDATE questions
            SET text = 'What is the positive degree of ''most beautiful''?'
            WHERE text = 'Which of these is the positive degree of ''most beautiful''?'
        """))
        
        # Fix 2: Update "Fill in the blank: The ___ (small/blue) bag is mine."
        r2 = conn.execute(text("""
            UPDATE questions
            SET text = 'Fill in the blank: The ___ (small blue/big red) bag is mine.'
            WHERE text = 'Fill in the blank: The ___ (small/blue) bag is mine.'
        """))
        
        conn.commit()
        print(f"Updated {r1.rowcount} positive degree questions.")
        print(f"Updated {r2.rowcount} bag color questions.")

# Run fix on both
fix_questions(RENDER_DB_URL, "Render DB")
fix_questions(LOCAL_DB_URL, "Local DB")
