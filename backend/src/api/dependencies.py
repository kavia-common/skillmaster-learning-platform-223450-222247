"""FastAPI dependencies and common utilities for injecting repositories, config, and database sessions."""

from typing import Annotated, Generator

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from src.config import Config
from src.repositories.memory_repository import InMemoryRepository, ProgressRepository, SkillRepository
from src.db.sqlalchemy import get_session_factory


# PUBLIC_INTERFACE
def get_config_dep(request: Request) -> Config:
    """Return the application configuration stored on app.state."""
    return request.app.state.config  # type: ignore[attr-defined]


# PUBLIC_INTERFACE
def get_repository_dep(request: Request) -> InMemoryRepository:
    """Return the default in-memory repository from app.state."""
    # In this prototype we have a single repo implementing both interfaces.
    return request.app.state.repositories["default"]  # type: ignore[attr-defined]


# PUBLIC_INTERFACE
def get_db() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy Session bound to the configured engine.

    This dependency creates a scoped Session from the global session factory and
    ensures it is closed after the request finishes.

    Environment:
        Requires SQLALCHEMY_DATABASE_URL to be set in the environment for non-SQLite
        databases. Defaults to a local SQLite file for development if not provided.

    Yields:
        sqlalchemy.orm.Session: Active session for DB operations.
    """
    SessionFactory = get_session_factory()
    db: Session = SessionFactory()
    try:
        yield db
    finally:
        # Make sure connections are returned to the pool and resources released
        db.close()


# Aliases typed for clarity in route signatures
ConfigDep = Annotated[Config, Depends(get_config_dep)]
RepoDep = Annotated[InMemoryRepository, Depends(get_repository_dep)]
SkillRepoDep = Annotated[SkillRepository, Depends(get_repository_dep)]
ProgressRepoDep = Annotated[ProgressRepository, Depends(get_repository_dep)]
DbSessionDep = Annotated[Session, Depends(get_db)]
