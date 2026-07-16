class SessionEngineException(Exception):
    """Base exception for the Session Engine."""
    pass

class UnsupportedSessionTypeError(SessionEngineException):
    """Raised when an unimplemented session type is requested."""
    pass

class ChapterNotReadyForRevisionError(SessionEngineException):
    """Raised when a revision is requested but criteria aren't met."""
    pass

class NoEligibleQuestionsError(SessionEngineException):
    """Raised when there are no questions available to add to a session."""
    pass

class SessionValidationError(SessionEngineException):
    """Raised for bad input or ownership mismatches."""
    pass

class SessionStateTransitionError(SessionEngineException):
    """Raised when an invalid state transition occurs (e.g. Completing a CREATED session)."""
    pass
