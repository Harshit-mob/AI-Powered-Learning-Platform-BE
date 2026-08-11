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

print(f"Syncing questions from Render DB: {RENDER_DB_URL}")
print(f"To Local DB: {LOCAL_DB_URL}")

render_engine = create_engine(RENDER_DB_URL)
local_engine = create_engine(LOCAL_DB_URL)

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

def sync_chapter_questions(ch_title):
    with render_engine.connect() as r_conn:
        # 1. Fetch questions from Render
        res = r_conn.execute(text("""
            SELECT q.id, q.learning_unit_id, q.question_type, q.concept, q.text, q.mcq_options, 
                   q.correct_option, q.answer_complexity, q.evaluation_method, q.learning_objective, 
                   q.keywords, q.difficulty, q.estimated_time, q.hint_level_1, q.hint_level_2, 
                   q.full_explanation, q.source_pages, q.supported_answer_modes, q.expected_answer, 
                   q.acceptable_answers, q.question_hash, q.bloom_level, q.cognitive_level, 
                   q.intent, q.voice_score, q.speaking_time, q.thinking_time, q.cluster_id, 
                   q.session_tags, q.production_score, q.coverage_weight, q.metadata_score, 
                   q.normalized_concept, q.cluster_name, q.question_purpose, q.progression_level, 
                   q.prerequisite_concepts, q.misconception_tags
            FROM chapters c
            JOIN topics t ON t.chapter_id = c.id
            JOIN subtopics st ON st.topic_id = t.id
            JOIN learning_units lu ON lu.subtopic_id = st.id
            JOIN questions q ON q.learning_unit_id = lu.id
            WHERE c.title = :title
        """), {"title": ch_title})
        questions = res.fetchall()
        
    if not questions:
        print(f"No questions found on Render for chapter '{ch_title}'.")
        return
        
    print(f"Found {len(questions)} questions on Render for '{ch_title}'. Syncing to local...")
    
    with local_engine.connect() as l_conn:
        # First, delete local responses/questions for this chapter to ensure clean state
        # Get learning unit IDs on local for this chapter title
        lu_res = l_conn.execute(text("""
            SELECT lu.id
            FROM chapters c
            JOIN topics t ON t.chapter_id = c.id
            JOIN subtopics st ON st.topic_id = t.id
            JOIN learning_units lu ON lu.subtopic_id = st.id
            WHERE c.title = :title
        """), {"title": ch_title})
        lu_ids = [row[0] for row in lu_res.fetchall()]
        
        if lu_ids:
            # Delete local responses
            l_conn.execute(text("""
                DELETE FROM student_responses 
                WHERE question_id IN (SELECT id FROM questions WHERE learning_unit_id IN :lu_ids)
            """), {"lu_ids": tuple(lu_ids)})
            # Delete local questions
            l_conn.execute(text("""
                DELETE FROM questions WHERE learning_unit_id IN :lu_ids
            """), {"lu_ids": tuple(lu_ids)})
            l_conn.commit()
            
        inserted_count = 0
        import json
        for q in questions:
            l_conn.execute(text("""
                INSERT INTO questions (
                    id, learning_unit_id, question_type, concept, text, mcq_options, 
                    correct_option, answer_complexity, evaluation_method, learning_objective, 
                    keywords, difficulty, estimated_time, hint_level_1, hint_level_2, 
                    full_explanation, source_pages, supported_answer_modes, expected_answer, 
                    acceptable_answers, question_hash, bloom_level, cognitive_level, 
                    intent, voice_score, speaking_time, thinking_time, cluster_id, 
                    session_tags, production_score, coverage_weight, metadata_score, 
                    normalized_concept, cluster_name, question_purpose, progression_level, 
                    prerequisite_concepts, misconception_tags
                ) VALUES (
                    :id, :learning_unit_id, :question_type, :concept, :text, :mcq_options, 
                    :correct_option, :answer_complexity, :evaluation_method, :learning_objective, 
                    :keywords, :difficulty, :estimated_time, :hint_level_1, :hint_level_2, 
                    :full_explanation, :source_pages, :supported_answer_modes, :expected_answer, 
                    :acceptable_answers, :question_hash, :bloom_level, :cognitive_level, 
                    :intent, :voice_score, :speaking_time, :thinking_time, :cluster_id, 
                    :session_tags, :production_score, :coverage_weight, :metadata_score, 
                    :normalized_concept, :cluster_name, :question_purpose, :progression_level, 
                    :prerequisite_concepts, :misconception_tags
                )
            """), {
                "id": q[0],
                "learning_unit_id": q[1], "question_type": q[2], "concept": q[3], "text": q[4], 
                "mcq_options": json.dumps(q[5]) if q[5] is not None else None,
                "correct_option": q[6], "answer_complexity": q[7], "evaluation_method": q[8], "learning_objective": q[9],
                "keywords": json.dumps(q[10]) if q[10] is not None else None, 
                "difficulty": q[11], "estimated_time": q[12], "hint_level_1": q[13], "hint_level_2": q[14],
                "full_explanation": q[15], 
                "source_pages": json.dumps(q[16]) if q[16] is not None else None, 
                "supported_answer_modes": q[17], 
                "expected_answer": q[18],
                "acceptable_answers": json.dumps(q[19]) if q[19] is not None else None, 
                "question_hash": q[20], "bloom_level": q[21], "cognitive_level": q[22],
                "intent": q[23], "voice_score": q[24], "speaking_time": q[25], "thinking_time": q[26], "cluster_id": q[27],
                "session_tags": q[28], 
                "production_score": q[29], "coverage_weight": q[30], "metadata_score": q[31],
                "normalized_concept": q[32], "cluster_name": q[33], "question_purpose": q[34], "progression_level": q[35],
                "prerequisite_concepts": q[36], 
                "misconception_tags": q[37]
            })
            inserted_count += 1
            
        l_conn.commit()
        print(f"Successfully synced {inserted_count} questions for '{ch_title}' to Local DB.")

for ch in ch_titles:
    sync_chapter_questions(ch)
