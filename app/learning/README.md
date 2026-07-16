# Learning Domain Architecture

The Learning Domain acts as the continuous state engine of the platform. It consumes the output produced by the Assessment Domain and updates the student's learning profile.

## Component Responsibilities

- **Learning Event Handler**: The orchestrator. Receives `EvaluationResult` objects, coordinates updates via the UnitOfWork, and returns a single `LearningOutcome` DTO.
- **Mastery Engine & Calculators**: Uses weighted scoring to modify `mastery_percentage` safely (bounded `0.0` - `1.0`) based on evaluation score, time taken, hints, and question difficulty.
- **Review Scheduler**: Applies spaced repetition algorithms via the Strategy Pattern (`SchedulerFactory`). Fully decoupled from mastery calculations, enabling parallel upgrades to FSRS or Leitner algorithms.
- **Progress Tracker**: Calculates ephemeral session deltas (e.g., net gain) allowing the UI to instantly display "+15% Mastery!" without expensive DB queries.

## Contract Integrity

- **No Question Generation**: This domain never creates or selects questions.
- **Immutable DTO Out**: To ensure separation of concerns, the entire domain evaluates and persists changes locally, and then hands off a `LearningOutcome` payload to the next domain (Personalization) without invoking it directly.
