import logging
from typing import Dict, Any

from .validation_models import ValidationResult, ValidationSeverity, ValidationIssue, QualityConfig
from .duplicate_analyzer import DuplicateAnalyzer
from .question_quality_analyzer import QuestionQualityAnalyzer

logger = logging.getLogger(__name__)

VALID_QUESTION_TYPES = {
    "DEFINITION", "RECALL", "UNDERSTANDING", "APPLICATION", "OBSERVATION", 
    "REASONING", "COMPARISON", "COMPARE", "CAUSE_EFFECT", "TRUE_FALSE", "FILL_BLANK", "MCQ"
}

class QuestionValidator:
    def __init__(self, config: QualityConfig, duplicate_analyzer: DuplicateAnalyzer, quality_analyzer: QuestionQualityAnalyzer):
        self.config = config
        self.duplicate_analyzer = duplicate_analyzer
        self.quality_analyzer = quality_analyzer

    def validate(self, q: Dict[str, Any], unit_diversity_count: int) -> ValidationResult:
        issues = []
        is_valid = True
        
        q_text = str(q.get("question", "")).strip()
        expected_ans = str(q.get("expected_answer", "")).strip()
        
        if not q_text:
            issues.append(ValidationIssue("EMPTY_QUESTION", ValidationSeverity.CRITICAL, "Question text is empty."))
            is_valid = False
            
        if not expected_ans:
            issues.append(ValidationIssue("EMPTY_ANSWER", ValidationSeverity.CRITICAL, "Expected answer is empty."))
            is_valid = False
            
        q_type = str(q.get("question_type", "")).strip().upper().replace(" ", "_").replace("/", "_")
        q["question_type"] = q_type
        if q_type not in VALID_QUESTION_TYPES:
            issues.append(ValidationIssue("INVALID_TYPE", ValidationSeverity.CRITICAL, f"Unknown question_type: {q_type}"))
            is_valid = False
            
        if self.duplicate_analyzer.check_duplicate(q):
            issues.append(ValidationIssue("DUPLICATE", ValidationSeverity.CRITICAL, "Duplicate question detected."))
            is_valid = False
            
        # Answer Validation
        acc_answers = q.get("acceptable_answers", [])
        if not acc_answers:
            issues.append(ValidationIssue("NO_ACCEPTABLE_ANSWERS", ValidationSeverity.CRITICAL, "No acceptable answers provided."))
            is_valid = False
        else:
            min_required = 1 if q_type == "MCQ" else 2
            if len(acc_answers) < min_required:
                issues.append(ValidationIssue("FEW_ANSWERS", ValidationSeverity.CRITICAL, f"Minimum {min_required} acceptable answers required."))
                is_valid = False
            elif len(acc_answers) < 5 and q_type != "MCQ":
                issues.append(ValidationIssue("FEW_ANSWERS_RECOMMENDATION", ValidationSeverity.INFO, "Recommend 5-10 acceptable answers for voice friendliness."))
                
            norm_acc_ans = [a.strip().lower() for a in acc_answers]
            if len(norm_acc_ans) != len(set(norm_acc_ans)):
                issues.append(ValidationIssue("DUPLICATE_ANSWERS", ValidationSeverity.CRITICAL, "Duplicate acceptable answers detected."))
                is_valid = False
            if expected_ans.strip().lower() not in norm_acc_ans:
                issues.append(ValidationIssue("MISSING_EXPECTED", ValidationSeverity.CRITICAL, "Expected answer not found in acceptable answers."))
                is_valid = False
                
        # Length check
        wc = len(q_text.split())
        if wc > self.config.max_question_words:
            issues.append(ValidationIssue("QUESTION_LONG", ValidationSeverity.WARNING, f"Question is long ({wc} words). Max is {self.config.max_question_words}."))
        elif wc < 6:
            issues.append(ValidationIssue("QUESTION_SHORT", ValidationSeverity.WARNING, "Question is very short."))
            
        exp = str(q.get("full_explanation", "")).strip()
        exp_wc = len(exp.split())
        if exp_wc > 60:
            issues.append(ValidationIssue("EXPLANATION_LONG", ValidationSeverity.WARNING, f"Explanation is long ({exp_wc} words)."))
            
        if "MCQ" in q.get("supported_answer_modes", []) or q_type == "MCQ":
            options = q.get("mcq_options", [])
            if len(options) != 4:
                issues.append(ValidationIssue("INVALID_MCQ", ValidationSeverity.CRITICAL, "MCQ must have exactly 4 options."))
                is_valid = False
                
        quality_score = self.quality_analyzer.analyze(q, unit_diversity_count)
        
        overall_severity = ValidationSeverity.CRITICAL if not is_valid else (ValidationSeverity.WARNING if any(i.severity == ValidationSeverity.WARNING for i in issues) else ValidationSeverity.INFO)
        
        return ValidationResult(
            valid=is_valid,
            severity=overall_severity,
            quality_score=quality_score,
            issues=issues
        )
