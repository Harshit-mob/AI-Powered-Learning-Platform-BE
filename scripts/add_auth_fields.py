import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine, text
from app.core.config import settings

def main():
    engine = create_engine(settings.DATABASE_URL)
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE students ADD COLUMN email VARCHAR;"))
            print("Added email column.")
        except Exception as e:
            print(f"Email column might already exist: {e}")
            
        try:
            conn.execute(text("ALTER TABLE students ADD COLUMN hashed_password VARCHAR;"))
            print("Added hashed_password column.")
        except Exception as e:
            print(f"Hashed_password column might already exist: {e}")

        try:
            conn.execute(text("CREATE UNIQUE INDEX ix_students_email ON students (email);"))
            print("Added index on email.")
        except Exception as e:
            print(f"Index might already exist: {e}")

if __name__ == "__main__":
    main()
