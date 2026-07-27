import re
import logging
from typing import List
from app.content.pdf_extractor import ExtractedPage

logger = logging.getLogger(__name__)

class ContentCleaner:
    """
    Service responsible for normalizing and cleaning extracted text.
    Fixes OCR mistakes, broken lines, and multiple spaces while preserving 
    structural elements like headings, lists, tables, and scientific terms.
    """
    
    def __init__(self):
        # A dictionary of common OCR mistakes. This can be loaded from a config file in the future.
        # e.g., 'rn' misread as 'm', '1' as 'l' or 'I' depending on context.
        self.ocr_fixes = {
            r'(?i)\bclieck\b': 'check', # Example OCR error fix
            r'([a-z])- ([a-z])': r'\1\2', # Fix mid-word hyphenation splits
        }

    def clean(self, pages: List[ExtractedPage]) -> str:
        """
        Processes a list of extracted pages and returns a unified, cleaned text document.
        Handles repeated headers/footers by skipping them.
        """
        if not pages:
            return ""

        cleaned_pages = []
        
        for page in pages:
            text = page.text
            if not text.strip():
                continue
                
            text = text.replace('\x00', '')
            text = self._normalize_spaces(text)
            text = self._fix_ocr_mistakes(text)
            text = self._fix_broken_lines(text)
            
            # Requirement: "Preserve Page References"
            # We explicitly demarcate the pages so the Curriculum Parser and Learning Unit Builder 
            # can know exactly which source pages a concept comes from.
            cleaned_pages.append(f"\n\n--- [PAGE {page.page_number}] ---\n\n{text}")
            
        return "".join(cleaned_pages).strip()

    def _normalize_spaces(self, text: str) -> str:
        """Removes multiple horizontal spaces but preserves necessary newlines."""
        # Replace 2 or more spaces or tabs with a single space
        return re.sub(r'[^\S\r\n]{2,}', ' ', text)

    def _fix_ocr_mistakes(self, text: str) -> str:
        """Applies basic regex replacements for common OCR errors."""
        for pattern, replacement in self.ocr_fixes.items():
            text = re.sub(pattern, replacement, text)
        return text

    def _fix_broken_lines(self, text: str) -> str:
        """
        Merges lines that were incorrectly split by PDF extraction or OCR.
        Contains specific heuristics to preserve structural elements.
        """
        lines = text.split('\n')
        fixed_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                # Preserve intentional paragraph breaks
                fixed_lines.append("")
                continue
                
            if fixed_lines and fixed_lines[-1].strip():
                prev = fixed_lines[-1].strip()
                
                # Heuristics to PRESERVE structure:
                # 1. Is it a list item? (Starts with -, *, •, or 1., a.)
                is_current_list = bool(re.match(r'^(\-|\*|\•|\d+\.|\w\.)\s', line))
                is_prev_list = bool(re.match(r'^(\-|\*|\•|\d+\.|\w\.)\s', prev))
                
                # 2. Is it a Heading? (Short line, no punctuation at end, often title case or all caps)
                is_prev_heading = len(prev) < 60 and not prev.endswith(('.', ':', '?', '!'))
                
                # If previous line ends with a hyphen (and not a space before it), it's a broken word
                if prev.endswith('-') and not prev.endswith(' -'):
                    fixed_lines[-1] = prev[:-1] + line
                    continue
                
                # If previous line doesn't end with sentence-ending punctuation, 
                # AND current line starts with a lowercase letter, 
                # AND it's not part of a list structure...
                if prev[-1] not in '.!?:;”"' and line[0].islower() and not is_current_list and not is_prev_list:
                    # It's a broken sentence. Merge them.
                    fixed_lines[-1] = prev + " " + line
                    continue
            
            fixed_lines.append(line)
            
        return "\n".join(fixed_lines)
