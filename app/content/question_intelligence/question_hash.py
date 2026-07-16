import hashlib
import logging
from typing import Dict, Any

from .models import EducationalIntent
from .utils import normalize_text

logger = logging.getLogger(__name__)

class QuestionHasher:
    """
    Generates a stable, unique SHA-256 hash for a question using core semantic fields.
    """
    def generate_hash(self, question: Dict[str, Any], intent: EducationalIntent) -> str:
        unit_id = str(question.get("learning_unit_id", "")).strip()
        concept = normalize_text(str(question.get("concept", "")))
        q_text = normalize_text(str(question.get("question", "")))
        q_type = str(question.get("question_type", "")).strip().upper()
        intent_val = intent.value
        
        # Stable concatenated payload
        payload = f"{unit_id}|{concept}|{q_text}|{q_type}|{intent_val}"
        
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()
