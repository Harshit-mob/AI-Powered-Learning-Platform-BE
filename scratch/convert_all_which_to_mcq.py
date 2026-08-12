import os
import json
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
RENDER_DB_URL = os.getenv("DATABASE_URL")
LOCAL_DB_URL = "postgresql://harshitdarji:admin123@localhost:5432/microlearning_db"

conversions = {
    # English Chapter: How I Taught My Grandmother to Read / Grammar
    "In the sentence 'Ranbir likes to be out of the forest', which word is a pronoun?": {
        "options": ["Ranbir", "forest", "likes", "none"],
        "correct": "none"
    },
    "Which is the subject in: 'All the children worked hard'?": {
        "options": ["All the children", "worked", "hard", "worked hard"],
        "correct": "All the children"
    },
    "Which suffix would you add to 'art' to name a person who makes art?": {
        "options": ["ist", "er", "or", "ing"],
        "correct": "ist"
    },
    "Which word in the phrase 'The Blue Umbrella' acts as an adjective?": {
        "options": ["Blue", "Umbrella", "The", "acts"],
        "correct": "Blue"
    },
    "Which word in the sentence 'She laughed a little' is a subject pronoun?": {
        "options": ["She", "laughed", "little", "a"],
        "correct": "She"
    },
    "Which pronoun would replace 'The students' in 'The students played'?": {
        "options": ["They", "He", "She", "We"],
        "correct": "They"
    },
    "Which pronoun shows ownership in 'Tom ate his breakfast'?": {
        "options": ["his", "Tom", "ate", "breakfast"],
        "correct": "his"
    },
    "Which noun is the subject in the sentence Aunt Polly scolds Tom": {
        "options": ["Aunt Polly", "Tom", "scolds", "scolds Tom"],
        "correct": "Aunt Polly"
    },
    "Which word in 'Aunt Polly said to herself' is a reflexive pronoun?": {
        "options": ["herself", "Aunt Polly", "said", "to"],
        "correct": "herself"
    },
    "Which word in the sentence 'Tom hurt himself' is a reflexive pronoun?": {
        "options": ["himself", "Tom", "hurt", "his"],
        "correct": "himself"
    },
    "Which word from the text is a synonym for 'admirable'?": {
        "options": ["praiseworthy", "terrible", "ordinary", "unhappy"],
        "correct": "praiseworthy"
    },
    "Which word describes a quality that makes someone feel pity or sadness?": {
        "options": ["pathos", "joy", "excitement", "anger"],
        "correct": "pathos"
    },
    # Science: Magnets
    "Which metal was attached to the end of the shepherd's stick?": {
        "options": ["Iron", "Copper", "Gold", "Silver"],
        "correct": "Iron"
    },
    "Which pole will be attracted to its North pole?": {
        "options": ["South pole", "North pole", "East pole", "West pole"],
        "correct": "South pole"
    },
    "Which direction does a freely suspended lodestone indicate?": {
        "options": ["North-south", "East-west", "North-east", "South-west"],
        "correct": "North-south"
    },
    "Which regions of a bar magnet are the strongest?": {
        "options": ["The ends", "The middle", "The top", "The bottom"],
        "correct": "The ends"
    },
    "Which device helps sailors find directions using a magnet?": {
        "options": ["Compass", "Telescope", "Thermometer", "Barometer"],
        "correct": "Compass"
    },
    # Social Science
    "In the timeline of human development, which comes after Prehistory?": {
        "options": ["Proto History", "Ancient History", "Modern History", "Future History"],
        "correct": "Proto History"
    },
    "Which government level looks after matters like national defence and foreign affairs?": {
        "options": ["Central Government", "State Government", "Local Government", "District Government"],
        "correct": "Central Government"
    },
    "Which government level would handle a big protest by state police?": {
        "options": ["State Government", "Central Government", "Local Government", "Village Government"],
        "correct": "State Government"
    }
}

def convert_to_mcq(db_url, db_name):
    print(f"\n=== Converting Which Questions to MCQ in {db_name} ===")
    engine = create_engine(db_url)
    with engine.connect() as conn:
        updated_count = 0
        for text_val, data in conversions.items():
            opts_json = json.dumps(data["options"])
            res = conn.execute(text("""
                UPDATE questions
                SET question_type = 'MCQ',
                    supported_answer_modes = ARRAY['MCQ']::varchar[],
                    evaluation_method = 'MCQ',
                    mcq_options = :opts_json,
                    correct_option = :correct,
                    expected_answer = :correct
                WHERE text = :text_val
            """), {
                "opts_json": opts_json,
                "correct": data["correct"],
                "text_val": text_val
            })
            updated_count += res.rowcount
            
        conn.commit()
        print(f"Successfully converted {updated_count} questions to MCQ in {db_name}.")

convert_to_mcq(RENDER_DB_URL, "Render DB")
convert_to_mcq(LOCAL_DB_URL, "Local DB")
