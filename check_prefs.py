from sqlalchemy import text
from app.database.session import SessionLocal

db = SessionLocal()
try:
    result = db.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'student_preferences'
    """))
    print("student_preferences columns:")
    for row in result:
        print(row)
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
