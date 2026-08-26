from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.auth import router as auth_router
from app.api.v1.session import router as session_router
from app.api.v1.content import router as content_router
from app.api.v1.student import router as student_router
from app.api.v1.home import router as home_router
from app.api.v1.masterdata import router as masterdata_router
from app.api.v1.notification import router as notification_router
from app.api.v1.admin_prompt import router as admin_prompt_router
from app.api.v1.middleware import setup_middleware
from app.api.v1.errors import APIException, custom_api_exception_handler, global_exception_handler

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="Student MVP API Layer",
    version="1.0.0"
)

# Setup Middleware
setup_middleware(app)

# Setup Exception Handlers
app.add_exception_handler(APIException, custom_api_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Health Check
@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME}

# Include Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(session_router, prefix=settings.API_V1_STR)
app.include_router(content_router, prefix=settings.API_V1_STR)
app.include_router(student_router, prefix=settings.API_V1_STR)
app.include_router(home_router, prefix=settings.API_V1_STR)
app.include_router(masterdata_router, prefix=settings.API_V1_STR)
app.include_router(notification_router, prefix=settings.API_V1_STR)
app.include_router(admin_prompt_router, prefix=settings.API_V1_STR)
