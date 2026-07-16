from dataclasses import dataclass

@dataclass
class IntelligenceConfig:
    words_per_minute: int = 130  # Average speaking rate (conversational)
    thinking_multiplier_recall: float = 1.0
    thinking_multiplier_reasoning: float = 2.5
    optimal_voice_score_threshold: int = 80
    production_ready_threshold: int = 85
