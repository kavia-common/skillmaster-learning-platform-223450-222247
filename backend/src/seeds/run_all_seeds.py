"""
PUBLIC_INTERFACE
Seed Runner - Execute all seed scripts to populate both content and relational data.

This module provides a single entry point to run all seeding logic required for
local development or initial environment bootstrapping.

Usage:
    PYTHONPATH=backend python3 -m src.seeds.run_all_seeds

Behavior:
- Ensures relational tables exist
- Seeds initial subjects, skills (progressive), modules, lessons, activities
- Seeds initial content for /content/* endpoints if present

Notes:
- Idempotent: Seeding can be safely re-run multiple times
- Configuration: Uses environment variables read by backend config
"""
import asyncio
import logging
import os
import sys

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("seed_runner")


def _safe_log_exc(label: str, e: Exception) -> None:
    logger.exception("Seed step failed (%s): %s", label, e)


# PUBLIC_INTERFACE
def run_all_seeds() -> None:
    """Run all available seeds idempotently in a deterministic order.

    Steps:
    1) Ensure relational tables exist (safe to re-run).
    2) Seed progressive skills + minimal content.
    3) Print entity counts.

    Notes:
    - This function is safe to call multiple times.
    - It avoids optional content seeds that are not present to prevent noise.
    """
    failures = 0

    # 1) Initialize relational tables
    try:
        from src.db.table_init import create_all_tables

        # create_all_tables is async-compatible; run in event loop
        asyncio.run(create_all_tables())
        logger.info("Relational tables initialized (or already existed).")
    except Exception as e:
        _safe_log_exc("Initialize relational tables", e)
        failures += 1

    # 2) Progressive skills and baseline relational content
    try:
        # Seed progressive skills (idempotent)
        from src.seeds.seed_progressive_skills import run as run_progressive

        run_progressive()
        logger.info("Progressive skills seed completed.")
    except Exception as e:
        _safe_log_exc("Seed progressive skills", e)
        failures += 1

    # 3) Compute/print counts via seed_initial_content helper (does counting)
    try:
        from src.db.sqlalchemy import get_session_factory
        from src.seeds.seed_initial_content import seed_initial_content

        SessionFactory = get_session_factory()
        with SessionFactory() as session:
            counts = seed_initial_content(session)
        logger.info(
            "Seed complete: subjects=%s, skills=%s, modules=%s, lessons=%s, activities=%s, quizzes=%s",
            counts.get("subjects"),
            counts.get("skills"),
            counts.get("modules"),
            counts.get("lessons"),
            counts.get("activities"),
            counts.get("quizzes"),
        )
    except Exception as e:
        _safe_log_exc("Finalize counts", e)
        failures += 1

    if failures:
        raise SystemExit(f"Seeding completed with {failures} failure(s).")

    logger.info("All seeds completed successfully.")


if __name__ == "__main__":
    try:
        run_all_seeds()
    except SystemExit:
        raise
    except Exception as e:
        logger.exception("Seeding crashed: %s", e)
        sys.exit(1)
