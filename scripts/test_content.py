import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.core.student import Student
from app.repositories.base.unit_of_work import UnitOfWork
from app.application.content_service import ContentService
from pprint import pprint

def main():
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    
    # We will use the UoW directly
    # Find the teststudent@gmail.com
    with Session() as session:
        student = session.query(Student).filter(Student.email == "teststudent@gmail.com").first()
        if not student:
            print("No student teststudent@gmail.com found.")
            return
            
        print(f"Student ID: {student.id}, Grade ID: {student.grade_id}")
        if not student.grade_id:
            print("Student has no grade, let's assign the first grade found in the db to test.")
            from app.models.course import Grade
            first_grade = session.query(Grade).first()
            if first_grade:
                student.grade_id = first_grade.id
                session.commit()
                print(f"Assigned grade {first_grade.name} to student.")
            else:
                print("No grades found in DB.")
                return

    uow = UnitOfWork(session_factory=lambda: Session())
    service = ContentService(uow)
    
    subjects = service.get_subjects(student.id)
    print("\n--- SUBJECTS ---")
    pprint(subjects)
    
    if subjects:
        first_subject = subjects[0]["subject_id"]
        chapters = service.get_chapters(student.id, first_subject)
        print("\n--- CHAPTERS ---")
        pprint(chapters)

if __name__ == "__main__":
    main()
