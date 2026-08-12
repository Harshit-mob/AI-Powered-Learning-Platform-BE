import os
import sys
import json
import re
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.content.ai_provider import default_ai_provider

load_dotenv()
RENDER_DB_URL = os.getenv("DATABASE_URL")
LOCAL_DB_URL = "postgresql://harshitdarji:admin123@localhost:5432/microlearning_db"

SYSTEM_PROMPT = """
You are an expert Educational Assessment QA AI. Your task is to convert a list of FILL_BLANK questions into MCQ (Multiple Choice Questions) with exactly 4 options.
For each question:
1. Rephrase the question text if necessary to be a clear question or a sentence with options next to the blank (e.g. "Which word completes...").
2. Generate exactly 4 believable options in `mcq_options`. One option must be the correct answer.
3. Set the `correct_option` and `expected_answer` to match the correct answer option character-for-character.

Input:
A JSON array of questions, each having:
- `id`: unique UUID
- `question`: question text
- `expected_answer`: correct answer

Output:
Return ONLY a valid JSON array of the converted questions containing exactly:
`id`, `question`, `expected_answer`, `mcq_options`, `correct_option`.

Do NOT return any markdown, comments, or explanations outside the JSON array.
"""

def convert_fill_blanks(db_url, db_name):
    print(f"\n=== Converting Social Science Fill-in-the-Blanks to MCQ in {db_name} ===")
    engine = create_engine(db_url)
    with engine.connect() as conn:
        # Get all FILL_BLANK questions for Social Science
        rows = conn.execute(text("""
            SELECT q.id, q.text, q.expected_answer
            FROM questions q
            JOIN learning_units lu ON lu.id = q.learning_unit_id
            JOIN subtopics st ON st.id = lu.subtopic_id
            JOIN topics tp ON tp.id = st.topic_id
            JOIN chapters c ON c.id = tp.chapter_id
            JOIN subjects s ON s.id = c.subject_id
            WHERE s.name = 'Social Science' AND q.question_type = 'FILL_BLANK'
        """)).fetchall()
        
        print(f"Found {len(rows)} FILL_BLANK questions in {db_name}.")
        if not rows:
            return
            
        input_list = []
        for r in rows:
            input_list.append({
                "id": str(r[0]),
                "question": r[1],
                "expected_answer": r[2]
            })
            
        # Call Gemini in chunks of 20
        chunk_size = 20
        updated_count = 0
        for i in range(0, len(input_list), chunk_size):
            chunk = input_list[i:i + chunk_size]
            payload_str = json.dumps(chunk, indent=2)
            
            try:
                raw_response = default_ai_provider.generate_text(system_prompt=SYSTEM_PROMPT, content=payload_str)
                match = re.search(r'\[.*\]', raw_response, re.DOTALL)
                if not match:
                    continue
                    
                converted = json.loads(match.group(0))
                for item in converted:
                    q_id = item.get("id")
                    mcq_options = item.get("mcq_options", [])
                    correct = item.get("correct_option")
                    
                    conn.execute(text("""
                        UPDATE questions
                        SET text = :text,
                            question_type = 'MCQ',
                            mcq_options = CAST(:mcq_options AS jsonb),
                            correct_option = :correct,
                            expected_answer = :correct,
                            supported_answer_modes = ARRAY['MCQ']::varchar[],
                            evaluation_method = 'MCQ'
                        WHERE id = :q_id
                    """), {
                        "text": item.get("question"),
                        "mcq_options": json.dumps(mcq_options),
                        "correct": correct,
                        "q_id": q_id
                    })
                    updated_count += 1
                    
            except Exception as e:
                print(f"Error processing chunk: {e}")
                continue
                
        conn.commit()
        print(f"Successfully converted {updated_count} FILL_BLANK questions to MCQ in {db_name}.")

def main():
    convert_fill_blanks(RENDER_DB_URL, "Render DB")
    convert_fill_blanks(LOCAL_DB_URL, "Local DB")

if __name__ == "__main__":
    main()
