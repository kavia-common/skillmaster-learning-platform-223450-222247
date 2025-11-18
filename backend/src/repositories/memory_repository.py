"""Repository interfaces and an in-memory implementation with seeded data.

This module defines simple repository interfaces for Skills and User Progress,
and provides an in-memory implementation that can be used for development
and testing prior to integrating a persistent data store.

Repositories:
- SkillRepository
- ProgressRepository

InMemoryRepository provides both interfaces.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Protocol
from datetime import datetime

from src.domain.models import Skill, Module, Lesson, ProgressEntry, UserProgress


# PUBLIC_INTERFACE
class SkillRepository(Protocol):
    """Repository interface for working with skills."""

    # PUBLIC_INTERFACE
    def list_skills(self) -> List[Skill]:
        """Return all available skills."""

    # PUBLIC_INTERFACE
    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """Get a single skill by ID."""

    # PUBLIC_INTERFACE
    def list_modules(self, skill_id: str) -> List[Module]:
        """List modules for a given skill."""

    # PUBLIC_INTERFACE
    def list_lessons(self, module_id: str) -> List[Lesson]:
        """List lessons for a given module."""


# PUBLIC_INTERFACE
class ProgressRepository(Protocol):
    """Repository interface for reading/writing user progress."""

    # PUBLIC_INTERFACE
    def get_user_progress(self, user_id: str) -> UserProgress:
        """Get aggregated progress for a user."""

    # PUBLIC_INTERFACE
    def add_progress_entry(self, entry: ProgressEntry) -> ProgressEntry:
        """Add a new progress entry."""

    # PUBLIC_INTERFACE
    def mark_lesson_completed(
        self, user_id: str, skill_id: str, module_id: str, lesson_id: str, score: Optional[float] = None
    ) -> ProgressEntry:
        """Create a completion progress entry for a lesson."""

    # PUBLIC_INTERFACE
    def get_progress_for_lesson(self, user_id: str, lesson_id: str) -> List[ProgressEntry]:
        """Get all progress entries for a specific lesson for the given user."""


class InMemoryRepository(SkillRepository, ProgressRepository):
    """In-memory repository for skills and user progress.

    This repository is safe for single-process development use. It is not thread-safe.
    """

    def __init__(self) -> None:
        self._skills: Dict[str, Skill] = {}
        # Keyed by user_id
        self._user_progress: Dict[str, UserProgress] = {}
        # Seed some initial data
        self._seed_data()

    def _seed_data(self) -> None:
        """Initialize the in-memory store with a few example skills, modules, and lessons."""
        # Skill: Python Basics
        py_lessons_1 = [
            Lesson(id="py-l1", module_id="py-m1", title="Introduction to Python", content="Basics and history.", order=1),
            Lesson(id="py-l2", module_id="py-m1", title="Variables and Types", content="Numbers, strings, bools.", order=2),
        ]
        py_lessons_2 = [
            Lesson(id="py-l3", module_id="py-m2", title="Control Flow", content="if, for, while, match.", order=1),
            Lesson(id="py-l4", module_id="py-m2", title="Functions", content="Defining and calling functions.", order=2),
        ]
        py_modules = [
            Module(id="py-m1", skill_id="py", title="Getting Started", description="Overview", order=1, lessons=py_lessons_1),
            Module(id="py-m2", skill_id="py", title="Core Concepts", description="Flow and functions", order=2, lessons=py_lessons_2),
        ]
        python_skill = Skill(
            id="py",
            name="Python Basics",
            description="Learn the fundamentals of Python.",
            modules=py_modules,
            tags=["programming", "python", "beginner"],
        )

        # Skill: Web Accessibility
        a11y_lessons_1 = [
            Lesson(id="a11y-l1", module_id="a11y-m1", title="Intro to A11y", content="Why accessibility matters.", order=1),
            Lesson(id="a11y-l2", module_id="a11y-m1", title="Semantic HTML", content="Use proper elements.", order=2),
        ]
        a11y_modules = [
            Module(id="a11y-m1", skill_id="a11y", title="Foundations", description="Basics of a11y", order=1, lessons=a11y_lessons_1),
        ]
        a11y_skill = Skill(
            id="a11y",
            name="Web Accessibility",
            description="Build inclusive and accessible web experiences.",
            modules=a11y_modules,
            tags=["web", "a11y", "frontend"],
        )

        self._skills[python_skill.id] = python_skill
        self._skills[a11y_skill.id] = a11y_skill

        # Seed a sample user progress
        sample_user_id = "user-123"
        entries = [
            ProgressEntry(
                id="p1",
                user_id=sample_user_id,
                skill_id="py",
                module_id="py-m1",
                lesson_id="py-l1",
                completed=True,
                score=95.0,
                timestamp=datetime.utcnow(),
            )
        ]
        self._user_progress[sample_user_id] = UserProgress(user_id=sample_user_id, entries=entries)

    # SkillRepository implementation
    def list_skills(self) -> List[Skill]:
        return list(self._skills.values())

    def get_skill(self, skill_id: str) -> Optional[Skill]:
        return self._skills.get(skill_id)

    def list_modules(self, skill_id: str) -> List[Module]:
        skill = self._skills.get(skill_id)
        return skill.modules if skill else []

    def list_lessons(self, module_id: str) -> List[Lesson]:
        for skill in self._skills.values():
            for module in skill.modules:
                if module.id == module_id:
                    return module.lessons
        return []

    # ProgressRepository implementation
    def get_user_progress(self, user_id: str) -> UserProgress:
        if user_id not in self._user_progress:
            self._user_progress[user_id] = UserProgress(user_id=user_id, entries=[])
        return self._user_progress[user_id]

    def add_progress_entry(self, entry: ProgressEntry) -> ProgressEntry:
        progress = self.get_user_progress(entry.user_id)
        progress.entries.append(entry)
        self._user_progress[entry.user_id] = progress
        return entry

    def mark_lesson_completed(
        self, user_id: str, skill_id: str, module_id: str, lesson_id: str, score: Optional[float] = None
    ) -> ProgressEntry:
        new_entry = ProgressEntry(
            id=f"pe-{user_id}-{lesson_id}-{int(datetime.utcnow().timestamp())}",
            user_id=user_id,
            skill_id=skill_id,
            module_id=module_id,
            lesson_id=lesson_id,
            completed=True,
            score=score,
            timestamp=datetime.utcnow(),
        )
        return self.add_progress_entry(new_entry)

    def get_progress_for_lesson(self, user_id: str, lesson_id: str) -> List[ProgressEntry]:
        progress = self.get_user_progress(user_id)
        return [e for e in progress.entries if e.lesson_id == lesson_id]
