class RepositoryException(Exception):
    """Base class for repository exceptions."""
    pass

class EntityNotFoundError(RepositoryException):
    """Raised when an entity is not found in the database."""
    pass

class DuplicateEntityError(RepositoryException):
    """Raised when attempting to create an entity that already exists."""
    pass

class DatabaseConnectionError(RepositoryException):
    """Raised when there is an issue connecting to the database."""
    pass
