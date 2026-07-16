import os
import yaml
from typing import Dict, Any, Tuple

class ScientificValidator:
    """
    Validates and repairs scientific accuracy of question text and answers
    using strict deterministic rules.
    """
    def __init__(self):
        rules_path = os.path.join(os.path.dirname(__file__), "config", "scientific_rules.yaml")
        try:
            with open(rules_path, "r") as f:
                self.rules = yaml.safe_load(f)
        except Exception:
            self.rules = {"forbidden_terms": {}, "replacements": {}}
            
    def validate(self, question: Dict[str, Any]) -> Tuple[str, str]:
        """
        Returns (status, message).
        status: "PASS", "WARNING", "ERROR"
        """
        warnings = []
        errors = []
        
        # We will check question text, hints, full_explanation, etc., and lists like acceptable_answers
        fields_to_check = ["text", "question", "expected_answer", "acceptable_answers", "full_explanation", "hint_level_1", "hint_level_2"]
        
        # Hardcoded specific phrases to reject (ERROR)
        critical_phrases = [
            "theory is proven",
            "theory becomes fact",
            "scientific proof",
            "absolute truth",
            "100% proven"
        ]
        
        warning_replacements = {
            "proved correct": "supported by repeated testing",
            "proven": "supported by evidence",
            "prove": "support",
            "proof": "scientific evidence",
            "fact": "consistent observations",
            "learn the truth": "discover the most accurate current explanation",
            "proved forever": "supported by evidence",
            "scientifically proven forever": "supported by our current scientific understanding",
            "absolute truth": "best available evidence"
        }
        
        repaired = False
        
        for field in fields_to_check:
            val = question.get(field)
            if not val:
                continue
                
            if isinstance(val, str):
                items_to_check = [val]
            elif isinstance(val, list):
                items_to_check = val
            else:
                continue
                
            repaired_items = []
            field_repaired = False
            
            for item in items_to_check:
                if not isinstance(item, str):
                    repaired_items.append(item)
                    continue
                    
                item_lower = item.lower()
                
                # 1. Critical Errors -> Reject immediately
                for bad in critical_phrases:
                    if bad in item_lower:
                        errors.append(f"Contains scientifically inaccurate phrase '{bad}' in {field}")
                        return "ERROR", "; ".join(errors)
                        
                # 2. Warnings -> Attempt repair
                for warn_term, replacement in warning_replacements.items():
                    if warn_term in item_lower:
                        import re
                        item = re.sub(rf"\b{warn_term}\b", replacement, item, flags=re.IGNORECASE)
                        warnings.append(f"Repaired '{warn_term}' to '{replacement}' in {field}")
                        repaired = True
                        field_repaired = True
                        
                repaired_items.append(item)
                
            if field_repaired:
                if isinstance(val, str):
                    question[field] = repaired_items[0]
                else:
                    question[field] = repaired_items
                        
        if errors:
            return "ERROR", "; ".join(errors)
        if warnings:
            return "WARNING", "; ".join(warnings)
            
        return "PASS", ""
