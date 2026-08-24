import re
from typing import Any
from app.assessment.models.dto import AnswerSubmission, EvaluationResult

def normalize_text(text: str) -> str:
    if not text:
        return ""
    # Lowercase and convert to string
    normalized = str(text).lower().strip()
    # Replace internal hyphens/dashes with spaces
    normalized = normalized.replace("-", " ")
    # Remove leading/trailing punctuation commonly found in sentences/voice transcripts
    normalized = re.sub(r'^[.,?!;:"\'\(\)\-\s]+', '', normalized)
    normalized = re.sub(r'[.,?!;:"\'\(\)\-\s]+$', '', normalized)
    # Strip common leading voice fillers
    fillers = [
        r"^it's\s+", r"^it\s+is\s+", r"^the\s+answer\s+is\s+", r"^answer\s+is\s+", 
        r"^i\s+think\s+it\s+is\s+", r"^my\s+answer\s+is\s+", r"^the\s+", r"^a\s+", r"^an\s+", r"^its\s+"
    ]
    for filler in fillers:
        normalized = re.sub(filler, '', normalized)
    # Normalize internal whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized.strip()

def is_truthy(text: str) -> bool:
    t = normalize_text(text)
    return any(val in t for val in ["true", "yes", "correct", "right", "yup", "yeah", "हाँ", "સાચું", "साचु"])

def is_falsy(text: str) -> bool:
    t = normalize_text(text)
    return any(val in t for val in ["false", "no", "incorrect", "wrong", "nope", "nah", "नहीं", "ખોટું", "ખોટુ"])

def check_keyword_overlap(provided: str, expected: str) -> bool:
    provided_words = set(provided.split())
    expected_words = [w for w in expected.split() if len(w) > 2 and w not in ["the", "and", "for", "are", "was", "were", "they", "with", "from"]]
    if not expected_words:
        return False
    matched = 0
    for ew in expected_words:
        # Check for stem-level matching (e.g. 'go' in 'going')
        if len(ew) >= 4 and any(ew[:2] in pw for pw in provided_words if len(pw) >= 4):
            matched += 1
        elif any(ew in pw or pw in ew for pw in provided_words):
            matched += 1
    return (matched / len(expected_words)) >= 0.8

class EvaluationEngine:
    def evaluate(self, submission: AnswerSubmission, expected_answer: Any, question_type: str, acceptable_answers: list = None) -> EvaluationResult:
        """
        Evaluates a submitted answer deterministically.
        Does not interact with repositories or mastery engine.
        """
        is_correct = False
        score = 0.0
        evaluation_method = "EXACT_MATCH"
        matched_answer = str(submission.provided_answer)
        
        q_type_upper = str(question_type).upper()
        
        if q_type_upper != "VOICE_MATCH":
            # Check for boolean True/False evaluation first
            if q_type_upper == "TRUE_FALSE" or q_type_upper == "BOOLEAN":
                expected_str = str(expected_answer)
                provided_str = str(submission.provided_answer)
                if is_truthy(expected_str) and is_truthy(provided_str):
                    is_correct = True
                    score = 1.0
                elif is_falsy(expected_str) and is_falsy(provided_str):
                    is_correct = True
                    score = 1.0
            
            if not is_correct:
                expected = normalize_text(expected_answer)
                provided = normalize_text(submission.provided_answer)
                
                acceptables = [expected]
                if acceptable_answers:
                    acceptables.extend([normalize_text(a) for a in acceptable_answers])
                    
                for acc in acceptables:
                    if acc and provided == acc:
                        is_correct = True
                        score = 1.0
                        break
                    elif acc and acc in provided:
                        # For short-answers/recalls/voice, containing the answer makes it fully correct
                        if q_type_upper not in ["FILL_BLANK", "FILL_IN_THE_BLANK"]:
                            is_correct = True
                            score = 1.0
                            evaluation_method = "EXACT_MATCH"
                            break
                        else:
                            is_correct = True
                            score = 0.5
                            evaluation_method = "PARTIAL_MATCH"
                    elif acc and q_type_upper not in ["FILL_BLANK", "FILL_IN_THE_BLANK"] and check_keyword_overlap(provided, acc):
                        # Student spoke all the main key words (e.g. 'going to school' instead of 'goes to school')
                        is_correct = True
                        score = 1.0
                        evaluation_method = "EXACT_MATCH"
                        break
                    elif acc and provided in acc:
                        # Student spoke a subset of the correct answer
                        is_correct = True
                        score = 0.8
                        evaluation_method = "PARTIAL_MATCH"
                
                # Re-check if we found an exact match to override partial
                if score == 1.0:
                    evaluation_method = "EXACT_MATCH"
        # Voice match and others would use specialized deterministic routines
        elif question_type == "VOICE_MATCH":
            is_correct = True if submission.confidence_rating and submission.confidence_rating > 0.8 else False
            score = submission.confidence_rating or 0.0
            evaluation_method = "VOICE_CONFIDENCE"
            
        return EvaluationResult(
            session_id=submission.session_id,
            question_id=submission.question_id,
            student_id=submission.student_id,
            is_correct=is_correct,
            evaluation_score=score,
            evaluation_method=evaluation_method,
            matched_answer=matched_answer,
            voice_score=submission.confidence_rating,
            response_time=submission.time_taken_seconds,
            hints_used=submission.hints_used
        )
