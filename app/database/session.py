from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Generator
from app.core.config import settings

# Create the SQLAlchemy Engine
# The engine is the starting point for any SQLAlchemy application
# Use database_url_fixed to normalize postgres:// -> postgresql:// (Render compatibility)
engine = create_engine(
    settings.database_url_fixed,
    pool_pre_ping=True,  # Tests the connection before issuing a query
    echo=settings.DEBUG  # Prints SQL queries in the terminal if DEBUG is True
)

# SessionLocal class will be used to create actual database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all SQLAlchemy ORM models
Base = declarative_base()

# Dependency to be used in FastAPI endpoints to get the database session
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
