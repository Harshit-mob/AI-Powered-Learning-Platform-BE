# AI-Powered Learning Platform - Backend

This is the Python (FastAPI) backend for the Student MVP.

## Architecture

The backend follows Clean Architecture and Domain-Driven Design (DDD).

- **API Layer**: Thin controllers mapping HTTP requests (`app/api/v1/`).
- **Application Layer**: Application services orchestrating use cases and Unit of Work (`app/application/`).
- **Domain Layer**: Core business engines (`app/runtime/`, `app/assessment/`).
- **Infrastructure Layer**: SQLAlchemy models, repositories, and DB connections (`app/models/`, `app/repositories/`).

## Features (Student MVP)
- Content Hierarchy (Boards -> Grades -> Chapters -> Topics -> Learning Units)
- AI Question Bank Generation
- Adaptive Session Engine (Daily Practice, Chapter Revision)
- Evaluation Engine
- Student Mastery & Review Scheduling

## Setup
1. `python -m venv venv`
2. `source venv/bin/activate`
3. `pip install -r requirements.txt`
4. `uvicorn app.main:app --reload`
