import json
import os
from app.database.session import SessionLocal
from app.models.quiz import Question

def dump_questions():
    db = SessionLocal()
    questions = db.query(Question).all()
    q_dicts = []
    
    for q in questions:
        q_dict = {}
        for c in q.__table__.columns:
            val = getattr(q, c.name)
            # handle lists and enums easily if needed, default=str handles UUIDs and datetime
            q_dict[c.name] = val
        q_dicts.append(q_dict)
        
    out_path = os.path.join(os.path.dirname(__file__), "..", "generated", "questions", "questions.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    with open(out_path, "w") as f:
        json.dump(q_dicts, f, indent=2, default=str)
        
    print(f"Dumped {len(q_dicts)} questions to {out_path}")

if __name__ == "__main__":
    dump_questions()
