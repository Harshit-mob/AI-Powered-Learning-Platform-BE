from datetime import datetime, timedelta
from typing import Dict, Any

from app.constants.scheduler import MIN_EASE_FACTOR

class SM2Scheduler:
    def calculate_next_review(self, 
                              evaluation_score: float, 
                              previous_interval: float, 
                              previous_ease: float, 
                              successive_correct: int) -> Dict[str, Any]:
        
        # Convert 0.0 - 1.0 evaluation to SM2 0-5 quality scale
        quality = int(evaluation_score * 5)
        
        if quality < 3:
            # Failed
            successive_correct = 0
            interval = 1.0
        else:
            # Passed
            successive_correct += 1
            if successive_correct == 1:
                interval = 1.0
            elif successive_correct == 2:
                interval = 6.0
            else:
                interval = previous_interval * previous_ease
                
        # Update ease factor
        ease = previous_ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        ease = max(MIN_EASE_FACTOR, ease)
        
        next_review = datetime.utcnow() + timedelta(days=interval)
        
        return {
            "next_review": next_review.isoformat(),
            "interval": interval,
            "ease_factor": ease,
            "successive_correct": successive_correct
        }
