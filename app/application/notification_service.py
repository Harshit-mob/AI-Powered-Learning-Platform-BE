import logging
import os
import uuid
from typing import Dict, Any, Optional
import firebase_admin
from firebase_admin import credentials, messaging, exceptions

from app.core.config import settings
from app.repositories.base.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
_firebase_initialized = False

try:
    if settings.ENABLE_MOCK_NOTIFICATIONS:
        logger.info("Firebase Push Notifications are running in MOCK mode (ENABLE_MOCK_NOTIFICATIONS=True).")
    else:
        cred_path = os.path.abspath(settings.FIREBASE_CREDENTIALS_PATH)
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            _firebase_initialized = True
            logger.info("Firebase Admin SDK initialized successfully.")
        else:
            logger.warning(
                f"Firebase credentials file not found at '{cred_path}'. "
                "Push notifications will run in MOCK mode."
            )
except Exception as e:
    logger.error(f"Failed to initialize Firebase Admin SDK: {e}. Falling back to MOCK mode.")


class NotificationService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    @property
    def is_mock_mode(self) -> bool:
        return settings.ENABLE_MOCK_NOTIFICATIONS or not _firebase_initialized

    def send_push_to_token(
        self, token: str, title: str, body: str, data: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Sends a single push notification to a specific device token.
        If the token is expired/unregistered, deactivates it in the database.
        """
        # Ensure all data values are strings for FCM compatibility
        fcm_data = {}
        if data:
            for k, v in data.items():
                fcm_data[str(k)] = str(v)

        if self.is_mock_mode:
            logger.info(
                f"[MOCK PUSH] Sent to token: {token} | Title: {title} | Body: {body} | Data: {fcm_data}"
            )
            return True

        try:
            # Build the message with high priority and default sound configurations
            notification = messaging.Notification(title=title, body=body)
            
            android_config = messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    sound="default",
                    default_sound=True
                )
            )
            
            apns_config = messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        sound="default",
                        badge=1
                    )
                )
            )

            message = messaging.Message(
                notification=notification,
                data=fcm_data if fcm_data else None,
                token=token,
                android=android_config,
                apns=apns_config
            )
            # Send the message
            response = messaging.send(message)
            logger.info(f"Successfully sent push notification. Message ID: {response}")
            return True

        except exceptions.UnregisteredError:
            logger.warning(f"FCM token unregistered/expired. Deactivating: {token}")
            self._deactivate_token_safely(token)
            return False

        except exceptions.FirebaseError as e:
            # Check if it's a code indicating bad/unregistered token
            # In some versions, the specific exception subclass might not be raised,
            # but the code field contains 'registration-token-not-registered'
            if getattr(e, "code", None) == "registration-token-not-registered":
                logger.warning(f"FCM token invalid/expired (detected via code). Deactivating: {token}")
                self._deactivate_token_safely(token)
            else:
                logger.error(f"Firebase error sending push notification: {e}")
            return False

        except Exception as e:
            logger.error(f"Unexpected error sending push notification: {e}")
            return False

    def send_push_to_student(
        self, student_id: uuid.UUID, title: str, body: str, data: Optional[Dict[str, str]] = None
    ) -> tuple[int, list[str]]:
        """
        Sends a push notification to all active device tokens registered to a student.
        Returns a tuple of (successful_sends_count, list_of_target_tokens).
        """
        # We perform database operations inside a unit of work context
        with self.uow:
            active_tokens = self.uow.device_tokens.get_by_student(student_id)
            if not active_tokens:
                logger.info(f"No active device tokens found for student {student_id}")
                return 0, []

            successful_sends = 0
            sent_tokens = []
            for token_record in active_tokens:
                success = self.send_push_to_token(
                    token=token_record.token,
                    title=title,
                    body=body,
                    data=data
                )
                if success:
                    successful_sends += 1
                    sent_tokens.append(token_record.token)

            self.uow.commit()
            return successful_sends, sent_tokens

    def _deactivate_token_safely(self, token: str) -> None:
        """Deactivate token inside a separate UOW to ensure transaction is flushed/committed."""
        try:
            # If we are already in an active transaction, this will be part of it.
            # Otherwise we commit it separately.
            self.uow.device_tokens.deactivate_token(token)
        except Exception as e:
            logger.error(f"Failed to deactivate FCM token {token}: {e}")
