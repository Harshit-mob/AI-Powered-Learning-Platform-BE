import logging
import re
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

class ContentValidator:
    """
    Validates normalized text before it is sent to the Curriculum Parser.
    Checks for missing headings, broken paragraphs, repetitive text, and OCR artifacts.
    """
    def __init__(self):
        pass
        
    def validate(self, text: str) -> Tuple[bool, Dict[str, any]]:
        """
        Runs validation heuristics on the text.
        Returns a tuple of (is_valid, validation_report).
        """
        report = {
            "is_valid": True,
            "missing_headings": 0,
            "broken_paragraphs": 0,
            "very_short_paragraphs": 0,
            "repeated_paragraphs": 0,
            "unknown_ocr_tokens": 0,
            "very_long_sentences": 0,
            "warnings": []
        }
        
        if not text:
            report["is_valid"] = False
            report["warnings"].append("Text is empty.")
            return False, report
            
        paragraphs = [p for p in text.split('\n\n') if p.strip()]
        
        seen_paragraphs = set()
        
        for p in paragraphs:
            # Check for repetition
            if p in seen_paragraphs and len(p) > 30 and not p.startswith('{'):
                report["repeated_paragraphs"] += 1
                report["warnings"].append(f"Repeated paragraph detected: '{p[:40]}...'")
            seen_paragraphs.add(p)
            
            # Check for unusually short paragraphs (ignoring JSON structs and page markers)
            if len(p) < 15 and not p.startswith('{') and not p.startswith('---'):
                report["very_short_paragraphs"] += 1
                
            # Check for unknown tokens/garbage (e.g., %$#@^&)
            # Find characters that are not standard text, punctuation, or numbers. Include Devanagari (Hindi) and Gujarati ranges.
            special_chars = len(re.findall(r'[^a-zA-Z0-9\s.,!?:;\'"()\[\]{}\-/%°\u0900-\u097f\u0a80-\u0aff]', p))
            if len(p) > 0 and (special_chars / len(p)) > 0.15: # >15% special chars
                report["unknown_ocr_tokens"] += 1
                report["warnings"].append(f"High unknown OCR token density in: '{p[:40]}...'")
                
            # Check for extremely long sentences
            sentences = re.split(r'[.!?]+', p)
            for s in sentences:
                if len(s.split()) > 60: # More than 60 words
                    report["very_long_sentences"] += 1
                    report["warnings"].append(f"Very long sentence detected: '{s[:40]}...'")
                    
        # If there are severe warnings (e.g., garbage text), mark as invalid
        if report["unknown_ocr_tokens"] > 3 or report["repeated_paragraphs"] > 3:
            report["is_valid"] = False
            
        return report["is_valid"], report
