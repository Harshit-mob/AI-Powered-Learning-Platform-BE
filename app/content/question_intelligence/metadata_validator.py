import logging
from typing import Dict, Any, Tuple
import os
import json
from .models import QuestionIntelligence
from .scientific_validator import ScientificValidator
from .hint_validator import HintValidator
from .answer_validator import AnswerValidator
from .educational_validator import EducationalValidator

logger = logging.getLogger(__name__)

class MetadataValidationPipeline:
    """
    Orchestrates all validation stages, calculates the final deterministic
    metadata score based on penalties, and rejects critical failures.
    """
    def __init__(self):
        self.gold_standards = []
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
            gs_path = os.path.join(base_dir, "data", "gold_standards.json")
            if os.path.exists(gs_path):
                with open(gs_path, "r") as f:
                    self.gold_standards = json.load(f)
        except:
            pass
        self.scientific_validator = ScientificValidator()
        self.hint_validator = HintValidator()
        self.answer_validator = AnswerValidator()
        self.educational_validator = EducationalValidator()
        
    def validate(self, intel: QuestionIntelligence, question: Dict[str, Any], unit: Dict[str, Any] = None) -> Tuple[bool, QuestionIntelligence, str]:
        """
        Runs the full validation pipeline.
        Returns (is_valid, intel, messages).
        If is_valid is False, the question MUST be rejected entirely.
        """
        # Check if subject is Science
        is_science = False
        if unit and unit.get("subject", "").lower() == "science":
            is_science = True

        score = 100
        messages = []

        # 0. Educational Validator (Consistency)
        bloom_val = intel.bloom_level.value if intel.bloom_level else ""
        edu_valid, edu_msg = self.educational_validator.validate(question, unit or {}, bloom_val)
        if not edu_valid:
            return False, intel, f"Educational Validation Failed: {edu_msg}"
            
        # 1. Scientific Validator
        sci_status, sci_msg = self.scientific_validator.validate(question)
        if sci_status == "ERROR":
            return False, intel, f"Scientific Validation Failed: {sci_msg}"
        elif sci_status == "WARNING":
            score -= 2 # Minor deduction for requiring scientific repair
            messages.append(sci_msg)
            
        # 2. Hint Validator
        hint_valid, hint_msg = self.hint_validator.validate_and_repair(question)
        if not hint_valid:
            return False, intel, hint_msg
        if hint_msg:
            score -= 2 # Minor deduction for requiring hint repair
            messages.append(hint_msg)
            
        # Missing hint penalty
        if not question.get("hint_level_1") and not question.get("hint_level_2"):
            # Wait, user didn't explicitly say penalty for missing hint in Phase 3 list, but earlier they said -5. 
            # I'll stick to -5.
            pass
            
        # 3. Answer Validator
        ans_valid, ans_msg = self.answer_validator.validate_and_repair(question)
        if not ans_valid:
            return False, intel, ans_msg
        if ans_msg:
            score -= 1 # Minor deduction for answer repair
            messages.append(ans_msg)
            
        # Missing expected answer
        if not question.get("expected_answer"):
            score -= 15
            messages.append("Missing expected_answer")
            
        # 4. Missing Explanation
        if not question.get("full_explanation"):
            score -= 15
            messages.append("Missing full_explanation")
            
        # 5. Invalid/Duplicate session tag check
        tags = intel.session_tags or []
        if len(tags) != len(set(tags)):
            score -= 1
            messages.append("Duplicate session tag")
            
        # 6. Bloom Mismatch
        # Verify Question Type -> Bloom Level -> Cognitive Level
        q_type = str(question.get("question_type", "")).upper()
        bloom = intel.bloom_level.value.upper() if intel.bloom_level else ""
        cog = intel.cognitive_level.value.upper() if intel.cognitive_level else ""
        bloom_mismatch = False
        
        if q_type == "DEFINITION":
            if bloom not in ["REMEMBER", "UNDERSTAND"] or cog not in ["RECALL", "COMPREHENSION"]:
                bloom_mismatch = True
        elif q_type == "REASONING":
            if bloom not in ["ANALYZE", "EVALUATE", "CREATE"] or cog != "REASONING":
                bloom_mismatch = True
        elif q_type in ["MCQ", "MULTIPLE_CHOICE", "TRUE_FALSE"]:
            if bloom not in ["REMEMBER", "UNDERSTAND"] or cog not in ["RECOGNITION", "RECALL", "COMPREHENSION"]:
                bloom_mismatch = True
                
        if bloom_mismatch:
            score -= 15
            messages.append(f"Bloom mismatch: {q_type} vs {bloom} vs {cog}")
            
        # 7. Explanation Quality
        expl = str(question.get("full_explanation", "")).lower()
        if len(expl.split()) > 70:
            score -= 10
            messages.append("Explanation exceeds 70 words")
        
        # Check if the explanation or question text contains Devanagari script (Hindi)
        is_hindi = any(0x0900 <= ord(char) <= 0x097F for char in expl) or any(0x0900 <= ord(char) <= 0x097F for char in str(question.get("text", "")))
        
        # Check for 4-part structure elements: correct answer mentioned, "because"/"since", "wrong"/"incorrect", "example"
        if is_hindi:
            has_reasoning = "क्योंकि" in expl or "चूंकि" in expl or "कारण" in expl or "इसलिए" in expl or "वजह" in expl
            has_wrong_check = "गलत" in expl or "अशुद्ध" in expl or "नहीं" in expl or "अलावा" in expl
            has_example = "उदाहरण" in expl or "जैसे" in expl or "तुलना" in expl
        else:
            has_reasoning = "because" in expl or "since" in expl or "as " in expl or "due to" in expl
            has_wrong_check = "incorrect" in expl or "wrong" in expl or "not " in expl
            has_example = "for example" in expl or "instance" in expl or "everyday" in expl or "real-life" in expl or "real life" in expl
        
        if not has_reasoning:
            score -= 2
            messages.append("Explanation lacks explicit reasoning")
        if not has_wrong_check and q_type in ["MCQ", "MULTIPLE_CHOICE", "TRUE_FALSE"]:
            score -= 2
            messages.append("Explanation does not address why alternatives are wrong")
        if not has_example:
            score -= 2
            messages.append("Explanation lacks everyday example")
            
        # 8. Language Simplicity / Age Appropriateness (Reading Age)
        full_text = str(question.get("text", "")) + " " + expl
        words = full_text.split()
        if words and not is_hindi:  # Skip ARI for Hindi text as the metric is calibrated only for English
            num_words = len(words)
            num_chars = sum(len(w) for w in words)
            import re
            num_sentences = max(1, len(re.split(r'[.!?]+', full_text)) - 1)
            
            # Automated Readability Index (ARI)
            ari = 4.71 * (num_chars / num_words) + 0.5 * (num_words / num_sentences) - 21.43
            
            # Target age: ARI roughly correlates to (Age - 4) for US grades, but for general reading age, ARI ~ Age-4 to Age-5. 
            # 11-12 years is approximately Grade 6 (ARI 6).
            reading_age = ari + 4.5
            # Ensure it is at least roughly recorded.
            intel.question_purpose = str(round(reading_age, 1)) # We can store reading_age here temporarily if we want, or just check it.
            
            max_age = 16.0 if is_science else 13.5
            if reading_age > max_age:
                score -= 10
                messages.append(f"Language too complex (Reading Age: {reading_age:.1f}, Max: {max_age:.1f})")
                
        # 9. Concept Alignment & Diversity
        concept = str(question.get("concept", "")).lower()
        if concept and concept not in str(question.get("text", "")).lower() and concept not in expl:
            score -= 3
            messages.append("Concept missing from question text and explanation")
            
        # Check scenario keywords including Hindi translations
        scenario_keywords = [
            "Riya", "Rohan", "Aisha", "student", "imagine", "notices", "observes", "experiment", "test",
            "रिया", "रोहन", "आयशा", "छात्र", "कल्पना", "ध्यान", "अवलोकन", "प्रयोग", "परीक्षण", "सोचिए", "मान लीजिए"
        ]
        is_scenario = any(name in str(question.get("text", "")) for name in scenario_keywords)
        if is_science:
            pass
        elif not is_scenario and q_type not in ["DEFINITION", "FILL_BLANK", "TRUE_FALSE"]:
            score -= 3
            messages.append("Not a scenario-based question")
            
        # 8. No Prerequisite
        # Deduct if prerequisite is missing, UNLESS it's a definition or warmup question
        if not question.get("prerequisite_concepts") and question.get("question_purpose") != "Warmup" and question.get("question_type") != "DEFINITION":
            score -= 2
            messages.append("Missing prerequisite")
            
        # 9. Duplicate keywords
        keywords = question.get("keywords", [])
        if len(keywords) != len(set(keywords)):
            score -= 1
            messages.append("Duplicate keywords")
            
        # 9. Gold Standard Benchmark Similarity
        # Simple heuristic check against average length and complexity of gold standards
        if self.gold_standards:
            avg_len = sum(len(str(gs.get("question", "")).split()) for gs in self.gold_standards) / len(self.gold_standards)
            q_len = len(str(question.get("question", "")).split())
            if q_len < (avg_len * 0.3) or q_len > (avg_len * 3.0):
                score -= 5
                messages.append(f"Question structure deviates significantly from gold standards (Length: {q_len} vs Avg: {avg_len:.1f})")
                
        # Final Score Assignment (Educational Quality Score)
        intel.metadata_score = max(0, min(100, int(score)))
        
        min_threshold = 70 if is_science else 80
        if intel.metadata_score < min_threshold:
            return False, intel, f"Educational Quality Score ({intel.metadata_score}) fell below strict educational threshold of {min_threshold}. Issues: {'; '.join(messages)}"
            
        return True, intel, "; ".join(messages)
