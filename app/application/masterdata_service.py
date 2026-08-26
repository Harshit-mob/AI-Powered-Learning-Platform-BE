from typing import List, Dict, Any, Optional
from app.repositories.base.unit_of_work import UnitOfWork
from app.models.course import Board, Grade, Subject
from app.models.quiz import QuestionBank
from app.api.v1.errors import APIException
import uuid

class MasterdataService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    # --- Board CRUD ---
    def get_boards(self) -> List[Board]:
        with self.uow:
            return self.uow.session.query(Board).order_by(Board.name).all()

    def get_board(self, board_id: uuid.UUID) -> Optional[Board]:
        with self.uow:
            return self.uow.session.query(Board).filter(Board.id == board_id).first()

    def create_board(self, name: str) -> Board:
        with self.uow:
            board = Board(name=name)
            self.uow.session.add(board)
            self.uow.commit()
            # Refresh to load attributes outside session
            self.uow.session.refresh(board)
            return board

    def update_board(self, board_id: uuid.UUID, name: Optional[str]) -> Optional[Board]:
        with self.uow:
            board = self.uow.session.query(Board).filter(Board.id == board_id).first()
            if not board:
                return None
            if name is not None:
                board.name = name
            self.uow.commit()
            self.uow.session.refresh(board)
            return board

    def delete_board(self, board_id: uuid.UUID) -> bool:
        with self.uow:
            board = self.uow.session.query(Board).filter(Board.id == board_id).first()
            if not board:
                return False
                
            self.uow.session.delete(board)
            self.uow.commit()
            return True

    # --- Grade CRUD ---
    def get_all_grades(self) -> List[Grade]:
        with self.uow:
            return self.uow.session.query(Grade).order_by(Grade.name).all()

    def get_grades_by_board(self, board_id: uuid.UUID) -> List[Grade]:
        with self.uow:
            return self.uow.session.query(Grade).filter(Grade.board_id == board_id).order_by(Grade.name).all()

    def get_grade(self, grade_id: uuid.UUID) -> Optional[Grade]:
        with self.uow:
            return self.uow.session.query(Grade).filter(Grade.id == grade_id).first()

    def create_grade(self, board_id: uuid.UUID, name: str) -> Grade:
        with self.uow:
            grade = Grade(board_id=board_id, name=name)
            self.uow.session.add(grade)
            self.uow.commit()
            self.uow.session.refresh(grade)
            return grade

    def update_grade(self, grade_id: uuid.UUID, board_id: Optional[uuid.UUID], name: Optional[str]) -> Optional[Grade]:
        with self.uow:
            grade = self.uow.session.query(Grade).filter(Grade.id == grade_id).first()
            if not grade:
                return None
            if board_id is not None:
                grade.board_id = board_id
            if name is not None:
                grade.name = name
            self.uow.commit()
            self.uow.session.refresh(grade)
            return grade

    def delete_grade(self, grade_id: uuid.UUID) -> bool:
        with self.uow:
            grade = self.uow.session.query(Grade).filter(Grade.id == grade_id).first()
            if not grade:
                return False
                
            self.uow.session.delete(grade)
            self.uow.commit()
            return True

    # --- Subject CRUD ---
    def get_all_subjects(self) -> List[Subject]:
        with self.uow:
            return self.uow.session.query(Subject).order_by(Subject.name).all()

    def get_subjects_by_grade(self, grade_id: uuid.UUID) -> List[Subject]:
        with self.uow:
            return self.uow.session.query(Subject).filter(Subject.grade_id == grade_id).order_by(Subject.name).all()

    def get_subject(self, subject_id: uuid.UUID) -> Optional[Subject]:
        with self.uow:
            return self.uow.session.query(Subject).filter(Subject.id == subject_id).first()

    def create_subject(self, grade_id: uuid.UUID, name: str) -> Subject:
        with self.uow:
            subject = Subject(grade_id=grade_id, name=name)
            self.uow.session.add(subject)
            self.uow.commit()
            self.uow.session.refresh(subject)
            return subject

    def update_subject(self, subject_id: uuid.UUID, grade_id: Optional[uuid.UUID], name: Optional[str]) -> Optional[Subject]:
        with self.uow:
            subject = self.uow.session.query(Subject).filter(Subject.id == subject_id).first()
            if not subject:
                return None
            if grade_id is not None:
                subject.grade_id = grade_id
            if name is not None:
                subject.name = name
            self.uow.commit()
            self.uow.session.refresh(subject)
            return subject

    def delete_subject(self, subject_id: uuid.UUID) -> bool:
        with self.uow:
            subject = self.uow.session.query(Subject).filter(Subject.id == subject_id).first()
            if not subject:
                return False
                
            self.uow.session.delete(subject)
            self.uow.commit()
            return True
