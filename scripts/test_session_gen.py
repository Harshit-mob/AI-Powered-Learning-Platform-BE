import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.repositories.base.unit_of_work import UnitOfWork
from app.application.session_service import SessionApplicationService
from app.models.core.student import Student
import uuid

def main():
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    
    with Session() as session:
        student = session.query(Student).filter(Student.email == "teststudent@gmail.com").first()
        student_id = student.id

    uow = UnitOfWork(session_factory=lambda: Session())
    service = SessionApplicationService(uow)
    
    payload = {
        "topic_ids": ["0ec69a28-0f7d-4fe0-b78b-68c62f5c952c"]
    }
    
    try:
        data = service.generate_session(student_id, payload)
        import pprint
        pprint.pprint(data)
    except Exception as e:
        print(f"Exception: {type(e).__name__}: {e}")

if __name__ == "__main__":
    main()
