import re
import json
import logging
from typing import Tuple, Dict

logger = logging.getLogger(__name__)

class ContentNormalizer:
    """
    Normalizes text after it has been cleaned. 
    Improves OCR output without changing the meaning.
    """
    def __init__(self):
        self.stats = {
            "characters_corrected": 0,
            "spacing_fixes": 0,
            "headers_removed": 0,
            "footers_removed": 0,
            "paragraphs_merged": 0,
            "potential_ocr_issues": 0,
            "warnings": 0
        }
        
    def normalize(self, text: str) -> Tuple[str, Dict[str, int]]:
        """
        Runs the normalizer pipeline on the cleaned text.
        Returns the normalized text and the stats report.
        """
        if not text:
            return "", self.stats
            
        original_length = len(text)
        
        # 1. Remove Page Artifacts
        text = self._remove_page_artifacts(text)
        
        # 2. Normalize Whitespace
        text = self._normalize_whitespace(text)
        
        # 3. Fix OCR Spacing
        text = self._fix_ocr_spacing(text)
        
        # 4. Normalize Headings
        text = self._normalize_headings(text)
        
        # 5. Preserve Educational Structure
        text = self._preserve_educational_structure(text)
        
        # 6. Preserve Numbered Lists
        text = self._preserve_numbered_lists(text)
        
        self.stats["characters_corrected"] = abs(original_length - len(text))
        
        return text.strip(), self.stats
        
    def _normalize_whitespace(self, text: str) -> str:
        """Removes double spaces, random tabs, and trailing spaces while preserving paragraphs."""
        # Replace random tabs with spaces
        text = text.replace('\t', ' ')
        
        # Remove trailing spaces from lines
        text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)
        
        # Collapse multiple spaces into one space
        original_len = len(text)
        text = re.sub(r' {2,}', ' ', text)
        if len(text) < original_len:
            self.stats["spacing_fixes"] += (original_len - len(text))
            
        return text

    def _fix_ocr_spacing(self, text: str) -> str:
        """Fixes common OCR spacing errors like missing spaces after punctuation."""
        def repl_punct(match):
            self.stats["spacing_fixes"] += 1
            return f"{match.group(1)} {match.group(2)}"
            
        # Fix missing space after punctuation (e.g. "them.They" -> "them. They")
        text = re.sub(r'([a-z]{2,}[.,;:!?])([A-Z])', repl_punct, text)
        
        # Very basic heuristics to split words (e.g. "ofacquiring")
        # In production, a spell checker dictionary should be used for this.
        heuristics = [
            (r'\b(of)([a-z]{4,})\b', r'\1 \2'),
            (r'\b(in)([a-z]{4,})\b', r'\1 \2'),
            (r'\b(is)([a-z]{4,})\b', r'\1 \2'),
            (r'\b(the)([a-z]{4,})\b', r'\1 \2'),
            (r'\b(to)([a-z]{4,})\b', r'\1 \2'),
            (r'\b(and)([a-z]{4,})\b', r'\1 \2'),
            (r'\b([a-z]{4,})(is)\b', r'\1 \2'),
        ]
        
        for pattern, repl in heuristics:
            prev = text
            text = re.sub(pattern, repl, text)
            if prev != text:
                self.stats["spacing_fixes"] += 1
                
        return text

    def _remove_page_artifacts(self, text: str) -> str:
        """Removes page numbers and short headers/footers while preserving --- [PAGE X] --- markers."""
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            
            if re.match(r'^---\s+\[PAGE\s+\d+\]\s+---$', stripped):
                cleaned_lines.append(line)
                continue
                
            # Remove isolated numbers (likely page numbers)
            if stripped.isdigit() and len(stripped) < 5:
                self.stats["footers_removed"] += 1
                continue
                
            cleaned_lines.append(line)
            
        return '\n'.join(cleaned_lines)
        
    def _normalize_headings(self, text: str) -> str:
        """Converts inconsistent ALL CAPS headings into Title Case for consistency."""
        lines = text.split('\n')
        for i, line in enumerate(lines):
            stripped = line.strip()
            # If line is all uppercase, short enough to be a heading, and doesn't end with a period
            if stripped and stripped.isupper() and len(stripped) < 60 and not stripped.endswith('.'):
                lines[i] = stripped.title()
                
        return '\n'.join(lines)
        
    def _preserve_educational_structure(self, text: str) -> str:
        """Detects educational constructs (Activities, Discuss) and wraps them in a JSON struct."""
        blocks = re.split(r'\n\s*\n', text)
        new_blocks = []
        
        for block in blocks:
            stripped = block.strip()
            if not stripped:
                continue
                
            upper_block = stripped.upper()
            
            # Identify "Think and Discuss"
            if upper_block.startswith("THINK AND DISCUSS") or upper_block.startswith("THINK & DISCUSS"):
                struct = {
                    "type": "activity",
                    "title": "Think and Discuss",
                    "content": stripped
                }
                new_blocks.append(json.dumps(struct, indent=4))
                continue
                
            # Identify "Activity"
            if upper_block.startswith("ACTIVITY") or upper_block.startswith("ACTVITY"):
                struct = {
                    "type": "activity",
                    "title": "Activity",
                    "content": stripped
                }
                new_blocks.append(json.dumps(struct, indent=4))
                continue
                
            # Identify "Did you know"
            if upper_block.startswith("DID YOU KNOW"):
                struct = {
                    "type": "fact",
                    "title": "Did You Know",
                    "content": stripped
                }
                new_blocks.append(json.dumps(struct, indent=4))
                continue
                
            new_blocks.append(stripped)
            
        return '\n\n'.join(new_blocks)
        
    def _preserve_numbered_lists(self, text: str) -> str:
        """Ensures that lists are properly formatted and not collapsed on the same line."""
        # Split items if they appear consecutively on the same line (e.g. "text. 1. First 2. Second")
        # Find cases where a space precedes a digit and a dot, preceded by a space or start of line.
        text = re.sub(r'(?<=\w[.:!?])\s+(?=\d+\.\s)', '\n', text)
        return text
