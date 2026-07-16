from typing import Optional, List, Any, Dict
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.models.learning.events_log import EventsLog
from app.repositories.base.base_repository import BaseRepository
from app.repositories.exceptions import RepositoryException

class EventsRepository(BaseRepository[EventsLog]):
    def __init__(self, session):
        super().__init__(EventsLog, session)

    def append_event(self, event_data: Dict[str, Any]) -> EventsLog:
        return self.create(event_data)

    def append_many(self, events_data: List[Dict[str, Any]]) -> List[EventsLog]:
        return self.create_many(events_data)

    def get_events(self, skip: int = 0, limit: int = 100) -> List[EventsLog]:
        try:
            stmt = select(self.model).order_by(self.model.occurred_at.desc()).offset(skip).limit(limit)
            return list(self.session.scalars(stmt).all())
        except SQLAlchemyError as e:
            raise RepositoryException(f"Error getting events: {str(e)}")

    def get_by_aggregate(self, aggregate_id: str, aggregate_type: str) -> List[EventsLog]:
        try:
            stmt = select(self.model).where(
                self.model.entity_id == aggregate_id,
                self.model.entity_type == aggregate_type
            ).order_by(self.model.version.asc())
            return list(self.session.scalars(stmt).all())
        except SQLAlchemyError as e:
            raise RepositoryException(f"Error getting events for aggregate: {str(e)}")

    def replay_events(self, aggregate_id: str, aggregate_type: str, up_to_version: Optional[int] = None) -> List[EventsLog]:
        try:
            stmt = select(self.model).where(
                self.model.entity_id == aggregate_id,
                self.model.entity_type == aggregate_type
            )
            if up_to_version is not None:
                stmt = stmt.where(self.model.version <= up_to_version)
                
            stmt = stmt.order_by(self.model.version.asc())
            return list(self.session.scalars(stmt).all())
        except SQLAlchemyError as e:
            raise RepositoryException(f"Error replaying events: {str(e)}")
