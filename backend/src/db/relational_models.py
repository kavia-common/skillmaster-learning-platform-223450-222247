"""
Relational SQLAlchemy models for Subject → Module → Lesson → Activity/Quiz and Progress.

This layer complements the existing Mongo-backed catalog and supports
normalized storage for the learning hierarchy. It defines:

- Subject 1:N Module
- Module 1:N Lesson
- Lesson 1:N Activity
- Lesson 1:N Quiz (modeled as Activity subtype via 'type' and optional quiz fields)
- Progress entries referencing lesson-level (and optionally activity-level) completion

All tables include:
- id (surrogate key)
- created_at, updated_at timestamps
- is_deleted soft delete flag

Notes:
- Quiz is treated as a specialized Activity with question JSON payload
  (array of {"question","options":[...4 items...],"answerIndex":0-3}).
- Use server_default timestamps for created_at, updated_at; app code should update updated_at on writes.

Migrations:
- This project doesn't have Alembic configured; provide a helper to create_all
  consistent with project patterns. See src/db/table_init.py for init utility.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.sqlalchemy import Base


def utcnow() -> datetime:
    """Return UTC now; used for default python-side timestamps."""
    return datetime.utcnow()


class TimestampMixin:
    """Adds created/updated timestamps and soft delete flag."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")


class Subject(Base, TimestampMixin):
    """Top-level subject grouping skills/modules."""
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(150), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    modules: Mapped[List["Module"]] = relationship(
        "Module", back_populates="subject", cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint("slug", name="uq_subject_slug"),
    )


class Module(Base, TimestampMixin):
    """A module under a subject."""
    __tablename__ = "modules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    subject: Mapped["Subject"] = relationship("Subject", back_populates="modules")
    lessons: Mapped[List["Lesson"]] = relationship(
        "Lesson", back_populates="module", cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint("subject_id", "slug", name="uq_module_subject_slug"),
        Index("ix_module_subject_order", "subject_id", "order_index"),
    )


class Lesson(Base, TimestampMixin):
    """A lesson under a module."""
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("modules.id", ondelete="CASCADE"), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    module: Mapped["Module"] = relationship("Module", back_populates="lessons")
    activities: Mapped[List["Activity"]] = relationship(
        "Activity", back_populates="lesson", cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint("module_id", "slug", name="uq_lesson_module_slug"),
        Index("ix_lesson_module_order", "module_id", "order_index"),
    )


class ActivityType:
    """Enum-like constants for activity types."""
    CONTENT = "content"
    QUIZ = "quiz"


class Activity(Base, TimestampMixin):
    """An activity within a lesson.

    For quizzes, store JSON in quiz_questions with format:
        [{"question": str, "options": [str, str, str, str], "answerIndex": int(0..3)}, ...]
    """
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False, default=ActivityType.CONTENT, server_default=ActivityType.CONTENT)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # For content-type activities
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    # Quiz-only fields
    quiz_questions: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    quiz_pass_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="activities")

    __table_args__ = (
        CheckConstraint("type in ('content','quiz')", name="ck_activity_type"),
        Index("ix_activity_lesson_order", "lesson_id", "order_index"),
    )


class Progress(Base, TimestampMixin):
    """User progress entries (lesson or activity level)."""
    __tablename__ = "progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    subject_id: Mapped[Optional[int]] = mapped_column(ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True)
    module_id: Mapped[Optional[int]] = mapped_column(ForeignKey("modules.id", ondelete="SET NULL"), nullable=True)
    lesson_id: Mapped[Optional[int]] = mapped_column(ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True)
    activity_id: Mapped[Optional[int]] = mapped_column(ForeignKey("activities.id", ondelete="SET NULL"), nullable=True)

    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships (no backrefs needed for now)
    # subject/module/lesson/activity relationships are optional since we keep history

    __table_args__ = (
        Index("ix_progress_user_lesson_activity", "user_id", "lesson_id", "activity_id"),
    )
