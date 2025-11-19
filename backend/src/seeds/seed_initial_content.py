"""
Seed initial relational data for Subjects → Modules → Lessons → Activities/Quizzes,
and also seed progressive Skills for key topics.

Usage:
    python -m src.seeds.seed_initial_content

If SEED_RELATIONAL_DATA=true is set, this will run once on FastAPI startup.

Idempotent behavior: all inserts are done by checking unique slugs/keys first.
"""
from __future__ import annotations

from typing import Dict

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.db.table_init import create_all_tables
from src.db.sqlalchemy import get_engine, get_session_factory
from src.db.relational_models import Subject, Skill, Module, Lesson, Activity
from .seed_progressive_skills import run as run_progressive_skills


# PUBLIC_INTERFACE
def seed_initial_content(session: Session) -> Dict[str, int]:
    """Seed baseline relational content and progressive skills.

    This calls the progressive skills seed (idempotent) and then returns counts of
    key relational entities for observability.

    Args:
        session: An active SQLAlchemy Session.

    Returns:
        Dict[str, int]: Counts of subjects, modules, lessons, activities, quizzes, and skills.
    """
    # The progressive seed handles creating subjects, skills, modules, lessons, activities.
    # It opens its own session internally to be self-contained/idempotent.
    run_progressive_skills()

    # After seeding, compute counts using the provided session.
    counts = {
        "subjects": session.execute(select(func.count(Subject.id))).scalar_one(),
        "skills": session.execute(select(func.count(Skill.id))).scalar_one(),
        "modules": session.execute(select(func.count(Module.id))).scalar_one(),
        "lessons": session.execute(select(func.count(Lesson.id))).scalar_one(),
        "activities": session.execute(select(func.count(Activity.id))).scalar_one(),
        # quizzes are activities with type='quiz'
        "quizzes": session.execute(
            select(func.count(Activity.id)).where(Activity.type == "quiz")
        ).scalar_one(),
    }
    return counts


def main() -> None:
    """CLI entrypoint to run the seed script manually.

    Initializes tables if missing, runs seeding idempotently, and prints entity counts.
    """
    # Ensure engine and tables exist
    _ = get_engine()
    # Create tables (safe if already exist)
    import asyncio  # local import to avoid unused when used as module
    asyncio.run(create_all_tables())

    # Use a new session for counting/logging
    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        counts = seed_initial_content(session)

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
