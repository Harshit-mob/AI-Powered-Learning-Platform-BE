import pytest
from sqlalchemy.exc import IntegrityError
import uuid

from app.models.core.student import Student
from app.repositories.personalization.student_repository import StudentRepository
from app.repositories.base.unit_of_work import UnitOfWork
from app.repositories.exceptions import DuplicateEntityError, RepositoryException

def test_student_crud(db_session):
    repo = StudentRepository(db_session)
    
    # Test Create
    student_data = {"name": "Test Student", "streak_days": 5}
    student = repo.create(student_data)
    db_session.commit()
    assert student.id is not None
    assert student.name == "Test Student"
    
    # Test Read
    found_student = repo.find_by_id(student.id)
    assert found_student is not None
    assert found_student.streak_days == 5
    
    # Test Update
    repo.update(student.id, {"streak_days": 6})
    db_session.commit()
    updated = repo.find_by_id(student.id)
    assert updated.streak_days == 6
    
    # Test Delete
    repo.delete(student.id)
    db_session.commit()
    deleted = repo.find_by_id(student.id)
    assert deleted is None

def test_pagination(db_session):
    repo = StudentRepository(db_session)
    students = [{"name": f"Student {i}"} for i in range(15)]
    repo.create_many(students)
    db_session.commit()
    
    # Paginate
    page1 = repo.get_all(skip=0, limit=10)
    page2 = repo.get_all(skip=10, limit=10)
    
    assert len(page1) == 10
    assert len(page2) == 5

def test_unit_of_work_commit(session_factory):
    # Test UnitOfWork Context Manager and Commit
    with UnitOfWork(session_factory) as uow:
        uow.students.create({"name": "UoW Student"})
        uow.commit()
        
    with UnitOfWork(session_factory) as uow:
        student = uow.students.first({"name": "UoW Student"})
        assert student is not None
        assert student.name == "UoW Student"

def test_unit_of_work_rollback_on_exception(session_factory):
    # Test that exception inside block triggers automatic rollback
    try:
        with UnitOfWork(session_factory) as uow:
            uow.students.create({"name": "Rollback Student"})
            # Simulating business logic exception
            raise ValueError("Something went wrong")
    except ValueError:
        pass
        
    # Verify it was rolled back
    with UnitOfWork(session_factory) as uow:
        student = uow.students.first({"name": "Rollback Student"})
        assert student is None

def test_duplicate_entity_exception(db_session):
    repo = StudentRepository(db_session)
    student = repo.create({"name": "Unique Student"})
    db_session.commit()
    
    # Try to violate unique constraint (assuming we can mock this or use relationships)
    # Actually, students just have ID as PK, but we can test by forcing the same ID
    with pytest.raises(DuplicateEntityError):
        repo.create({"id": student.id, "name": "Duplicate"})
