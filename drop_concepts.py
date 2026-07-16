from sqlalchemy import text
from app.database.session import SessionLocal

db = SessionLocal()
try:
    db.execute(text("DROP TABLE IF EXISTS concepts CASCADE;"))
    db.commit()
    print("Table 'concepts' successfully dropped from database.")
except Exception as e:
    db.rollback()
    print(f"Error: {e}")
finally:
    db.close()
