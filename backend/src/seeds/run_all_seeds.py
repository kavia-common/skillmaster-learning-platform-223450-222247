"""One-off CLI to run all seeders idempotently without starting the server.

Usage:
    python -m src.seeds.run_all_seeds

Behavior:
- Ensures relational tables exist.
- Runs progressive skills/content seeding.
- Outputs counts for Subjects, Skills, Modules, Lessons, Activities, and Quizzes.
"""
from __future__ import annotations

import asyncio
from typing import Dict

# PUBLIC_INTERFACE
def run_all() -> Dict[str, int]:
    """Run all seeders and return entity counts."""
    from src.db.table_init import create_all_tables
    from src.db.sqlalchemy import get_engine, get_session_factory
    from src.seeds.seed_initial_content import seed_initial_content

    # Ensure engine initialized and tables created
    _ = get_engine()
    asyncio.run(create_all_tables())

    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        counts = seed_initial_content(session)

    return counts


def main() -> None:
    """CLI entrypoint to run all seeders and print results."""
    counts = run_all()
    print(
        "Seed complete: "
        f"subjects={counts['subjects']}, "
        f"skills={counts['skills']}, "
        f"modules={counts['modules']}, "
        f"lessons={counts['lessons']}, "
        f"activities={counts['activities']}, "
        f"quizzes={counts['quizzes']}"
    )


if __name__ == "__main__":
    main()
