from typing import Optional
from pydantic import BaseModel
from app.schemas.common.base import CamelBaseModel


class RegisterDeviceTokenRequest(CamelBaseModel):
    token: str
    platform: str           # "android" or "ios"
    device_id: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "token": "fcm_token_abc123xyz",
                "platform": "android",
                "deviceId": "device-uuid-from-mobile"
            }
        }
    }


class SendTestNotificationRequest(CamelBaseModel):
    title: str
    body: str
    data: Optional[dict] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Hello Study Buddy!",
                "body": "This is a test push notification.",
                "data": {
                    "type": "test",
                    "action": "open"
                }
            }
        }
    }

class SendTestNotificationResponse(BaseModel):
    successful_sends: int
    sent_tokens: list[str]

