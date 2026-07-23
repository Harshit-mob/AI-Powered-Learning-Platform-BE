import logging
from typing import List
from pydantic import BaseModel, Field
from app.content.ai_provider import AIProviderInterface, PromptBuilder

logger = logging.getLogger(__name__)

# --- Structured JSON Schemas ---
class ParsedLearningUnit(BaseModel):
    title: str = Field(..., description="A short, descriptive title for this specific concept.")
    content: str = Field(..., description="The granular text content belonging exclusively to this concept. Do not summarize, use original text where possible.")
    learning_objective: str = Field(..., description="What the student should understand after reading this unit.")
    keywords: List[str] = Field(..., description="Key vocabulary terms present in this unit.")
    difficulty: int = Field(..., ge=1, le=5, description="Estimated difficulty on a scale of 1 to 5.")
    estimated_reading_time: int = Field(..., description="Estimated time to read and comprehend in seconds.")
    source_pages: List[int] = Field(..., description="The page numbers this concept was extracted from.")
    summary: str = Field(..., description="A 1-2 sentence simplified summary of the concept.")
    subtopic_title: str = Field(..., description="The exact title of the subtopic this unit belongs to, used for mapping.")

class LearningUnitList(BaseModel):
    learning_units: List[ParsedLearningUnit]

class LearningUnitBuilder:
    """
    Service responsible for converting the entire structured curriculum into granular Learning Units.
    """
    
    def __init__(self, ai_provider: AIProviderInterface):
        self.ai_provider = ai_provider
        self.prompt_builder = PromptBuilder()

    def build_from_curriculum(self, curriculum_json: str) -> List[ParsedLearningUnit]:
        """
        Takes the entire Curriculum JSON (or a batch of topics) and uses AI to intelligently 
        slice it into multiple focused Learning Units in a single API call.
        """
        logger.info("Building Learning Units for batched curriculum scope...")
        
        system_prompt = self.prompt_builder.build("learning_unit_builder.md")

        try:
            structured_data = self.ai_provider.generate_structured_data(
                system_prompt=system_prompt,
                content=curriculum_json,
                schema=LearningUnitList
            )
            return structured_data.learning_units
        except Exception as e:
            logger.error(f"Failed to build learning units: {str(e)}")
            raise RuntimeError(f"Learning Unit Builder failed: {str(e)}")
