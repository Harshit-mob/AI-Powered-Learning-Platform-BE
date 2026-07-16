# Repository Layer

This repository layer provides a robust, decoupled data-access infrastructure for the Runtime Intelligence Engine. By abstracting SQLAlchemy away from the business services, we guarantee adherence to Domain-Driven Design (DDD) and SOLID principles.

## Responsibilities

Repositories have exactly **one responsibility**: encapsulating database persistence.

**What Repositories DO:**
- Execute specific CRUD operations and domain queries (e.g., `due_reviews()`, `latest_attempt()`).
- Use SQLAlchemy 2.x paradigms (`select()`, `selectinload()`) to prevent N+1 queries.
- Catch raw `SQLAlchemyError` exceptions and wrap them into clean domain exceptions (`RepositoryException`, `DuplicateEntityError`).
- Provide clean, typed return values to business logic.

**What Repositories DO NOT do:**
- **No Business Logic:** Repositories NEVER calculate mastery, determine spacing intervals, evaluate answers, or trigger recommendations.
- **No Transaction Commits:** Repositories NEVER call `session.commit()`. Transactions are strictly managed by the Unit of Work.
- **No Events:** Repositories do not publish domain events on the event bus.

## Unit of Work (UoW)

The `UnitOfWork` handles all transaction boundaries. Services should instantiate UoW in a context manager and use it to access repositories, ensuring atomicity across multiple tables.

### Example Usage

```python
from app.repositories.base.unit_of_work import UnitOfWork

def complete_learning_session(session_id: uuid.UUID, response_data: dict):
    with UnitOfWork() as uow:
        # 1. Save response (Persistence only)
        uow.responses.save_response(response_data)
        
        # 2. Update session (Persistence only)
        uow.sessions.finish_session(session_id, {"status": "COMPLETED"})
        
        # 3. Transaction committed ONLY if all operations succeed.
        uow.commit()
```

If an error occurs or an exception is raised, the context manager safely handles connection tear-down, and any uncommitted changes are rolled back.
