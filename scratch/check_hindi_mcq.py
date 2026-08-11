from sqlalchemy import create_engine, text
import json

import os
from dotenv import load_dotenv

load_dotenv()
RENDER_DB_URL = os.getenv("DATABASE_URL")
engine = create_engine(RENDER_DB_URL)

with engine.connect() as conn:
    # Get all active Hindi questions
    res = conn.execute(text("""
        SELECT q.id, q.text, q.question_type, q.mcq_options, c.title as chapter_title
        FROM questions q
        JOIN learning_units lu ON lu.id = q.learning_unit_id
        JOIN subtopics st ON st.id = lu.subtopic_id
        JOIN topics tp ON tp.id = st.topic_id
        JOIN chapters c ON c.id = tp.chapter_id
        JOIN subjects s ON s.id = c.subject_id
        WHERE s.name = 'Hindi'
    """)).fetchall()
    
    print(f"Total Hindi questions found: {len(res)}")
    no_options = []
    invalid_tf = []
    
    for qid, qtext, qtype, qopts, ch_title in res:
        # qopts can be a string, list, or None
        options = qopts
        if isinstance(qopts, str):
            try:
                options = json.loads(qopts)
            except Exception:
                options = []
                
        if not options:
            no_options.append((qid, qtext, qtype, ch_title))
        elif qtype == "TRUE_FALSE" and len(options) != 2:
            invalid_tf.append((qid, qtext, len(options), ch_title))
            
    print(f"\nHindi questions missing MCQ options: {len(no_options)}")
    for qid, qtext, qtype, ch_title in no_options[:10]:
        print(f"  - ID: {qid} | Type: {qtype} | Chapter: {ch_title} | Text: {qtext[:60]}")
        
    print(f"\nHindi True/False questions with invalid option counts: {len(invalid_tf)}")
    for qid, qtext, count, ch_title in invalid_tf[:10]:
        print(f"  - ID: {qid} | Options: {count} | Chapter: {ch_title} | Text: {qtext[:60]}")
