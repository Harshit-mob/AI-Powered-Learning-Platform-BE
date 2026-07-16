from typing import Dict, Any
from .models import BloomLevel, EducationalIntent

class TimeEstimator:
    """
    Deterministically calculates estimated answering and thinking times.
    """
    
    def estimate_answer_time(self, question: Dict[str, Any]) -> float:
        # Base on complexity
        complexity = str(question.get("answer_complexity", "WORD")).upper()
        comp_time = 2.0
        if complexity == "SHORT_PHRASE": comp_time = 4.0
        elif complexity == "PHRASE": comp_time = 6.0
        elif complexity == "SENTENCE": comp_time = 10.0
        elif complexity == "PARAGRAPH": comp_time = 15.0
            
        # Base on length
        expected = str(question.get("expected_answer", ""))
        len_time = len(expected) / 10.0
        
        # Base on type
        q_type = str(question.get("question_type", "")).upper()
        type_bonus = 0.0
        if q_type == "MCQ" or q_type == "TRUE_FALSE":
            type_bonus = 2.0
            
        final_time = (comp_time + len_time) / 2.0 + type_bonus
        return round(min(15.0, max(2.0, final_time)), 2)
        
    def estimate_thinking_time(self, question: Dict[str, Any], bloom: BloomLevel, intent: EducationalIntent) -> float:
        from .utils import count_words
        
        # Base reading time on question and answer length
        q_text = str(question.get("question", ""))
        ans_text = str(question.get("expected_answer", ""))
        
        q_wc = count_words(q_text)
        ans_wc = count_words(ans_text)
        
        # Average reading speed ~200 WPM -> 3.3 words per second
        reading_time = (q_wc + ans_wc) / 3.3
        
        # Base cognitive time
        base_time = 2.0
        
        # Bloom based
        if bloom == BloomLevel.UNDERSTAND:
            base_time = 5.0
        elif bloom == BloomLevel.APPLY:
            base_time = 8.0
        elif bloom == BloomLevel.ANALYZE:
            base_time = 12.0
            
        # Difficulty bonus
        diff = float(question.get("difficulty", 2.0))
        diff_bonus = diff * 1.5
        
        # Intent bonus
        if intent in {EducationalIntent.REASON, EducationalIntent.APPLICATION}:
            diff_bonus += 3.0
            
        final_time = reading_time + base_time + diff_bonus
        return round(min(45.0, max(2.0, final_time)), 2)

    def estimate_total_time(self, question: Dict[str, Any], speaking_time: float, thinking_time: float) -> int:
        """
        estimated_time = thinking_time + speaking_time + interaction_buffer
        """
        try:
            diff = int(question.get("difficulty", 2))
        except (ValueError, TypeError):
            diff = 2
            
        buffer_map = {1: 1, 2: 2, 3: 2, 4: 3, 5: 3}
        buffer = buffer_map.get(diff, 2)
        
        total_time = speaking_time + thinking_time + buffer
        return int(round(total_time))
