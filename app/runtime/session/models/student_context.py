from dataclasses import dataclass, field
from typing import Dict, List, Optional
import uuid

@dataclass
class StudentContext:
    student_id: uuid.UUID
    
    # LU ID -> Mastery Percentage (0.0 to 1.0)
    mastery_by_lu: Dict[uuid.UUID, float] = field(default_factory=dict)
    
    # LU ID -> Confidence Score
    confidence_by_lu: Dict[uuid.UUID, float] = field(default_factory=dict)
    
    # LU ID -> Status string (e.g. "NEW", "MASTERED", "REVIEW")
    status_by_lu: Dict[uuid.UUID, str] = field(default_factory=dict)
    
    # Question ID -> is_correct boolean (whether student has correctly answered it before)
    correct_questions: Dict[uuid.UUID, bool] = field(default_factory=dict)
    
    # Question ID -> number of times attempted
    question_attempts: Dict[uuid.UUID, int] = field(default_factory=dict)
    
    # LU ID -> List of recent responses to determine if they frequently fail this LU
    recent_incorrect_by_lu: Dict[uuid.UUID, int] = field(default_factory=dict)
