"""Domain models for the SkillMaster backend.

This module defines the Pydantic models that represent the core domain entities:
- Skill
- Module
- Lesson
- ProgressEntry
- UserProgress

These models are used across repositories and services, and serialized via the API.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# PUBLIC_INTERFACE
class Lesson(BaseModel):
    """A single lesson within a module."""

    id: str = Field(..., description="Unique identifier for the lesson")
    module_id: str = Field(..., description="Identifier of the parent module")
    title: str = Field(..., description="Lesson title")
    content: str = Field(..., description="Lesson content in markdown or rich-text format")
    order: int = Field(..., description="Ordering index of the lesson within a module")


# PUBLIC_INTERFACE
class Module(BaseModel):
    """A module within a skill, containing a list of lessons."""

    id: str = Field(..., description="Unique identifier for the module")
    skill_id: str = Field(..., description="Identifier of the parent skill")
    title: str = Field(..., description="Module title")
    description: Optional[str] = Field(None, description="Optional description for the module")
    order: int = Field(..., description="Ordering index of the module within a skill")
    lessons: List[Lesson] = Field(default_factory=list, description="Lessons contained in this module")


# PUBLIC_INTERFACE
class Skill(BaseModel):
    """A skill that learners can master, consisting of modules and lessons."""

    id: str = Field(..., description="Unique identifier for the skill")
    name: str = Field(..., description="Human-friendly name of the skill")
    description: Optional[str] = Field(None, description="Brief description of the skill")
    modules: List[Module] = Field(default_factory=list, description="Modules that belong to the skill")
    tags: List[str] = Field(default_factory=list, description="Tags for discovery and filtering")


# PUBLIC_INTERFACE
class ProgressEntry(BaseModel):
    """A progress entry recording a user's interaction with a lesson."""

    id: str = Field(..., description="Unique identifier for this progress entry")
    user_id: str = Field(..., description="Identifier for the user this progress belongs to")
    skill_id: str = Field(..., description="Identifier for the related skill")
    module_id: str = Field(..., description="Identifier for the related module")
    lesson_id: str = Field(..., description="Identifier for the related lesson")
    completed: bool = Field(False, description="Whether the lesson was completed")
    score: Optional[float] = Field(None, description="Optional score or grade for the lesson")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the progress was recorded")


# PUBLIC_INTERFACE
class UserProgress(BaseModel):
    """Aggregated progress for a user, across skills and lessons."""

    user_id: str = Field(..., description="Identifier of the user")
    entries: List[ProgressEntry] = Field(default_factory=list, description="All progress entries for the user")

    # PUBLIC_INTERFACE
    def completion_rate_for_skill(self, skill: Skill) -> float:
        """Calculate the completion rate for a given skill.

        Returns a number between 0 and 1 representing the fraction of lessons completed.

        Args:
            skill: The Skill to compute completion for.

        Returns:
            float: Completion rate in [0, 1]. Returns 0 if the skill has no lessons.
        """
        total_lessons = sum(len(m.lessons) for m in skill.modules)
        if total_lessons == 0:
            return 0.0
        completed_lessons = 0
        completed_ids = {e.lesson_id for e in self.entries if e.completed}
        for module in skill.modules:
            for lesson in module.lessons:
                if lesson.id in completed_ids:
                    completed_lessons += 1
        return completed_lessons / total_lessons
