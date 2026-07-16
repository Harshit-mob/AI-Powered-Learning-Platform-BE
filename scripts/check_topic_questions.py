import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine, text
from app.core.config import settings
import uuid

def main():
    engine = create_engine(settings.DATABASE_URL)
    topic_id = '0ec69a28-0f7d-4fe0-b78b-68c62f5c952c'
    
    with engine.connect() as conn:
        # Check questions in this topic
        query = text("""
            SELECT q.id, q.learning_unit_id 
            FROM questions q
            JOIN learning_units lu ON q.learning_unit_id = lu.id
            JOIN subtopics st ON lu.subtopic_id = st.id
            JOIN topics t ON st.topic_id = t.id
            WHERE t.id = :topic_id
        """)
        questions = conn.execute(query, {"topic_id": topic_id}).fetchall()
        print(f"Total questions mapped to topic {topic_id}: {len(questions)}")

if __name__ == "__main__":
    main()
