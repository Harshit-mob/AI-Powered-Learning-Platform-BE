from typing import Dict, Any, List

class VoiceKeywordGenerator:
    """
    Deterministically generates natural spoken alternatives for the expected answer
    to improve voice-recognition matching.
    """
    
    def generate(self, question: Dict[str, Any]) -> List[str]:
        expected = str(question.get("expected_answer", "")).strip()
        if not expected:
            return []
            
        variants = [expected]
        
        # Heuristic rules to generate spoken variants
        lower_expected = expected.lower()
        
        # 1. "It is X"
        variants.append(f"It is {lower_expected}")
        
        # 2. "The answer is X"
        variants.append(f"The answer is {lower_expected}")
        
        # 3. Handle boolean-like specifically
        if lower_expected in {"true", "false", "yes", "no"}:
            variants.append(f"I think it is {lower_expected}")
            
        # 4. Handle one-word answers
        if len(lower_expected.split()) == 1:
            variants.append(f"Just {lower_expected}")
            
        # Limit to 5
        # Ensure uniqueness
        seen = set()
        unique_variants = []
        for v in variants:
            if v.lower() not in seen:
                seen.add(v.lower())
                unique_variants.append(v)
                
        return unique_variants[:5]
