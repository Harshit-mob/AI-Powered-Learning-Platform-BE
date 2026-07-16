from app.database.session import SessionLocal
from app.models.quiz import Question
from app.models.course import LearningUnit, Subtopic, Topic
import uuid

db = SessionLocal()
topic_id = uuid.UUID('0ec69a28-0f7d-4fe0-b78b-68c62f5c952c')

questions = db.query(Question)\
    .join(Question.learning_unit)\
    .join(LearningUnit.subtopic)\
    .where(Subtopic.topic_id == topic_id)\
    .all()

diffs = {}
for q in questions:
    d = q.difficulty
    diffs[d] = diffs.get(d, 0) + 1

print(f"Total questions: {len(questions)}")
print(f"Difficulties: {diffs}")
db.close()
