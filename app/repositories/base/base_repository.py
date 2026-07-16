from typing import Generic, TypeVar, Type, List, Optional, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select, func, update, delete
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.database.session import Base
from app.repositories.exceptions import DuplicateEntityError, RepositoryException

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: Session):
        self.model = model
        self.session = session

    def get_by_id(self, id: Any) -> Optional[ModelType]:
        try:
            return self.session.get(self.model, id)
        except SQLAlchemyError as e:
            raise RepositoryException(f"Database error getting {self.model.__name__} by id: {str(e)}")

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        try:
            stmt = select(self.model).offset(skip).limit(limit)
            return list(self.session.scalars(stmt).all())
        except SQLAlchemyError as e:
            raise RepositoryException(f"Database error getting all {self.model.__name__}: {str(e)}")

    def exists(self, id: Any) -> bool:
        try:
            stmt = select(func.count()).select_from(self.model).where(self.model.id == id)
            return self.session.scalar(stmt) > 0
        except SQLAlchemyError as e:
            raise RepositoryException(f"Database error checking existence of {self.model.__name__}: {str(e)}")

    def create(self, obj_in: Dict[str, Any]) -> ModelType:
        try:
            db_obj = self.model(**obj_in)
            self.session.add(db_obj)
            self.session.flush()
            return db_obj
        except IntegrityError as e:
            self.session.rollback()
            raise DuplicateEntityError(f"Duplicate entity for {self.model.__name__}: {str(e)}")
        except SQLAlchemyError as e:
            self.session.rollback()
            raise RepositoryException(f"Database error creating {self.model.__name__}: {str(e)}")

    def create_many(self, objs_in: List[Dict[str, Any]]) -> List[ModelType]:
        try:
            db_objs = [self.model(**obj) for obj in objs_in]
            self.session.add_all(db_objs)
            self.session.flush()
            return db_objs
        except IntegrityError as e:
            self.session.rollback()
            raise DuplicateEntityError(f"Duplicate entities for {self.model.__name__}: {str(e)}")
        except SQLAlchemyError as e:
            self.session.rollback()
            raise RepositoryException(f"Database error creating multiple {self.model.__name__}: {str(e)}")

    def update(self, id: Any, obj_in: Dict[str, Any]) -> Optional[ModelType]:
        try:
            stmt = update(self.model).where(self.model.id == id).values(**obj_in)
            self.session.execute(stmt)
            self.session.flush()
            return self.get_by_id(id)
        except SQLAlchemyError as e:
            self.session.rollback()
            raise RepositoryException(f"Database error updating {self.model.__name__}: {str(e)}")

    def delete(self, id: Any) -> bool:
        try:
            stmt = delete(self.model).where(self.model.id == id)
            result = self.session.execute(stmt)
            self.session.flush()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            self.session.rollback()
            raise RepositoryException(f"Database error deleting {self.model.__name__}: {str(e)}")

    def count(self) -> int:
        try:
            stmt = select(func.count()).select_from(self.model)
            return self.session.scalar(stmt)
        except SQLAlchemyError as e:
            raise RepositoryException(f"Database error counting {self.model.__name__}: {str(e)}")

    def filter(self, filters: Dict[str, Any], skip: int = 0, limit: int = 100) -> List[ModelType]:
        try:
            stmt = select(self.model).filter_by(**filters).offset(skip).limit(limit)
            return list(self.session.scalars(stmt).all())
        except SQLAlchemyError as e:
            raise RepositoryException(f"Database error filtering {self.model.__name__}: {str(e)}")

    def first(self, filters: Dict[str, Any]) -> Optional[ModelType]:
        try:
            stmt = select(self.model).filter_by(**filters).limit(1)
            return self.session.scalars(stmt).first()
        except SQLAlchemyError as e:
            raise RepositoryException(f"Database error getting first {self.model.__name__}: {str(e)}")
