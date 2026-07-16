# Runtime Session Engine

This is the core business engine that handles all session generation and lifecycle management. It sits strictly between the API layer and the underlying Assessment/Learning algorithms, enforcing hard business rules about duration, unlock conditions, and content distribution.

## Architecture

- **SessionEngine (Facade)**: `generate()`, `resume()`, `complete()`. Exposes state transitions.
- **DistributionEngine**: Balances fetched candidates against Bloom Taxonomy and Difficulty policies based on a dynamic time constraint.
- **DailyPracticeEngine**: Generates exactly 10-minute sessions focused on active topics.
- **ChapterRevisionEngine**: Generates 15-minute sessions covering an entire chapter. Strictly locked until all topics inside the chapter hit 80% mastery (`SessionConfig.CHAPTER_UNLOCK_MASTERY`).

## Future Session Types (Deferred)
- `RECOVERY`: Triggered when mastery drops.
- `WEEKLY_REVIEW`: Balances decay curves from the Review Scheduler.
- `MOCK_TEST`: Full length, mimicking exact exam patterns.
- `CHALLENGE`: 100% HARD difficulty.
