import logging
from typing import Dict, Any, List

from .models import QuestionIntelligence
from .config import IntelligenceConfig

logger = logging.getLogger(__name__)

import os
import json

class SessionTagGenerator:
    """
    Generates deterministic, highly-indexable session tags for rapid filtering.
    """
    def __init__(self, config: IntelligenceConfig):
        self.config = config
        
        # Load taxonomy
        tax_path = os.path.join(os.path.dirname(__file__), "config", "taxonomy.json")
        try:
            with open(tax_path, "r") as f:
                self.taxonomy = json.load(f)
        except Exception:
            self.taxonomy = {"tags": {}}
            
        self.allowed_tags = set()
        for group in self.taxonomy.get("tags", {}).values():
            self.allowed_tags.update(group)
        # We enforce a strict canonical vocabulary as per requirements
        self.valid_tags = {
            "easy", "medium", "hard", 
            "warmup", "practice", "assessment", "challenge", "mastery",
            "remember", "understand", "apply", "analyze", "evaluate", "create",
            "voice_friendly", "mcq", "fill_blank", "definition", "reasoning"
        }

    def generate(self, question: Dict[str, Any], partial_intel: QuestionIntelligence) -> List[str]:
        tags = set()
        
        q_type = str(question.get("question_type", "")).upper()
        bloom = str(partial_intel.bloom_level.value).lower() if partial_intel.bloom_level else "understand"
        purpose = str(getattr(partial_intel, 'question_purpose', "practice")).lower()
        
        # Core Mapping Rules
        if q_type == "DEFINITION":
            tags.update(["definition", "remember"])
        elif q_type == "REASONING":
            tags.update(["reasoning", "analyze"])
        elif q_type in ["MCQ", "MULTIPLE_CHOICE"]:
            tags.update(["mcq", "remember"])
        elif q_type == "FILL_BLANK":
            tags.update(["fill_blank", "remember"])
            
        # Ensure Bloom and Purpose are added cleanly
        if bloom in self.valid_tags: tags.add(bloom)
        if purpose in self.valid_tags: tags.add(purpose)
            
        # 1. Difficulty Tags
        diff = int(question.get("difficulty", 2))
        if diff == 1:
            tags.add("easy")
        elif diff >= 4:
            tags.add("hard")
        else:
            tags.add("medium")
            
        # 2. Modality Tags
        if partial_intel.voice_score >= getattr(self.config, 'optimal_voice_score_threshold', 80):
            tags.add("voice_friendly")
            
        # Filter strictly
        valid_tags = [t for t in tags if t in self.valid_tags]
        
        # Return sorted list for deterministic testing
        return sorted(list(set(valid_tags)))
