import logging
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.services.content.ai_provider import AIProviderInterface, PromptBuilder

logger = logging.getLogger(__name__)

# --- Structured JSON Schemas ---
class ParsedSubtopic(BaseModel):
    title: str = Field(..., description="Title of the subtopic")
    summary: str = Field(..., description="Summary of the subtopic")
    content: str = Field(..., description="The full, raw text content belonging to this subtopic. Do not summarize.")
    learning_objectives: List[str] = Field(..., description="Learning objectives for this subtopic")
    estimated_reading_time: int = Field(..., description="Estimated reading time in seconds")
    source_pages: List[int] = Field(..., description="Source page numbers")

class ParsedTopic(BaseModel):
    title: str = Field(..., description="Title of the main topic")
    summary: str = Field(..., description="A 1-2 sentence simplified summary of the topic.")
    learning_objectives: List[str] = Field(..., description="List of learning objectives for this topic.")
    keywords: List[str] = Field(..., description="Key vocabulary terms present in this topic.")
    source_pages: List[int] = Field(..., description="Source page numbers for the topic")
    subtopics: List[ParsedSubtopic] = Field(..., description="Subtopics belonging to this topic")

class ParsedChapter(BaseModel):
    title: str = Field(..., description="Title of the chapter")
    topics: List[ParsedTopic] = Field(..., description="Topics belonging to this chapter")

class ParsedCurriculum(BaseModel):
    board: str = Field(..., description="Educational Board (e.g., CBSE)")
    grade: str = Field(..., description="Grade level (e.g., Grade 6)")
    subject: str = Field(..., description="Subject name (e.g., Science)")
    chapter: ParsedChapter


class CurriculumParser:
    """
    Service responsible for converting raw cleaned text into a highly structured 
    curriculum JSON object representing the exact hierarchy.
    DOES NOT insert into the database.
    """
    
    def __init__(self, ai_provider: AIProviderInterface):
        self.ai_provider = ai_provider
        self.prompt_builder = PromptBuilder()

    def parse(self, cleaned_text: str, metadata_hints: Optional[Dict[str, Any]] = None) -> ParsedCurriculum:
        """
        Analyzes the cleaned text document and extracts the structural hierarchy.
        """
        logger.info("Starting Curriculum Parsing via AI Provider...")
        
        hints_str = f"Hints: {metadata_hints}" if metadata_hints else ""
        system_prompt = self.prompt_builder.build("curriculum_parser.md", hints_section=hints_str)

        try:
            # We rely entirely on the AI Provider Interface to guarantee structured JSON output
            structured_data = self.ai_provider.generate_structured_data(
                system_prompt=system_prompt,
                content=cleaned_text,
                schema=ParsedCurriculum
            )
            return structured_data
        except Exception as e:
            logger.error(f"Failed to parse curriculum: {str(e)}")
            raise RuntimeError(f"Curriculum parsing failed: {str(e)}")
