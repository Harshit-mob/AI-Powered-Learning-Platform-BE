from typing import Any, Dict, Generic, TypeVar
from datetime import datetime, timezone
from app.schemas.common.base import CamelBaseModel

T = TypeVar("T")

class SuccessResponse(CamelBaseModel, Generic[T]):
    success: bool = True
    message: str
    timestamp: str
    data: T

def create_response(data: Any, message: str = "Success") -> Dict[str, Any]:
    return {
        "success": True,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data
    }
