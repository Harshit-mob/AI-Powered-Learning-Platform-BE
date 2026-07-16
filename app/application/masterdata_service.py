from typing import List, Dict, Any
from app.repositories.base.unit_of_work import UnitOfWork
from app.models.course import Board, Grade
import uuid

class MasterdataService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def get_boards(self) -> List[Dict[str, Any]]:
        with self.uow:
            boards = self.uow.session.query(Board).all()
            return [{"id": b.id, "name": b.name} for b in boards]

    def get_grades_by_board(self, board_id: uuid.UUID) -> List[Dict[str, Any]]:
        with self.uow:
            grades = self.uow.session.query(Grade).filter(Grade.board_id == board_id).all()
            return [{"id": g.id, "name": g.name} for g in grades]
