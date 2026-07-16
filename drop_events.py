from sqlalchemy import text
from app.database.session import SessionLocal

db = SessionLocal()
try:
    db.execute(text("DROP TABLE IF EXISTS events_log CASCADE;"))
    db.commit()
    print("Table 'events_log' successfully dropped from database.")
except Exception as e:
    db.rollback()
    print(f"Error: {e}")
finally:
    db.close()
