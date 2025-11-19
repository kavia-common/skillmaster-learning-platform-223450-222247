"""
Seed initial relational data for Subjects → Modules → Lessons → Activities/Quizzes,
and also seed progressive Skills for key topics.

Usage:
    python -m src.seeds.seed_initial_content

If SEED_RELATIONAL_DATA=true is set, this will run once on FastAPI startup.

Idempotent behavior: all inserts are done by checking unique slugs/keys first.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from src.db.table_init import init_all_tables
from src.db.sqlalchemy import get_engine, get_session_factory
from .seed_progressive_skills import run as run_progressive_skills


# PUBLIC_INTERFACE
def seed_initial_content(session: Session) -> None:
    """Seed baseline relational content and progressive skills.

    This function currently focuses on seeding progressive Skills and minimal content
    by delegating to `seed_progressive_skills.run()`, which is idempotent.
    """
    # The progressive seed handles creating subjects, skills, modules, lessons, activities.
    # It opens its own session internally, so nothing is needed with the provided session.
    run_progressive_skills()


def main() -> None:
    """CLI entrypoint to run the seed script manually."""
    engine = get_engine()
    init_all_tables(engine)
    SessionFactory = get_session_factory(engine)
    with SessionFactory() as session:
        seed_initial_content(session)


if __name__ == "__main__":
    main()
