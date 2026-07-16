import uuid
from app.repositories.base.unit_of_work import UnitOfWork
from app.runtime.session.exceptions import SessionValidationError

class SessionValidator:
    """
    Validates pre-conditions before generating or resuming sessions.
    """
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def validate_content_access(self, student_id: uuid.UUID, content_id: uuid.UUID, content_type: str):
        """
        Validates if the student has access to the requested content.
        """
        with self.uow:
            student = self.uow.students.find_by_id(student_id)
            if not student:
                raise SessionValidationError(f"Student {student_id} not found.")
            
            # Check content exists and matches grade/board boundaries
            # if content_type == "CHAPTER":
            #     if not self.uow.chapters.exists(content_id):
            #         raise SessionValidationError("Invalid chapter.")
            pass

    def validate_session_ownership(self, session_id: uuid.UUID, student_id: uuid.UUID):
        """
        Ensures a student can only resume or complete their own sessions.
        """
        with self.uow:
            session = self.uow.sessions.get_by_id(session_id)
            if not session:
                raise SessionValidationError("Session not found.")
            
            if session.student_id != student_id:
                raise SessionValidationError("Forbidden. You do not own this session.")
                
            return session
