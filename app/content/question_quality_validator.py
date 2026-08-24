import logging
import re
from typing import Dict, Any
from collections import defaultdict
from functools import lru_cache

logger = logging.getLogger(__name__)

VALID_QUESTION_TYPES = {
    "DEFINITION", "RECALL", "UNDERSTANDING", "APPLICATION", "OBSERVATION", 
    "REASONING", "COMPARISON", "COMPARE", "CAUSE_EFFECT", "TRUE_FALSE", "FILL_BLANK", "MCQ"
}

TYPE_DIFFICULTY_BOUNDS = {
    "DEFINITION": (1, 1),
    "RECALL": (1, 2),
    "UNDERSTANDING": (2, 2),
    "APPLICATION": (3, 3),
    "REASONING": (3, 4),
    "COMPARISON": (3, 3),
    "COMPARE": (3, 3),
    "CAUSE_EFFECT": (3, 3),
    "TRUE_FALSE": (1, 2),
    "FILL_BLANK": (1, 2),
    "MCQ": (1, 3)
}

class QuestionQualityValidator:
    """
    Validates question educational quality, voice-first constraints, diversity, and duplicates.
    Pure Python logic with no AI calls.
    """
    def __init__(self):
        self._pattern = re.compile(r'[^\w\s]')
        # Tracker for duplicates: dict of unit_id -> set of signature strings
        self._seen_signatures = defaultdict(set)
        
        # Tracker for diversity: dict of unit_id -> dict of question_type -> count
        self._type_counts = defaultdict(lambda: defaultdict(int))
        
        self.stats = {
            "Total Processed": 0,
            "Accepted": 0,
            "Rejected": 0,
            "Warnings": 0
        }
        self.rejection_reasons = defaultdict(int)
        self.warnings = defaultdict(int)
        
        # Per LU stats
        self.lu_stats = defaultdict(lambda: {
            "Generated": 0,
            "Accepted": 0,
            "Rejected": 0,
            "Duplicates": 0,
            "Types": defaultdict(int),
            "Scores": [],
            "Voice_Scores": [],
            "Accepted_Questions": []
        })

    @lru_cache(maxsize=2048)
    def _normalize_text(self, text: str) -> str:
        if not text: return ""
        text = self._pattern.sub('', text)
        return " ".join(text.lower().split())

    def _word_count(self, text: str) -> int:
        return len(self._normalize_text(text).split())

    def _reject(self, reason: str, details: str = ""):
        self.stats["Rejected"] += 1
        self.rejection_reasons[reason] += 1
        logger.warning(f"Quality Rejected: {reason}. {details}")
        return False
        
    def _warn(self, reason: str, details: str = ""):
        self.stats["Warnings"] += 1
        self.warnings[reason] += 1
        logger.info(f"Quality Warning: {reason}. {details}")

    def calculate_voice_score(self, text: str) -> int:
        wc = self._word_count(text)
        score = 100
        if wc > 12: score -= (wc - 12) * 5
        if wc < 6: score -= (6 - wc) * 5
        return max(0, score)

    def calculate_question_quality(self, q: Dict[str, Any]) -> int:
        score = 100
        acc_ans = q.get("acceptable_answers", [])
        if len(acc_ans) < 5: score -= 5
        
        voice_score = self.calculate_voice_score(q.get("question", ""))
        if voice_score < 80: score -= 10
        
        hint1 = self._normalize_text(str(q.get("hint_level_1", "")))
        hint2 = self._normalize_text(str(q.get("hint_level_2", "")))
        if hint1 and hint1 in hint2: score -= 10
        
        exp = str(q.get("full_explanation", ""))
        if self._word_count(exp) > 60: score -= 10
        
        return max(0, score)

    def validate(self, q: Dict[str, Any]) -> bool:
        self.stats["Total Processed"] += 1
        unit_id = str(q.get("learning_unit_id", "unknown"))
        lu_record = self.lu_stats[unit_id]
        lu_record["Generated"] += 1

        q_text = str(q.get("question", "")).strip()
        expected_ans = str(q.get("expected_answer", "")).strip()
        
        if not q_text: return self._reject("Question is empty")
        if not expected_ans: return self._reject("Expected answer is empty")

        # 1. Question Type Validation
        q_type = str(q.get("question_type", "")).strip().upper().replace(" ", "_").replace("/", "_")
        q["question_type"] = q_type
        if q_type not in VALID_QUESTION_TYPES:
            return self._reject("Unknown question_type", q_type)

        # 2. Length Validation (Warning only)
        wc = self._word_count(q_text)
        if wc > 18:
            self._warn("Question length exceeds 18 words", q_text)
        elif wc < 6:
            self._warn("Question very short", q_text)

        # 3. Automatic Estimated Time
        complexity = str(q.get("answer_complexity", "")).upper()
        if complexity == "WORD":
            q["estimated_answer_time"] = 4
        elif complexity == "SHORT_PHRASE":
            q["estimated_answer_time"] = 6
        elif complexity == "SHORT_SENTENCE":
            q["estimated_answer_time"] = 10
        else:
            q["estimated_answer_time"] = 5

        # 4. Difficulty Consistency Check
        diff = q.get("difficulty", 2)
        min_d, max_d = TYPE_DIFFICULTY_BOUNDS.get(q_type, (1, 4))
        if not (min_d <= diff <= max_d):
            return self._reject("Difficulty inconsistency", f"{q_type} difficulty should be {min_d}-{max_d}, got {diff}")

        # 5. Explanation Length
        explanation = str(q.get("full_explanation", "")).strip()
        if self._word_count(explanation) > 60:
            self._warn("Explanation length exceeds 60 words")

        # 6. Acceptable Answer Validation
        acc_answers = q.get("acceptable_answers", [])
        if not acc_answers:
            return self._reject("No acceptable answers")
        if len(acc_answers) < 2:
            return self._reject("Minimum 2 acceptable answers required")
        if len(acc_answers) < 5:
            self._warn("Recommend 5-10 acceptable answers, got < 5")
            
        norm_acc_ans = [self._normalize_text(a) for a in acc_answers]
        if len(norm_acc_ans) != len(set(norm_acc_ans)):
            return self._reject("Duplicate acceptable answers")
        if "" in norm_acc_ans:
            return self._reject("Empty acceptable answer string")
            
        norm_exp_ans = self._normalize_text(expected_ans)
        if norm_exp_ans not in norm_acc_ans:
            return self._reject("Expected answer not found in acceptable answers")

        # 7. Hints Leakage
        norm_h1 = self._normalize_text(str(q.get("hint_level_1", "")))
        norm_h2 = self._normalize_text(str(q.get("hint_level_2", "")))
        norm_exp = self._normalize_text(explanation)
        
        if norm_exp_ans and norm_exp_ans in norm_h1: return self._reject("Hint 1 contains the answer")
        if norm_exp and norm_exp in norm_h2: return self._reject("Hint 2 contains the complete explanation")

        # 8. MCQ / TRUE_FALSE Validation
        if q_type == "MCQ":
            options = q.get("mcq_options", [])
            if len(options) != 4: return self._reject("MCQ does not contain exactly four options")
            norm_opts = [self._normalize_text(opt) for opt in options]
            if len(set(norm_opts)) != 4: return self._reject("Duplicate MCQ options")
            if "" in norm_opts: return self._reject("Empty MCQ option")
            correct_opt = str(q.get("correct_option", "")).strip()
            if not correct_opt or self._normalize_text(correct_opt) not in norm_opts:
                return self._reject("Correct option not found in options")
        elif q_type == "TRUE_FALSE":
            options = q.get("mcq_options", [])
            if options:
                if len(options) != 2: return self._reject("True/False must contain exactly two options")
                norm_opts = [self._normalize_text(opt) for opt in options]
                if len(set(norm_opts)) != 2: return self._reject("Duplicate True/False options")
                if "" in norm_opts: return self._reject("Empty True/False option")
                correct_opt = str(q.get("correct_option", "")).strip()
                if not correct_opt or self._normalize_text(correct_opt) not in norm_opts:
                    return self._reject("Correct option not found in options")

        # 9. Duplicate Detection (Type + Concept + Question Text + Answer + Method)
        concept = self._normalize_text(str(q.get("concept", "")))
        norm_q = self._normalize_text(q_text)
        eval_method = str(q.get("evaluation_method", ""))
        
        sig = f"{q_type}|{concept}|{norm_q}|{norm_exp_ans}|{eval_method}"
        if sig in self._seen_signatures[unit_id]:
            lu_record["Duplicates"] += 1
            return self._reject("Duplicate question detected (same format and concept)")

        # Passed Quality Checks
        self._type_counts[unit_id][q_type] += 1
        self._seen_signatures[unit_id].add(sig)
        
        lu_record["Accepted"] += 1
        lu_record["Types"][q_type] += 1
        
        q_quality = self.calculate_question_quality(q)
        voice_score = self.calculate_voice_score(q_text)
        
        lu_record["Scores"].append(q_quality)
        lu_record["Voice_Scores"].append(voice_score)
        lu_record["Accepted_Questions"].append(q)
        
        self.stats["Accepted"] += 1
        return True

    def _calculate_concept_coverage(self, lu_record: dict, lu_dict: dict) -> float:
        lu_keywords = lu_dict.get("keywords", [])
        if not lu_keywords: return 100.0
        
        covered = 0
        norm_kws = [self._normalize_text(k) for k in lu_keywords]
        
        accepted = lu_record["Accepted_Questions"]
        text_corpus = " ".join([self._normalize_text(q.get("concept", "")) + " " + self._normalize_text(q.get("question", "")) for q in accepted])
        
        missing = []
        for k in norm_kws:
            if k in text_corpus:
                covered += 1
            else:
                missing.append(k)
                
        lu_record["Missing_Concepts"] = missing
        return (covered / len(lu_keywords)) * 100.0

    def generate_lu_summary(self, unit_id: str, lu_dict: dict) -> str:
        lu_record = self.lu_stats[unit_id]
        
        coverage = self._calculate_concept_coverage(lu_record, lu_dict)
        diversity = (len(lu_record["Types"]) / len(VALID_QUESTION_TYPES)) * 100 if VALID_QUESTION_TYPES else 0
        avg_voice = sum(lu_record["Voice_Scores"]) / len(lu_record["Voice_Scores"]) if lu_record["Voice_Scores"] else 0
        avg_q_qual = sum(lu_record["Scores"]) / len(lu_record["Scores"]) if lu_record["Scores"] else 0
        
        # 30% Diversity, 25% Coverage, 15% Voice, 30% Metadata/Hints/Explanation
        overall_quality = (diversity * 0.30) + (coverage * 0.25) + (avg_voice * 0.15) + (avg_q_qual * 0.30)
        
        report = []
        report.append("="*49)
        report.append(f"Learning Unit          : {lu_dict.get('title', unit_id)}")
        report.append(f"Questions Generated    : {lu_record['Generated']}")
        report.append(f"Questions Accepted     : {lu_record['Accepted']}")
        report.append(f"Rejected               : {lu_record['Generated'] - lu_record['Accepted']}")
        report.append(f"Duplicates             : {lu_record['Duplicates']}")
        report.append(f"Concept Coverage       : {coverage:.0f}%")
        report.append(f"Voice Score            : {avg_voice:.0f}%")
        report.append(f"Question Diversity     : {diversity:.0f}%")
        report.append(f"Overall Quality        : {overall_quality:.0f}%")
        
        missing = lu_record.get("Missing_Concepts", [])
        if missing:
            report.append(f"Missing Concepts       : {', '.join(missing)}")
            
        report.append("Status                 : READY")
        report.append("="*49)
        
        # Store for chapter aggregation
        lu_record["overall_quality"] = overall_quality
        lu_record["coverage"] = coverage
        lu_record["avg_voice"] = avg_voice
        
        return "\n".join(report)

    def generate_chapter_summary(self, chapter_title: str, processing_time: float) -> str:
        total_units = len(self.lu_stats)
        total_gen = sum(r["Generated"] for r in self.lu_stats.values())
        total_acc = sum(r["Accepted"] for r in self.lu_stats.values())
        total_rej = total_gen - total_acc
        
        avg_q = total_acc / total_units if total_units > 0 else 0
        avg_cov = sum(r.get("coverage", 0) for r in self.lu_stats.values()) / total_units if total_units > 0 else 0
        avg_qual = sum(r.get("overall_quality", 0) for r in self.lu_stats.values()) / total_units if total_units > 0 else 0
        avg_voice = sum(r.get("avg_voice", 0) for r in self.lu_stats.values()) / total_units if total_units > 0 else 0
        
        report = []
        report.append("="*49)
        report.append(f"Chapter                : {chapter_title}")
        report.append(f"Learning Units         : {total_units}")
        report.append(f"Questions Generated    : {total_gen}")
        report.append(f"Questions Accepted     : {total_acc}")
        report.append(f"Rejected               : {total_rej}")
        report.append(f"Average Questions      : {avg_q:.1f}")
        report.append(f"Coverage               : {avg_cov:.0f}%")
        report.append(f"Average Quality        : {avg_qual:.0f}%")
        report.append(f"Average Voice Score    : {avg_voice:.0f}%")
        report.append(f"Processing Time        : {processing_time:.2f} seconds")
        report.append("Status                 : READY")
        report.append("="*49)
        return "\n".join(report)
