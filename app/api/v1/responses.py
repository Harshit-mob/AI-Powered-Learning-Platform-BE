from typing import Any, Dict, Generic, TypeVar
from datetime import datetime, timezone
from pydantic import BaseModel

T = TypeVar("T")

class GenericSuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str
    timestamp: str
    data: T

SuccessResponse = GenericSuccessResponse[Any]

def create_response(data: Any, message: str = "Success") -> Dict[str, Any]:
    return {
        "success": True,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data
    }
