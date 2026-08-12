import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
RENDER_DB_URL = os.getenv("DATABASE_URL")

engine = create_engine(RENDER_DB_URL)
with engine.connect() as conn:
    res = conn.execute(text("""
        SELECT q.id, q.text, q.question_type, q.expected_answer
        FROM questions q
        JOIN learning_units lu ON lu.id = q.learning_unit_id
        JOIN subtopics st ON st.id = lu.subtopic_id
        JOIN topics tp ON tp.id = st.topic_id
        JOIN chapters c ON c.id = tp.chapter_id
        WHERE c.title = 'How I Taught My Grandmother to Read' AND q.text ILIKE '%which%' AND q.question_type NOT IN ('MCQ', 'TRUE_FALSE')
    """)).fetchall()
    
    print(f"Found {len(res)} non-MCQ questions with 'which' in the English chapter:")
    for r in res:
        print(f"  - ID: {r[0]} | Type: {r[2]} | Answer: {r[3]} | Text: {r[1]}")
