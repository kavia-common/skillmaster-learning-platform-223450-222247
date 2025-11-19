"""
DB initialization service for relational models.

This module can be imported in FastAPI startup if we want to ensure tables exist
when the app boots in environments where migrations are not yet configured.
"""

from __future__ import annotations

from src.db.table_init import create_all_tables


# PUBLIC_INTERFACE
async def ensure_relational_schema() -> None:
    """Ensure relational tables exist by calling create_all_tables()."""
    await create_all_tables()
