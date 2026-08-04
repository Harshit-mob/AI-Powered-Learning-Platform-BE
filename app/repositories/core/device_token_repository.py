import uuid
from typing import List, Optional

from sqlalchemy.exc import SQLAlchemyError

from app.models.core.device_token import StudentDeviceToken
from app.repositories.base.base_repository import BaseRepository
from app.repositories.exceptions import RepositoryException


class DeviceTokenRepository(BaseRepository[StudentDeviceToken]):
    def __init__(self, session):
        super().__init__(StudentDeviceToken, session)

    def get_by_student(self, student_id: uuid.UUID) -> List[StudentDeviceToken]:
        """Return all active tokens for a student (across all devices)."""
        return self.filter({"student_id": student_id, "is_active": True})

    def get_by_student_and_device(self, student_id: uuid.UUID, device_id: str) -> Optional[StudentDeviceToken]:
        """Return the token row for a specific student + device combination."""
        return self.first({"student_id": student_id, "device_id": device_id})

    def upsert_token(self, student_id: uuid.UUID, token: str, platform: str, device_id: Optional[str]) -> StudentDeviceToken:
        """
        Insert a new token or update an existing one.
        Matches by (student_id, device_id) if device_id is provided, otherwise by token value.
        """
        try:
            existing = None

            if device_id:
                existing = self.get_by_student_and_device(student_id, device_id)
            else:
                # Fallback: match by token string itself
                existing = self.first({"student_id": student_id, "token": token})

            if existing:
                existing.token = token
                existing.platform = platform
                existing.is_active = True
                self.session.flush()
                return existing
            else:
                new_token = StudentDeviceToken(
                    student_id=student_id,
                    token=token,
                    platform=platform,
                    device_id=device_id,
                    is_active=True,
                )
                self.session.add(new_token)
                self.session.flush()
                return new_token

        except SQLAlchemyError as e:
            self.session.rollback()
            raise RepositoryException(f"Error upserting device token: {str(e)}")

    def deactivate_token(self, token: str) -> None:
        """Mark a specific FCM/APN token as inactive (e.g. when push delivery fails)."""
        try:
            record = self.first({"token": token})
            if record:
                record.is_active = False
                self.session.flush()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise RepositoryException(f"Error deactivating token: {str(e)}")

    def deactivate_by_device(self, student_id: uuid.UUID, device_id: str) -> None:
        """Deactivate a specific device's token for a student (single-device logout)."""
        try:
            record = self.get_by_student_and_device(student_id, device_id)
            if record:
                record.is_active = False
                self.session.flush()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise RepositoryException(f"Error deactivating device token: {str(e)}")

    def deactivate_all_for_student(self, student_id: uuid.UUID) -> None:
        """Deactivate all device tokens for a student (full logout from all devices)."""
        try:
            records = self.filter({"student_id": student_id, "is_active": True})
            for record in records:
                record.is_active = False
            self.session.flush()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise RepositoryException(f"Error deactivating all tokens: {str(e)}")
