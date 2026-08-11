import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

RENDER_DB_URL = os.getenv("DATABASE_URL")
LOCAL_DB_URL = "postgresql://harshitdarji:admin123@localhost:5432/microlearning_db"

def link_qbank(db_url, db_name):
    print(f"\nLinking and updating QBank for {db_name}...")
    engine = create_engine(db_url)
    
    ch_titles = [
        "How I Taught My Grandmother to Read",
        "The Incident of the Tooth",
        "Children of India",
        "सोनकंठी गौरैया",
        "ननिहाल",
        "संज्ञा",
        "संज्ञा के विकारिक तत्व",
        "Exploring Magnets"
    ]
    
    with engine.connect() as conn:
        for ch_title in ch_titles:
            # Get Chapter
            res = conn.execute(text("SELECT id, subject_id FROM chapters WHERE title = :title"), {"title": ch_title})
            ch = res.fetchone()
            if not ch:
                print(f"Chapter '{ch_title}' not found in {db_name}. Skipping.")
                continue
            ch_id, sub_id = ch
            
            # Get questions count
            q_res = conn.execute(text("""
                SELECT q.id
                FROM questions q
                JOIN learning_units lu ON lu.id = q.learning_unit_id
                JOIN subtopics st ON st.id = lu.subtopic_id
                JOIN topics tp ON tp.id = st.topic_id
                WHERE tp.chapter_id = :ch_id
            """), {"ch_id": ch_id})
            q_ids = [row[0] for row in q_res.fetchall()]
            
            print(f"Found {len(q_ids)} questions in {db_name} for '{ch_title}'.")
            if not q_ids:
                continue
            
            # Find or create QBank
            qb_res = conn.execute(text("SELECT id FROM question_banks WHERE chapter_id = :ch_id"), {"ch_id": ch_id})
            qb = qb_res.fetchone()
            
            if not qb:
                # Create
                import uuid
                qb_id = str(uuid.uuid4())
                conn.execute(text("""
                    INSERT INTO question_banks (id, subject_id, chapter_id, file_name, source_type, status, total_questions, created_at)
                    VALUES (:id, :subject_id, :chapter_id, :file_name, 'TEXTBOOK_EXERCISE', 'APPROVED', :total, now())
                """), {
                    "id": qb_id,
                    "subject_id": sub_id,
                    "chapter_id": ch_id,
                    "file_name": f"Textbook_Exercises_{ch_title.replace(' ', '_')}.pdf",
                    "total": len(q_ids)
                })
                print(f"Created new QuestionBank record in {db_name} for '{ch_title}' (ID: {qb_id}).")
            else:
                qb_id = qb[0]
                # Update
                conn.execute(text("""
                    UPDATE question_banks
                    SET status = 'APPROVED', total_questions = :total, subject_id = :sub_id
                    WHERE id = :qb_id
                """), {
                    "total": len(q_ids),
                    "sub_id": sub_id,
                    "qb_id": qb_id
                })
                print(f"Updated existing QuestionBank record in {db_name} for '{ch_title}' (ID: {qb_id}).")
                
            # Link questions
            linked = conn.execute(text("""
                UPDATE questions
                SET question_bank_id = :qb_id
                WHERE id IN :q_ids
            """), {"qb_id": qb_id, "q_ids": tuple(q_ids)})
            print(f"Linked {linked.rowcount} questions to QuestionBank.")
            
        conn.commit()

link_qbank(RENDER_DB_URL, "Render DB")
link_qbank(LOCAL_DB_URL, "Local DB")
print("\nDone linking QBank records.")
