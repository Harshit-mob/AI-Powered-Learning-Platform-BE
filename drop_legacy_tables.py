from sqlalchemy import text
from app.database.session import SessionLocal

db = SessionLocal()
try:
    db.execute(text("DROP TABLE IF EXISTS submitted_answers CASCADE;"))
    db.execute(text("DROP TABLE IF EXISTS quiz_sessions CASCADE;"))
    db.commit()
    print("Tables successfully dropped from database.")
except Exception as e:
    db.rollback()
    print(f"Error: {e}")
finally:
    db.close()
