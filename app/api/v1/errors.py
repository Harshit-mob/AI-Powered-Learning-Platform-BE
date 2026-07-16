from fastapi import Request, status
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class APIException(Exception):
    def __init__(self, code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, errors: list = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.errors = errors or []

def error_response(code: str, message: str, status_code: int = 400, errors: list = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": {
                "code": code,
                "errors": errors or []
            }
        }
    )

async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url}: {exc}", exc_info=True)
    return error_response(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

async def custom_api_exception_handler(request: Request, exc: APIException):
    return error_response(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        errors=exc.errors
    )
