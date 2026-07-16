from typing import Dict, Any

class DataCleaner:
    """
    Deterministically cleans and sanitizes core question data fields without AI generation.
    """
    
    def clean(self, question: Dict[str, Any]):
        self._clean_hints(question)
        self._clean_acceptable_answers(question)
        self._clean_evaluation_method(question)
        self._clean_keywords(question)
        self._simplify_language(question)
        return question
        
    def _simplify_language(self, question: Dict[str, Any]):
        replacements = {
            "systematically": "carefully",
            "systematically observe": "look carefully at",
            "therefore": "so",
            "consequently": "so",
            "employ": "use",
            "demonstrate": "show",
            "demonstrates": "shows",
            "utilize": "use",
            "facilitate": "help",
            "comprehensive": "full",
            "acquire": "get"
        }
        import re
        for field in ["text", "question", "full_explanation", "hint_level_1", "hint_level_2"]:
            text = question.get(field, "")
            if isinstance(text, str) and text:
                for acad, simple in replacements.items():
                    text = re.sub(rf"\b{acad}\b", simple, text, flags=re.IGNORECASE)
                question[field] = text
        
    def _clean_keywords(self, question: Dict[str, Any]):
        keywords = question.get("keywords", [])
        if not isinstance(keywords, list):
            keywords = []
        
        # Lowercase, deduplicate, sort
        seen = set()
        cleaned = []
        
        banned = {"the", "a", "an", "is", "of", "to", "it", "they", "we", "he", "she", "you", "i", "what", "how", "why"}
        expected = str(question.get("expected_answer", "")).strip().lower()
        
        # 1. Primary concept
        concept = str(question.get("concept", "")).strip().lower()
        if concept and concept not in banned and concept != expected:
            cleaned.append(concept)
            seen.add(concept)
            
        # 2. Important nouns/verbs from original keywords
        for k in keywords:
            k_lower = str(k).strip().lower()
            if not k_lower or k_lower in banned or k_lower == expected or expected in k_lower:
                continue
            if k_lower not in seen:
                cleaned.append(k_lower)
                seen.add(k_lower)
                
            if len(cleaned) >= 5:
                break
                
        question["keywords"] = cleaned[:5]

    def _clean_hints(self, question: Dict[str, Any]):
        bad_phrases = ["starts with letter", "starts with the letter", "think carefully", "the answer is"]
        
        for level in ["hint_level_1", "hint_level_2"]:
            hint = str(question.get(level, ""))
            hint_lower = hint.lower()
            
            if any(p in hint_lower for p in bad_phrases):
                # We replace poor, structural hints with generic guiding hints
                if level == "hint_level_1":
                    question[level] = "Review the core concepts related to this topic to find the answer."
                else:
                    question[level] = "Consider how this concept applies in a practical scenario."
                    
    def _clean_acceptable_answers(self, question: Dict[str, Any]):
        acc = question.get("acceptable_answers", [])
        expected = str(question.get("expected_answer", "")).strip()
        
        if not isinstance(acc, list):
            return
            
        clean_acc = []
        for a in acc:
            a_lower = str(a).lower().strip()
            expected_lower = expected.lower()
            
            # Remove redundant long definitions if expected is short
            if len(a_lower.split()) > len(expected_lower.split()) + 2:
                continue
                
            clean_acc.append(str(a).strip())
            
        if expected and expected.lower() not in [c.lower() for c in clean_acc]:
            clean_acc.insert(0, expected)
            
        question["acceptable_answers"] = list(set(clean_acc))
        
    def _clean_evaluation_method(self, question: Dict[str, Any]):
        q_type = str(question.get("question_type", "")).upper()
        complexity = str(question.get("answer_complexity", "")).upper()
        
        # Priority 6 rules:
        if q_type == "MCQ" or q_type == "MULTIPLE_CHOICE":
            question["evaluation_method"] = "MCQ"
            return
        if q_type == "TRUE_FALSE":
            question["evaluation_method"] = "BOOLEAN"
            return
            
        if complexity == "SINGLE_WORD" or complexity == "WORD":
            question["evaluation_method"] = "WORD_MATCH"
            return
            
        if complexity == "SHORT_PHRASE" or complexity == "PHRASE":
            question["evaluation_method"] = "KEYWORD_MATCH"
            return
            
        if complexity in ["SENTENCE", "LONG_REASONING", "COMPLEX_EXPLANATION"]:
            question["evaluation_method"] = "SEMANTIC_MATCH"
            return
            
        # Fallback based on question type
        if q_type == "FILL_BLANK":
            question["evaluation_method"] = "WORD_MATCH"
        else:
            question["evaluation_method"] = "SEMANTIC_MATCH"
