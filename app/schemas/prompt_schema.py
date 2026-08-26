from pydantic import BaseModel, Field

class PromptResponse(BaseModel):
    name: str = Field(..., description="The unique key of the system prompt")
    content: str = Field(..., description="The actual markdown system prompt content")

class PromptUpdateRequest(BaseModel):
    content: str = Field(..., min_length=100, description="The updated prompt content (must be at least 100 characters)")
