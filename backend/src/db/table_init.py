"""
Utility to initialize relational database tables.

Usage options:
1) Programmatic (at app startup if desired):
    from src.db.table_init import create_all_tables
    await create_all_tables()  # although sync, kept as awaitable for symmetry

2) CLI:
    python -m src.db.table_init

This uses SQLAlchemy engine and the declarative Base to create tables defined
in src.db.relational_models.
"""

from __future__ import annotations

import asyncio

from src.db.sqlalchemy import Base, get_engine
# Import models to ensure they are registered with Base.metadata
from src.db import relational_models as _  # noqa: F401


# PUBLIC_INTERFACE
async def create_all_tables() -> None:
    """Create all tables for the relational models if they don't exist."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    asyncio.run(create_all_tables())
