import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine
from sqlalchemy import create_engine, text
from app.core.config import settings

def main():
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        students = conn.execute(text("SELECT id, email, hashed_password FROM students")).fetchall()
        print(f"Total students: {len(students)}")
        for s in students:
            hash_val = s[2]
            print(f"ID: {s[0]} | Email: {s[1]} | Hash Length: {len(hash_val) if hash_val else 0} | Hash: {hash_val}")

if __name__ == "__main__":
    main()
