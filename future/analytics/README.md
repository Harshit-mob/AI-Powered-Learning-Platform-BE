# Analytics Domain Architecture

The Analytics Domain strictly adheres to CQRS and Event Sourcing patterns. It maintains Read Models optimized for querying, completely disjoint from the transactional (Write) domain used for learning progression.

## Key Principles

- **No Business Logic Mutability**: The Analytics Domain never triggers mastery updates or review schedules.
- **Event-Driven**: Populated entirely by consuming immutable Domain Events (e.g. `MASTERY_UPDATED`, `QuestionAnswered`).
- **No Table Scans**: Aggregations (like `average_mastery` or `accuracy`) are calculated incrementally as events arrive, avoiding heavy runtime `GROUP BY` aggregations on millions of rows.

## Components

- **AnalyticsDispatcher**: The consumer that maps incoming domain events to the correct specific analytics services. Supports historical batch replay to reconstruct corrupted or new read models from the event log.
- **Question Analytics & Monitor**: Updates running averages of difficulty, time taken, and accuracy. The Monitor scans these metrics to automatically flag questions that might be poorly phrased (high skip rate) or mapped to the wrong difficulty.
- **Teacher Dashboard / Student Analytics**: Exposes quick pre-calculated metrics (`StudentAnalyticsReport`, `TeacherDashboardReport`) ready for API consumption without locking primary tables.
