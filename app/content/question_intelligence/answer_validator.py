import logging
from typing import Dict, Any, Tuple
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

class AnswerValidator:
    """
    Validates acceptable answers. Removes duplicates, normalizes capitalization,
    and rejects overly vague or contextually mismatched answers.
    """
    
    VAGUE_ANSWERS = {"everything", "anything", "all", "whatever"}
    
    def validate_and_repair(self, question: Dict[str, Any]) -> Tuple[bool, str]:
        repaired = False
        warnings = []
        
        q_text = str(question.get("text", "")).lower()
        q_type = str(question.get("question_type", "")).strip().upper()
        expected = str(question.get("expected_answer", "")).strip()
        acceptable = question.get("acceptable_answers", [])
        
        # 0. Deterministic Type / Complexity Heuristics
        expected_words = len(expected.split())
        complexity = "WORD"
        if expected_words > 3:
            complexity = "SHORT_PHRASE" if expected_words < 10 else "SENTENCE"
        
        # Enforce question type constraints based on answer length
        if q_type == "REASONING":
            reasoning_keywords = ["why", "how", "explain", "compare", "predict", "what would happen", "what conclusion"]
            has_reasoning_keyword = any(kw in q_text for kw in reasoning_keywords)
            is_one_word = (complexity == "WORD")
            is_yes_no = expected.lower() in ["yes", "no", "true", "false"]
            
            if is_one_word or is_yes_no or not has_reasoning_keyword:
                question["question_type"] = "RECALL"
                warnings.append(f"Downgraded REASONING to RECALL due to poor heuristics (word count={expected_words}, yes_no={is_yes_no}, has_keyword={has_reasoning_keyword})")
                repaired = True
                
        if not isinstance(acceptable, list):
            acceptable = []
            
        new_acceptable = []
        seen = {expected.lower()} # Don't allow duplicates of expected answer
        
        for ans in acceptable:
            ans_str = str(ans).strip()
            if not ans_str:
                continue
                
            ans_lower = ans_str.lower()
            
            # 1. Reject vague answers
            if ans_lower in self.VAGUE_ANSWERS:
        seen = set()
        
        # 5. Synthesize natural spoken variants for the expected answer
        # The user requested natural spoken variants (e.g. "Science" -> "The science", "It is science", "Science is the answer")
        # We completely OVERWRITE any LLM-provided synonyms to strictly reject unrelated synonyms.
        if expected and expected.lower() not in ["true", "false", "yes", "no"]:
            natural_variants = [
                expected,
                f"The {expected.lower()}",
                f"It is {expected.lower()}",
        exp_lower = expected.lower()
        variants = set()
        variants.add(f"the {exp_lower}")
        variants.add(f"it is {exp_lower}")
        variants.add(f"{exp_lower} is the answer")
        
        # If it's a verb (ends with 'ing' or 'tion'), add natural spoken versions
        if exp_lower.endswith("tion"):
            base = exp_lower[:-4]
            variants.add(f"{base}ing carefully")
            variants.add(f"by {base}ing")
            variants.add(f"we {base}")
            
        for variant in variants:
            if variant.lower() not in seen:
                new_acceptable.append(variant.capitalize() if len(variant.split()) > 3 else variant.title())
                seen.add(variant.lower())
                repaired = True
                warnings.append(f"Synthesized natural variant: {variant}")
        
        question["acceptable_answers"] = new_acceptable
        
        if repaired:
            return True, "; ".join(warnings)
        return True, ""
