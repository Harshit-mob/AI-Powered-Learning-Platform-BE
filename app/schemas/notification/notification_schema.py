from typing import Optional
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
