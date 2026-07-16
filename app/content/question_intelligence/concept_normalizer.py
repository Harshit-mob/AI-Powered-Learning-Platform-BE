import re
from typing import Dict, Any

class ConceptNormalizer:
    """
    Normalizes concepts into a consistent snake_case format.
    Removes punctuation, replaces '&' with 'and', trims whitespace.
    """
    def normalize(self, question: Dict[str, Any]) -> str:
        concept = str(question.get("concept", "")).strip()
        if not concept:
            return ""
            
        # 1. Lowercase
        concept = concept.lower()
        
        # 2. Replace '&' with 'and'
        concept = concept.replace("&", "and")
        
        # 3. Remove punctuation (keep alphanumeric and spaces)
        concept = re.sub(r'[^a-z0-9\s_]', '', concept)
        
        # 4. Remove common educational filler words to create canonical concepts
        fillers = {"definition", "meaning", "concept", "introduction", "basics", "understanding", "of", "the", "a", "an", "what", "is", "process"}
        words = concept.split()
        canonical_words = [w for w in words if w not in fillers]
        
        if not canonical_words:
            # Fallback if the concept was literally just "Definition of"
            canonical_words = words
            
        # 5. Sort words alphabetically to handle "Science Definition" vs "Definition Science" (both become 'science')
        # Wait, if we sort, "scientific method" becomes "method scientific". That's fine for internal canonical mapping.
        canonical_words.sort()
        
        # 6. Replace whitespace with single underscore
        concept = "_".join(canonical_words)
        
        return concept
