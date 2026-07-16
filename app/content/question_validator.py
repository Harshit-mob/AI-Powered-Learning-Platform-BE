import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SchemaValidator:
    """
    Validates the structural integrity of a question dictionary.
    Ensures required fields exist, are not empty, and arrays are actually arrays.
    Educational quality and bounds checking are deferred to the Quality Validator.
    """
    
    def validate(self, q: Dict[str, Any]) -> bool:
        """
        Validates a single question dictionary structurally.
        Returns True if valid, False if rejected.
        """
        try:
            # 1. Non-empty required strings
            if not str(q.get("question", "")).strip():
                logger.warning("Schema Validation Failed: question is missing or empty")
                return False
            if not str(q.get("expected_answer", "")).strip():
                logger.warning("Schema Validation Failed: expected_answer is missing or empty")
                return False
            if not str(q.get("question_type", "")).strip():
                logger.warning("Schema Validation Failed: question_type is missing")
                return False
            if not str(q.get("evaluation_method", "")).strip():
                logger.warning("Schema Validation Failed: evaluation_method is missing")
                return False

            # 2. Type checks
            if not isinstance(q.get("difficulty", 2), int):
                logger.warning("Schema Validation Failed: difficulty must be an integer")
                return False
            if not isinstance(q.get("estimated_answer_time", 5), int):
                logger.warning("Schema Validation Failed: estimated_answer_time must be an integer")
                return False

            # 3. Array checks
            modes = q.get("supported_answer_modes")
            if not isinstance(modes, list):
                logger.warning("Schema Validation Failed: supported_answer_modes is not an array")
                return False
            if not isinstance(q.get("acceptable_answers"), list):
                logger.warning("Schema Validation Failed: acceptable_answers is not an array")
                return False
            if not isinstance(q.get("keywords"), list):
                logger.warning("Schema Validation Failed: keywords is not an array")
                return False
            if not isinstance(q.get("mcq_options", []), list):
                logger.warning("Schema Validation Failed: mcq_options must be an array")
                return False

            # Passed structural checks
            return True
            
        except Exception as e:
            logger.error(f"Schema Validation threw an exception: {e}")
            return False
