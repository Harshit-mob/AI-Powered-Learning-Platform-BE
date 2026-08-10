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
        
        # Repair MCQ expected_answer / correct_option mismatch
        if q_type in ["MCQ", "MULTIPLE_CHOICE"]:
            mcq_options = question.get("mcq_options", [])
            if mcq_options:
                correct_opt = str(question.get("correct_option", "")).strip()
                # Find if there is an exact match already
                exact_expected = next((opt for opt in mcq_options if str(opt).lower() == expected.lower()), None)
                exact_correct = next((opt for opt in mcq_options if str(opt).lower() == correct_opt.lower()), None)
                
                if exact_expected:
                    if expected != exact_expected:
                        expected = exact_expected
                        question["expected_answer"] = expected
                        repaired = True
                if exact_correct:
                    if correct_opt != exact_correct:
                        question["correct_option"] = exact_correct
                        repaired = True
                        
                # If neither matched exactly, find the closest option by similarity
                if not exact_expected and not exact_correct:
                    best_match = None
                    best_score = 0.0
                    for opt in mcq_options:
                        opt_str = str(opt)
                        # Sequence Matcher similarity
                        sim = SequenceMatcher(None, opt_str.lower(), expected.lower()).ratio()
                        # Give extra weight if it is a complete substring of expected or vice-versa
                        if opt_str.lower() in expected.lower() or expected.lower() in opt_str.lower():
                            sim += 0.5
                        if sim > best_score:
                            best_score = sim
                            best_match = opt_str
                    
                    if best_match and (best_score > 0.4):
                        expected = best_match
                        question["expected_answer"] = best_match
                        question["correct_option"] = best_match
                        repaired = True
                        warnings.append(f"Mapped MCQ answer to closest option '{best_match}'")
        
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
                
        import re
        if not isinstance(acceptable, list):
            acceptable = []
            
        new_acceptable = []
        # Clean expected first
        expected_cleaned = re.sub(r'^[.,?!;:"\'\-\s]+', '', expected)
        expected_cleaned = re.sub(r'[.,?!;:"\'\-\s]+$', '', expected_cleaned).strip()
        seen = {expected_cleaned.lower()} # Don't allow duplicates of expected answer
        
        for ans in acceptable:
            ans_str = str(ans).strip()
            if not ans_str:
                continue
            
            # Strip trailing/leading punctuation
            ans_str = re.sub(r'^[.,?!;:"\'\-\s]+', '', ans_str)
            ans_str = re.sub(r'[.,?!;:"\'\-\s]+$', '', ans_str).strip()
            if not ans_str:
                continue
                
            ans_lower = ans_str.lower()
            
            # 1. Reject vague answers
            if ans_lower in self.VAGUE_ANSWERS:
                continue
                
            if ans_lower not in seen:
                new_acceptable.append(ans_str)
                seen.add(ans_lower)
        
        # 5. Synthesize natural spoken variants for the expected answer
        # The user requested natural spoken variants (e.g. "Science" -> "The science", "It is science", "Science is the answer")
        # We MERGE LLM-provided synonyms with synthesized variants instead of completely overwriting.
        if expected_cleaned and expected_cleaned.lower() not in ["true", "false", "yes", "no"]:
            exp_lower = expected_cleaned.lower()
            variants = set()
            
            # Detect Hindi (Devanagari script)
            is_hindi_ans = any(0x0900 <= ord(char) <= 0x097F for char in exp_lower)
            
            if is_hindi_ans:
                variants.add(f"उत्तर {exp_lower} है")
                variants.add(f"सही उत्तर {exp_lower} है")
                variants.add(f"यह {exp_lower} है")
            else:
                variants.add(f"the {exp_lower}")
                variants.add(f"it is {exp_lower}")
                variants.add(f"{exp_lower} is the answer")
                variants.add(f"its {exp_lower}")
                
                # If it's a verb (ends with 'ing' or 'tion'), add natural spoken versions
                if exp_lower.endswith("tion"):
                    base = exp_lower[:-4]
                    variants.add(f"{base}ing carefully")
                    variants.add(f"by {base}ing")
                    variants.add(f"we {base}")
                
            for variant in variants:
                if variant.lower() not in seen:
                    # For Hindi we don't need title case / capitalize as it does not apply
                    val = variant if is_hindi_ans else (variant.capitalize() if len(variant.split()) > 3 else variant.title())
                    new_acceptable.append(val)
                    seen.add(variant.lower())
                    repaired = True
                    warnings.append(f"Synthesized natural variant: {variant}")
        
        question["expected_answer"] = expected_cleaned
        question["acceptable_answers"] = new_acceptable
        
        if repaired:
            return True, "; ".join(warnings)
        return True, ""
