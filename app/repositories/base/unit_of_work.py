from __future__ import annotations
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database.session import SessionLocal
from app.repositories.exceptions import RepositoryException

from app.repositories.personalization.student_repository import StudentRepository
from app.repositories.learning.mastery_repository import MasteryRepository
from app.repositories.assessment.session_repository import SessionRepository
from app.repositories.assessment.response_repository import ResponseRepository
from app.repositories.content.question_repository import QuestionRepository
from app.repositories.core.device_token_repository import DeviceTokenRepository

class UnitOfWork:
    def __init__(self, session_factory=SessionLocal):
        self._session_factory = session_factory
        self.session: Session = None

    def __enter__(self) -> UnitOfWork:
        self.session = self._session_factory()
        
        self.students = StudentRepository(self.session)
        self.mastery = MasteryRepository(self.session)
        self.sessions = SessionRepository(self.session)
        self.responses = ResponseRepository(self.session)
        self.questions = QuestionRepository(self.session)
        self.device_tokens = DeviceTokenRepository(self.session)

        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None:
            self.rollback()
        self.session.close()

    def commit(self) -> None:
        try:
            self.session.commit()
        except SQLAlchemyError as e:
            self.rollback()
            raise RepositoryException(f"Database commit failed: {str(e)}")

    def rollback(self) -> None:
        try:
            self.session.rollback()
        except SQLAlchemyError as e:
            raise RepositoryException(f"Database rollback failed: {str(e)}")
