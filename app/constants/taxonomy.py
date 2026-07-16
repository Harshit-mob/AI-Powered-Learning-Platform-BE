from enum import Enum

class BloomLevel(str, Enum):
    REMEMBER = "REMEMBER"
    UNDERSTAND = "UNDERSTAND"
    APPLY = "APPLY"
    ANALYZE = "ANALYZE"
    EVALUATE = "EVALUATE"
    CREATE = "CREATE"

class CognitiveLevel(str, Enum):
    RECALL = "RECALL"
    COMPREHENSION = "COMPREHENSION"
    APPLICATION = "APPLICATION"
    REASONING = "REASONING"
