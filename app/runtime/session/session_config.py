class SessionConfig:
    """
    Centralized configuration for runtime session rules.
    In a real environment, these would be loaded from env vars or a settings DB.
    """
    # Durations in minutes
    DAILY_SESSION_MINUTES = 10
    REVISION_SESSION_MINUTES = 15
    
    # Expected time per question (seconds)
    AVERAGE_QUESTION_SECONDS = 60
    
    # Mastery Thresholds
    CHAPTER_UNLOCK_MASTERY = 0.80
    PASSING_SCORE_THRESHOLD = 0.75
    
    # Policy Configurations for Question Distribution
    DAILY_POLICY = {
        "bloom_distribution": {
            "RECALL": 0.40,
            "COMPREHENSION": 0.40,
            "APPLICATION": 0.20
        },
        "difficulty_distribution": {
            "EASY": 0.60,
            "MEDIUM": 0.30,
            "HARD": 0.10
        }
    }
    
    REVISION_POLICY = {
        "bloom_distribution": {
            "RECALL": 0.20,
            "COMPREHENSION": 0.30,
            "APPLICATION": 0.30,
            "ANALYSIS": 0.20
        },
        "difficulty_distribution": {
            "EASY": 0.30,
            "MEDIUM": 0.40,
            "HARD": 0.30
        }
    }
