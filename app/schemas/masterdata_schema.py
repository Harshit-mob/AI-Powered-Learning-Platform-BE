import uuid
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class MasterdataItemResponse(BaseModel):
    id: uuid.UUID
    name: str

    model_config = ConfigDict(from_attributes=True)

# --- Board Schemas ---
class BoardCreate(BaseModel):
    name: str

class BoardUpdate(BaseModel):
    name: Optional[str] = None

class BoardResponse(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# --- Grade Schemas ---
class GradeCreate(BaseModel):
    board_id: uuid.UUID
    name: str

class GradeUpdate(BaseModel):
    board_id: Optional[uuid.UUID] = None
    name: Optional[str] = None

class GradeResponse(BaseModel):
    id: uuid.UUID
    board_id: uuid.UUID
    name: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# --- Subject Schemas ---
class SubjectCreate(BaseModel):
    grade_id: uuid.UUID
    name: str

class SubjectUpdate(BaseModel):
    grade_id: Optional[uuid.UUID] = None
    name: Optional[str] = None

class SubjectResponse(BaseModel):
    id: uuid.UUID
    grade_id: uuid.UUID
    name: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

