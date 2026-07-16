import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.core.student import Student
from app.api.v1.auth_utils import get_password_hash, verify_password

def main():
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Let's see the first student
    student = session.query(Student).filter(Student.email.isnot(None)).first()
    if not student:
        print("No student found with email.")
        return
        
    print(f"Found student: {student.email}")
    print(f"Hashed password in DB: {student.hashed_password}")
    
    # Try to verify against a known string just to see if it throws error
    try:
        res = verify_password("Test1234!", student.hashed_password)
        print(f"Verification with Test1234! returned: {res}")
    except Exception as e:
        print(f"Error in verify_password: {e}")

if __name__ == "__main__":
    main()
