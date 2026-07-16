from typing import Dict, Any, List

class MisconceptionGenerator:
    """
    Deterministically generates misconception_tags based on textbook supported logic.
    """
    
    def generate(self, question: Dict[str, Any]) -> List[str]:
        q_text = str(question.get("question", "")).lower()
        q_type = str(question.get("question_type", "")).upper()
        
        misconceptions = []
        
        # Textbook supported misconceptions mapping
        textbook_misconceptions = {
            "science is only memorization": ["memoriz", "just facts", "memorize"],
            "observation means only seeing": ["only sight", "only seeing", "just looking"],
            "experiments always happen in labs": ["in a lab", "always laboratory", "only in lab"],
            "science has all the answers": ["has all answers", "knows everything", "solve everything"],
            "scientific facts never change": ["never change", "always true", "absolute truth"]
        }
        
        # Check distractors / text
        options = question.get("mcq_options", [])
        if isinstance(options, list):
            for opt in options:
                opt_lower = str(opt).lower()
                for belief, triggers in textbook_misconceptions.items():
                    if any(t in opt_lower for t in triggers):
                        misconceptions.append(f"Belief: {belief.capitalize()}")
                        
        # Check text
        for belief, triggers in textbook_misconceptions.items():
            if any(t in q_text for t in triggers):
                tag = f"Belief: {belief.capitalize()}"
                if tag not in misconceptions:
                    misconceptions.append(tag)
                    
        return list(set(misconceptions))
