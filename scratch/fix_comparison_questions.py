import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
RENDER_DB_URL = os.getenv("DATABASE_URL")
LOCAL_DB_URL = "postgresql://harshitdarji:admin123@localhost:5432/microlearning_db"

def fix_comparison_questions(db_url, db_name):
    print(f"\n=== Fixing Comparison Questions in {db_name} ===")
    engine = create_engine(db_url)
    with engine.connect() as conn:
        # Fix 1: Cat size comparison
        res1 = conn.execute(text("""
            UPDATE questions
            SET text = 'Riya notices that her cat is ____ (bigger/smaller) than her dog.'
            WHERE text = 'Riya notices that her cat is ____ than her dog. (Fill in with the correct form of ''big'')'
        """))
        
        # Fix 2: House size comparison
        res2 = conn.execute(text("""
            UPDATE questions
            SET text = 'Sam says, ''My house is the ____ (largest/larger) one in the street.'''
            WHERE text = 'Sam says, ''My house is the ____ one in the street.'' (Fill in with ''large'')'
        """))
        
        conn.commit()
        print(f"Updated {res1.rowcount} cat size questions.")
        print(f"Updated {res2.rowcount} house size questions.")

fix_comparison_questions(RENDER_DB_URL, "Render DB")
fix_comparison_questions(LOCAL_DB_URL, "Local DB")
