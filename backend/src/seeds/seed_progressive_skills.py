"""
Seed five topics with progressive skills and minimal content.

Topics: Digital, Communication, Career, Leadership, Creativity
Each topic gets three skills: Beginner, Intermediate, Advanced.
Each skill has one module, one lesson, and one content activity (idempotent).
"""

from sqlalchemy.orm import Session
from ..db.sqlalchemy import get_engine_sessionmaker
from ..db.relational_models import Subject, Skill, Module, Lesson, Activity


TOPICS = [
    ("digital", "Digital"),
    ("communication", "Communication"),
    ("career", "Career"),
    ("leadership", "Leadership"),
    ("creativity", "Creativity"),
]

LEVELS = ["Beginner", "Intermediate", "Advanced"]


def _ensure_subject(db: Session, slug: str, title: str) -> Subject:
    subj = db.query(Subject).filter(Subject.slug == slug).first()
    if subj:
        return subj
    subj = Subject(slug=slug, title=title, description=f"{title} topic")
    db.add(subj)
    db.commit()
    db.refresh(subj)
    return subj


def _ensure_skill(db: Session, subject_id: int, subject_slug: str, level: str) -> Skill:
    skill_slug = f"{subject_slug}-{level.lower()}"
    skill_name = f"{subject_slug.capitalize()} {level}"
    skill = db.query(Skill).filter(Skill.slug == skill_slug).first()
    if skill:
        return skill
    skill = Skill(
        subject_id=subject_id,
        name=skill_name,
        slug=skill_slug,
        description=f"{skill_name} path",
        level=level,
        tags=[subject_slug, level],
    )
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


def _ensure_module(db: Session, subject_id: int, skill_id: int, skill_slug: str) -> Module:
    module_slug = f"{skill_slug}-module-1"
    module = db.query(Module).filter(Module.slug == module_slug).first()
    if module:
        return module
    module = Module(
        subject_id=subject_id,
        skill_id=skill_id,
        slug=module_slug,
        title="Getting Started",
        description="Kick-off module",
        order_index=0,
    )
    db.add(module)
    db.commit()
    db.refresh(module)
    return module


def _ensure_lesson(db: Session, module_id: int, skill_slug: str) -> Lesson:
    lesson_slug = f"{skill_slug}-lesson-1"
    lesson = db.query(Lesson).filter(Lesson.slug == lesson_slug).first()
    if lesson:
        return lesson
    lesson = Lesson(
        module_id=module_id,
        slug=lesson_slug,
        title="First Steps",
        content="Welcome! This lesson introduces key concepts and a short activity.",
        order_index=0,
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson


def _ensure_activity(db: Session, lesson_id: int):
    activity = (
        db.query(Activity)
        .filter(Activity.lesson_id == lesson_id, Activity.order_index == 0, Activity.type == "content")
        .first()
    )
    if activity:
        return activity
    activity = Activity(
        lesson_id=lesson_id,
        type="content",
        title="Read: Introduction",
        content="Read the brief introduction and mark complete to proceed.",
        order_index=0,
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


# PUBLIC_INTERFACE
def run():
    """Run the progressive skills seed idempotently."""
    SessionLocal = get_engine_sessionmaker()
    db: Session = SessionLocal()
    try:
        for slug, title in TOPICS:
            subj = _ensure_subject(db, slug, title)
            for level in LEVELS:
                skill = _ensure_skill(db, subj.id, slug, level)
                mod = _ensure_module(db, subj.id, skill.id, skill.slug)
                lesson = _ensure_lesson(db, mod.id, skill.slug)
                _ensure_activity(db, lesson.id)
        print("Progressive skills seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
