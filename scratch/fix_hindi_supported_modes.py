import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()
RENDER_DB_URL = os.getenv("DATABASE_URL")
LOCAL_DB_URL = "postgresql://harshitdarji:admin123@localhost:5432/microlearning_db"

def fix_supported_modes(db_url, db_name):
    print(f"\nFixing supported_answer_modes in {db_name}...")
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        # Update both Hindi and Gujarati questions to have strictly ['MCQ'] as supported_answer_modes
        res = conn.execute(text("""
            UPDATE questions
            SET supported_answer_modes = ARRAY['MCQ']::varchar[]
            WHERE id IN (
                SELECT q.id
                FROM questions q
                JOIN learning_units lu ON lu.id = q.learning_unit_id
                JOIN subtopics st ON st.id = lu.subtopic_id
                JOIN topics tp ON tp.id = st.topic_id
                JOIN chapters c ON c.id = tp.chapter_id
                JOIN subjects s ON s.id = c.subject_id
                WHERE s.name IN ('Hindi', 'Gujarati')
            )
        """))
        
        conn.commit()
        print(f"Updated {res.rowcount} questions in {db_name}.")

# Fix both
fix_supported_modes(RENDER_DB_URL, "Render DB")
fix_supported_modes(LOCAL_DB_URL, "Local DB")
