"""
SQLAlchemy setup: engine, session factory, and Base.

This module provides a relational database layer to support hierarchical
Subject → Module → Lesson → Activity/Quiz and Progress tracking.

Configuration:
- Uses environment variable SQLALCHEMY_DATABASE_URL for the connection string.
- For SQLite URLs, this module sets check_same_thread=False automatically for dev-friendly concurrency.
- Do not hardcode secrets. Ensure .env provides SQLALCHEMY_DATABASE_URL.

Typical usage:
    from src.db.sqlalchemy import Base, get_engine, get_session_factory
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Global declarative base for models
Base = declarative_base()

_DEFAULT_DB_URL = "sqlite:///./skillmaster.db"


# PUBLIC_INTERFACE
def get_sqlalchemy_url() -> str:
    """Return SQLAlchemy database URL from environment or default to local SQLite.

    Env var:
        SQLALCHEMY_DATABASE_URL: Full SQLAlchemy connection URL (e.g., postgresql+psycopg://...).

    Returns:
        str: The connection URL.
    """
    # For local/dev environments we allow sqlite as a simple default.
    # In deployed environments, configure SQLALCHEMY_DATABASE_URL via secrets.
    return os.getenv("SQLALCHEMY_DATABASE_URL", _DEFAULT_DB_URL)


_engine = None
_SessionFactory: Optional[sessionmaker] = None


# PUBLIC_INTERFACE
def get_engine():
    """Get or create the SQLAlchemy engine singleton."""
    global _engine
    if _engine is not None:
        return _engine
    url = get_sqlalchemy_url()
    connect_args = {}
    # SQLite requires special connect args for multithreaded usage in dev
    if url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    _engine = create_engine(url, echo=False, future=True, connect_args=connect_args)
    return _engine


# PUBLIC_INTERFACE
def get_session_factory() -> sessionmaker:
    """Return a lazily-initialized sessionmaker bound to the engine."""
    global _SessionFactory
    if _SessionFactory is not None:
        return _SessionFactory
    _SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=get_engine(), class_=Session)
    return _SessionFactory


# PUBLIC_INTERFACE
@contextmanager
def db_session_scope() -> Generator[Session, None, None]:
    """Context manager that provides a transactional session scope.

    Example:
        with db_session_scope() as session:
            # use session
    """
    SessionFactory = get_session_factory()
    session: Session = SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
