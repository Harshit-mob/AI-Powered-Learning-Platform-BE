import os
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends
from app.api.v1.dependencies import get_current_admin, get_uow
from app.repositories.base.unit_of_work import UnitOfWork
from app.api.v1.responses import create_response, SuccessResponse, GenericSuccessResponse
from app.api.v1.errors import error_response
from app.models.prompt import SystemPrompt
from app.schemas.prompt_schema import PromptResponse, PromptUpdateRequest

router = APIRouter(prefix="/admin/prompts", tags=["Admin System Prompts"])

# Map prompt names to their filesystem default filenames
DEFAULT_PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"
PROMPT_FILES_MAP = {
    "question_generator": "question_generator.md",
    "learning_unit_builder": "learning_unit_builder.md"
}
PROMPT_LABELS = {
    "question_generator": "Question Generator",
    "learning_unit_builder": "Learning Unit Builder"
}

def load_default_prompt_file(name: str) -> str:
    filename = PROMPT_FILES_MAP.get(name)
    if not filename:
        return ""
    filepath = DEFAULT_PROMPTS_DIR / filename
    if not filepath.exists():
        return ""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

@router.get("", response_model=GenericSuccessResponse[List[PromptResponse]])
def list_prompts(
    admin = Depends(get_current_admin),
    uow: UnitOfWork = Depends(get_uow)
):
    """List all available system prompts with their current content (DB or fallback)."""
    with uow:
        # Load all from DB
        db_prompts = {p.name: p.content for p in uow.session.query(SystemPrompt).all()}
        
        results = []
        for name in PROMPT_FILES_MAP.keys():
            content = db_prompts.get(name)
            if not content:
                content = load_default_prompt_file(name)
            label = PROMPT_LABELS.get(name, name)
            results.append(PromptResponse(id=name, name=name, label=label, content=content))
            
        return create_response(results, "Prompts retrieved successfully")



@router.put("/{id}", response_model=SuccessResponse)
def update_prompt(
    id: str,
    payload: PromptUpdateRequest,
    admin = Depends(get_current_admin),
    uow: UnitOfWork = Depends(get_uow)
):
    """Update/save a dynamic prompt content in the database."""
    if id not in PROMPT_FILES_MAP:
        return error_response("BAD_REQUEST", f"System prompt key '{id}' is invalid.", status_code=400)
        
    # Validation: minimum length validation is enforced by schema (min_length=100)
    # Check if empty or whitespace only
    clean_content = payload.content.strip()
    if not clean_content:
        return error_response("BAD_REQUEST", "Prompt content cannot be empty or whitespace only.", status_code=400)
        
    with uow:
        db_prompt = uow.session.query(SystemPrompt).filter(SystemPrompt.name == id).first()
        if db_prompt:
            db_prompt.content = clean_content
        else:
            db_prompt = SystemPrompt(name=id, content=clean_content)
            uow.session.add(db_prompt)
        uow.commit()
        
    return create_response(None, f"System prompt '{id}' updated successfully.")
