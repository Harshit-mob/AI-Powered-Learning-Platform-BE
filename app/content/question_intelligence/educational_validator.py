import re
from typing import Dict, Any, Tuple

class EducationalValidator:
    """
    Validates semantic consistency between the question text, concept, and learning objective.
    Uses deterministic keyword overlap.
    """
    
    STOPWORDS = {"of", "the", "in", "and", "a", "an", "to", "for", "on", "with", "is", "what", "meaning", "definition", "are", "how", "why", "do", "does", "did", "can", "could", "will", "would", "should"}
    
    def validate(self, question: Dict[str, Any], unit: Dict[str, Any], bloom_level: str = "") -> Tuple[bool, str]:
        """
        Returns (is_valid, warning_message).
        """
        # 1. Validate Question Type vs Bloom
        q_type = str(question.get("question_type", "")).upper()
        bloom = bloom_level.upper() if bloom_level else ""
        
        if bloom and q_type:
            if q_type in ["RECALL", "DEFINITION", "FILL_BLANK"] and bloom in ["APPLY", "ANALYZE", "EVALUATE", "CREATE"]:
                return False, f"Invalid combination: {q_type} + Bloom {bloom}"
            if q_type in ["TRUE_FALSE", "MCQ", "MULTIPLE_CHOICE"] and bloom in ["CREATE", "EVALUATE"]:
                return False, f"Invalid combination: {q_type} + Bloom {bloom}"
                
        # 1.4 Concept Mastery Mapping
        concept = str(question.get("concept", "")).lower()
        diff = int(question.get("difficulty", 1))
        if diff < 5 and (" and " in concept or "," in concept or "&" in concept):
            if len(concept.split()) > 3: # E.g. "Scientific method and variables"
                return False, f"Mixed concepts detected in non-Level 5 question: {concept}. Questions must measure exactly one primary concept."
                
        # 1.5 Distractor & Format Quality Engine
        mcq_options = question.get("mcq_options", [])
        modes = question.get("supported_answer_modes", [])
        
        # Enforce supported modes for MCQ/TRUE_FALSE
        if q_type in ["MCQ", "MULTIPLE_CHOICE", "TRUE_FALSE"]:
            if modes != ["MCQ"] and modes != ["mcq"]:
                return False, f"MCQ or TRUE_FALSE questions must have exactly ['MCQ'] as supported_answer_modes. Found: {modes}"
                
        # Enforce that options are not leaked in the question text
        q_text = str(question.get("text", ""))
        q_text_lower = q_text.lower()
        
        # Check for option letter patterns like 'a.', 'b.', 'a)', 'b)' in question text
        option_patterns = [r'\b[a-d]\.\s', r'\b[a-d]\)\s', r'\b[1-4]\.\s', r'\b[1-4]\)\s']
        for pat in option_patterns:
            if re.search(pat, q_text_lower):
                return False, f"Question text must not contain option lists or letters (e.g., 'a.', 'b.'). Found pattern match in: {q_text}"
                
        if q_type in ["MCQ", "MULTIPLE_CHOICE"] and mcq_options:
            expected = str(question.get("expected_answer", "")).lower()
            correct_opt = str(question.get("correct_option", "")).lower()
            
            # Check if any mcq option string is embedded in the question text as a list
            for opt in mcq_options:
                opt_str = str(opt).strip()
                if len(opt_str) > 3 and f"\n{opt_str}" in q_text:
                    return False, f"MCQ options must not be appended to the question text: '{opt_str}' found in question text."
            
            # Check if expected_answer or correct_option matches one of the options
            has_expected_match = any(str(opt).lower() == expected for opt in mcq_options)
            has_correct_match = any(str(opt).lower() == correct_opt for opt in mcq_options)
            
            if not has_expected_match and not has_correct_match:
                return False, f"MCQ expected_answer or correct_option must exactly match one of the options in mcq_options: {mcq_options}"
                
            distractors = [opt for opt in mcq_options if str(opt).lower() != expected]
            obvious_distractors = ["apple", "car", "sleeping", "nothing", "magic", "pizza", "ghost"]
            for dist in distractors:
                if str(dist).lower() in obvious_distractors or len(str(dist)) < 2:
                    return False, f"Obvious or invalid distractor detected: {dist}"
        text = q_text_lower
        concept = str(question.get("concept", "")).lower()
        learning_objective = str(unit.get("learning_objective", "")).lower() if unit else ""
        
        # If we don't have a learning objective to compare to, we can't do this validation.
        if not learning_objective:
            return True, ""
            
        def extract_tokens(s: str) -> set:
            # Remove punctuation
            s = re.sub(r'[^\w\s]', '', s)
            tokens = set(s.split())
            return tokens - self.STOPWORDS
            
        lo_tokens = extract_tokens(learning_objective)
        text_tokens = extract_tokens(text)
        concept_tokens = extract_tokens(concept)
        
        if not lo_tokens:
            return True, "" # Can't validate against an empty/stopword-only LO
            
        # We want to ensure the question OR the concept has at least ONE meaningful word in common with the learning objective.
        # For Hindi and Gujarati, we bypass this strict check to prevent false-positive rejections due to translation/inflection differences.
        is_indic_content = any(
            (0x0900 <= ord(char) <= 0x097F) or (0x0a80 <= ord(char) <= 0x0aff)
            for char in text + concept + learning_objective
        )
        if is_indic_content:
            return True, ""
            
        # Relax check for English grammar and vocabulary questions
        grammar_keywords = {"pronoun", "noun", "tense", "subject", "predicate", "verb", "grammar", "adjective", "preposition", "synonym", "antonym", "vocabulary", "word", "singular", "plural"}
        if any(gk in concept or gk in text for gk in grammar_keywords):
            return True, ""

        overlap_with_text = lo_tokens.intersection(text_tokens)
        overlap_with_concept = lo_tokens.intersection(concept_tokens)
        
        if not overlap_with_text and not overlap_with_concept:
            # Maybe the full explanation has it? Let's check as a last resort.
            explanation = str(question.get("full_explanation", "")).lower()
            exp_tokens = extract_tokens(explanation)
            if not lo_tokens.intersection(exp_tokens):
                return False, "Semantic Mismatch: Question does not align with the learning objective."
                
        return True, ""
