from enum import Enum

class SchedulerType(str, Enum):
    SM2 = "SM2"
    FSRS = "FSRS"
    LEITNER = "LEITNER"

DEFAULT_EASE_FACTOR = 2.5
MIN_EASE_FACTOR = 1.3
DEFAULT_INTERVAL_DAYS = 1.0
