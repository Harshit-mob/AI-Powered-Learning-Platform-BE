import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
RENDER_DB_URL = os.getenv("DATABASE_URL")
LOCAL_DB_URL = "postgresql://harshitdarji:admin123@localhost:5432/microlearning_db"

updates = {
    "In 'beautiful old house', which adjective describes the age?": 
        "In the phrase 'beautiful old house', what adjective describes the age?",
        
    "Which degree shows no comparison at all?": 
        "What degree shows no comparison at all?",
        
    "Riya felt shy when she made a mistake. Which word describes her feeling?": 
        "Riya felt shy when she made a mistake. What word describes her feeling?",
        
    "Which word in 'tiny wooden box' represents the material?": 
        "What word in 'tiny wooden box' represents the material?",
        
    "Which pronoun can replace 'Anasuya Shankar' in the sentence: 'Anasuya Shankar wrote stories'?": 
        "What pronoun can replace 'Anasuya Shankar' in the sentence: 'Anasuya Shankar wrote stories'?",
        
    "In the sentence 'We used to wait for the bus', which is the pronoun?": 
        "Identify the pronoun in the sentence: 'We used to wait for the bus'.",
        
    "Sudha Murty writes in which two languages?": 
        "In which two languages does Sudha Murty write?",
        
    "In the sentence 'The grandmother loved her grandchildren', which word is a common noun?": 
        "Identify the common noun in the sentence: 'The grandmother loved her grandchildren'."
}

def apply_updates(db_url, db_name):
    print(f"\n=== Updating Questions in {db_name} ===")
    engine = create_engine(db_url)
    with engine.connect() as conn:
        total_updated = 0
        for old_txt, new_txt in updates.items():
            res = conn.execute(text("""
                UPDATE questions
                SET text = :new_txt
                WHERE text = :old_txt
            """), {"new_txt": new_txt, "old_txt": old_txt})
            total_updated += res.rowcount
        conn.commit()
        print(f"Updated {total_updated} questions in {db_name}.")

apply_updates(RENDER_DB_URL, "Render DB")
apply_updates(LOCAL_DB_URL, "Local DB")
