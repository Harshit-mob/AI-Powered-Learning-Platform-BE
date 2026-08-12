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
engine = create_engine(RENDER_DB_URL)

SYSTEM_PROMPT = """
You are an expert Educational Assessment QA AI. Your task is to review and improve a batch of questions from a specific chapter.
For each question in the input list, you must inspect and improve the following fields:
1. `question`: Refine the phrasing.
   - For MCQ, DEFINITION, and RECALL questions: If the text contains choice-identifying phrasing (like "Which...", "In the sentence '...', which..."), make sure it sounds natural and clearly asks for a choice.
   - For FILL_BLANK: If there are choices in parentheses, they must represent complete, alternative choices (e.g. "Sudha Murty ______ (was/is) born in 1950" or "____ (bigger/smaller)"), not partial fragments (like "(small/blue)").
2. `question_type`: Ensure it matches the format:
   - MCQ, TRUE_FALSE, DEFINITION, and RECALL questions MUST have exactly 4 options in `mcq_options` (or 2 options for TRUE_FALSE), and their `supported_answer_modes` MUST be exactly `["MCQ"]`.
   - If a question has choice phrasing, it MUST be converted to `MCQ`.
3. `mcq_options`: Ensure it contains exactly 4 plausible choices (or 2 choices for TRUE_FALSE).
4. `correct_option` and `expected_answer`: Ensure they are identical character-for-character to one of the options in `mcq_options`.
5. `acceptable_answers`: Add common spoken synonyms or alternative phrasings (especially for FILL_BLANK or voice-friendly questions). No trailing punctuation.
6. `hint_level_1` and `hint_level_2`: Ensure they are helpful and don't reveal the answer too early.
7. `full_explanation`: Write a child-friendly explanation (max 50-70 words) as a single natural paragraph. Do NOT use lists or numbered points.

Input:
A JSON array of questions, each having:
- `id`: unique UUID (do NOT change this)
- `question`: the question text
- `question_type`: type
- `expected_answer`: correct answer
- `mcq_options`: options array
- `correct_option`: correct option
- `acceptable_answers`: alternative answers
- `hint_level_1`: first hint
- `hint_level_2`: second hint
- `full_explanation`: explanation

Output:
Return ONLY a valid JSON array of the reviewed and improved questions containing exactly these fields:
`id`, `question`, `question_type`, `expected_answer`, `mcq_options`, `correct_option`, `acceptable_answers`, `hint_level_1`, `hint_level_2`, `full_explanation`.

Do NOT return any markdown, comments, or explanations outside the JSON array.
"""

def generate_review():
    print("=== Bulk Question Quality Review Generator ===")
    
    proposed_improvements = []
    markdown_report = [
        "# Proposed Question Improvements Review\n",
        "Please review the changes proposed by the AI below. If you approve, run the application script: `venv/bin/python scripts/apply_improvements.py` to update the database.\n",
        "---"
    ]
    
    with engine.connect() as conn:
        # Get all English chapters
        chapters = conn.execute(text("""
            SELECT DISTINCT c.id, c.title, s.name as subject_name
            FROM chapters c
            JOIN topics tp ON tp.chapter_id = c.id
            JOIN subtopics st ON st.topic_id = tp.id
            JOIN learning_units lu ON lu.subtopic_id = st.id
            JOIN questions q ON q.learning_unit_id = lu.id
            JOIN subjects s ON s.id = c.subject_id
            WHERE s.name = 'English'
            ORDER BY c.title
        """)).fetchall()
        
        print(f"Found {len(chapters)} English chapters to review.")
        
        for ch_id, ch_title, subj_name in chapters:
            print(f"\nProcessing Chapter: '{ch_title}'")
            
            # Fetch all questions
            q_rows = conn.execute(text("""
                SELECT q.id, q.text, q.question_type, q.expected_answer, 
                       q.mcq_options, q.correct_option, q.acceptable_answers,
                       q.hint_level_1, q.hint_level_2, q.full_explanation
                FROM questions q
                JOIN learning_units lu ON lu.id = q.learning_unit_id
                JOIN subtopics st ON st.id = lu.subtopic_id
                JOIN topics tp ON tp.id = st.topic_id
                WHERE tp.chapter_id = :ch_id
            """), {"ch_id": ch_id}).fetchall()
            
            if not q_rows:
                continue
                
            markdown_report.append(f"\n## Chapter: {ch_title}\n")
            
            # Format questions
            input_list = []
            orig_map = {}
            for r in q_rows:
                mcq_opts = r[4]
                if isinstance(mcq_opts, str):
                    try:
                        mcq_opts = json.loads(mcq_opts)
                    except:
                        mcq_opts = []
                elif not mcq_opts:
                    mcq_opts = []
                    
                acc_ans = r[6]
                if isinstance(acc_ans, str):
                    try:
                        acc_ans = json.loads(acc_ans)
                    except:
                        acc_ans = [r[3]]
                elif isinstance(acc_ans, list):
                    acc_ans = acc_ans
                else:
                    acc_ans = [r[3]]
                    
                orig_map[str(r[0])] = {
                    "question": r[1],
                    "question_type": r[2],
                    "expected_answer": r[3],
                    "mcq_options": mcq_opts,
                    "correct_option": r[5],
                    "acceptable_answers": acc_ans,
                    "hint_level_1": r[7] or "",
                    "hint_level_2": r[8] or "",
                    "full_explanation": r[9] or ""
                }
                
                input_list.append({
                    "id": str(r[0]),
                    "question": r[1],
                    "question_type": r[2],
                    "expected_answer": r[3],
                    "mcq_options": mcq_opts,
                    "correct_option": r[5],
                    "acceptable_answers": acc_ans,
                    "hint_level_1": r[7] or "",
                    "hint_level_2": r[8] or "",
                    "full_explanation": r[9] or ""
                })
                
            # Process in chunks of 20
            chunk_size = 20
            for i in range(0, len(input_list), chunk_size):
                chunk = input_list[i:i + chunk_size]
                print(f"Calling Gemini for chunk {i//chunk_size + 1}...")
                payload_str = json.dumps(chunk, indent=2)
                
                try:
                    raw_response = default_ai_provider.generate_text(system_prompt=SYSTEM_PROMPT, content=payload_str)
                    match = re.search(r'\[.*\]', raw_response, re.DOTALL)
                    if not match:
                        continue
                        
                    improved_list = json.loads(match.group(0))
                    
                    for item in improved_list:
                        q_id = item.get("id")
                        orig = orig_map.get(q_id)
                        if not orig:
                            continue
                            
                        # Keep proposed updates
                        proposed_improvements.append(item)
                        
                        # Generate markdown diff
                        markdown_report.append(f"### Question ID: `{q_id}`")
                        markdown_report.append(f"- **Original**: {orig['question']}")
                        markdown_report.append(f"- **Proposed**: **{item.get('question')}**")
                        markdown_report.append(f"- **Type**: `{orig['question_type']}` ➔ `{item.get('question_type')}`")
                        markdown_report.append(f"- **Original Options**: `{orig['mcq_options']}`")
                        markdown_report.append(f"- **Proposed Options**: **`{item.get('mcq_options')}`**")
                        markdown_report.append(f"- **Original Explanation**: *{orig['full_explanation']}*")
                        markdown_report.append(f"- **Proposed Explanation**: *{item.get('full_explanation')}*")
                        markdown_report.append("\n---")
                        
                except Exception as e:
                    print(f"Error processing chunk: {e}")
                    continue

    # Save outputs
    scratch_dir = "scratch"
    os.makedirs(scratch_dir, exist_ok=True)
    
    json_path = os.path.join(scratch_dir, "proposed_improvements.json")
    with open(json_path, "w") as f:
        json.dump(proposed_improvements, f, indent=2)
        
    md_path = os.path.join(scratch_dir, "proposed_improvements_review.md")
    with open(md_path, "w") as f:
        f.write("\n".join(markdown_report))
        
    print(f"\nSuccess! Proposed changes saved to {json_path}")
    print(f"User review report generated at {md_path}")
    print("Please inspect the markdown report. Once satisfied, execute apply_improvements.py to save database updates.")

if __name__ == "__main__":
    generate_review()
