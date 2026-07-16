from sqlalchemy import text
from app.database.session import SessionLocal

db = SessionLocal()
try:
    result = db.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """))
    tables = [row[0] for row in result]
    for table in tables:
        count = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        print(f"{table}: {count} rows")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
