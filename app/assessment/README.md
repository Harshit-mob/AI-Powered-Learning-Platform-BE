# Assessment Domain Architecture

The Assessment Domain is responsible for generating learning sessions dynamically from the existing AI-generated Question Bank. It adheres to strict deterministic rules without invoking any AI services at runtime.

## Component Responsibilities

- **Session Generator**: The primary orchestrator. Receives requests, selects a strategy, and delegates to the pure business logic components.
- **Session Strategies**: Implements the Strategy Pattern (`Practice`, `Revision`, `Challenge`, etc.). Each defines the bounds for a session (target difficulty, length, mix) without querying the database itself.
- **Question Selector**: Retrieves broad candidates from the `QuestionRepository` using `UnitOfWork`. Does not make qualitative decisions.
- **Difficulty Selector**: Uses pure business rules mapping mastery percentages and session types to discrete difficulty target buckets (e.g. `QuestionDifficulty.EASY`).
- **Question Ranker**: Applies deterministic heuristic scoring (Difficulty match, Bloom ordering, Diversity). Orders the candidates optimally.
- **Session Builder**: Assembles the ranked questions into an immutable DTO (`GeneratedSession`).
- **Evaluation Engine**: Inspects an `AnswerSubmission` against the `expected_answer` using rule-based strategies (Exact Match, Partial Lenient Match for blanks, Voice Confidence thresholds).

## Decoupled Architecture

The Assessment domain **does not**:
- Mutate `StudentMastery` or analytics tables.
- Care about what SR algorithm (SM2/FSRS) is used.
- Make external HTTP calls to OpenAI or Gemini.

Instead, the `EvaluationEngine` produces an `EvaluationResult` DTO.
This DTO is emitted as a domain event (Step 7: `SessionCompleted` event).
The `Learning Domain` will later consume that event to calculate mastery jumps, spaced repetition intervals, and analytics.
