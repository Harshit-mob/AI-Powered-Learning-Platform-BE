# Personalization Domain Architecture

The Personalization Domain translates the pure state updates of the Learning Domain into actionable recommendations, learning paths, and adaptive session goals for the student.

## Component Responsibilities

- **PersonalizationEngine**: Orchestrates the sub-engines and packages the final result into an immutable `PersonalizationOutcome` DTO.
- **RecommendationRules / Engine**: Scans the `LearningOutcome` for specific triggers (e.g., mastery drop -> Recovery; due interval < 1.0 -> Revision) and ranks them by deterministic priority.
- **LearningPathEngine**: Converts a high-priority recommendation into a sequential learning graph (e.g., `Recovery -> Practice -> Assessment`).
- **AdaptiveSessionSelector**: Selects the absolute next immediate session type to present on the dashboard.
- **DailyGoalTracker**: Generates deterministic progress tracking logic based on the session's footprint (questions answered, concepts mastered).
- **PreferenceEngine**: Exposes the user's explicit preferences to adjust the UI/UX.

## Contract Integrity

- **No Mastery Modification**: The Personalization Domain has no authority to change mastery scores or scheduler states.
- **Input / Output**: It strictly receives `LearningOutcome` and outputs `PersonalizationOutcome`.
- **Stateless Rules**: Recommendations are purely generated off state snapshots and event streams.

## Extension Guide

To add a new recommendation rule:
1. Open `recommendation_rules.py`.
2. Add a new `if` block evaluating the `outcome.progress_summary` or `outcome.mastery_updates`.
3. Append a `RecommendationItem` with an appropriate `priority`.
4. Ensure a unit test is added to `test_personalization.py`.
