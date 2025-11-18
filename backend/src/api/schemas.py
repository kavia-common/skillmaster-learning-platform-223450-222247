"""API schemas (Pydantic models) for request/response bodies."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from src.domain.models import Lesson, Module, ProgressEntry, Skill, UserProgress


# Simple wrappers to expose domain models in responses while allowing future divergence


class SkillSummary(BaseModel):
    """Lightweight summary of a skill for listings."""
    id: str = Field(..., description="Skill id")
    name: str = Field(..., description="Skill display name")
    description: Optional[str] = Field(None, description="Skill description")
    tags: List[str] = Field(default_factory=list, description="Skill tags")

    @staticmethod
    def from_skill(skill: Skill) -> "SkillSummary":
        return SkillSummary(id=skill.id, name=skill.name, description=skill.description, tags=skill.tags)


class SkillDetail(BaseModel):
    """Detailed skill view including modules and lessons."""
    id: str
    name: str
    description: Optional[str]
    tags: List[str]
    modules: List[Module]

    @staticmethod
    def from_skill(skill: Skill) -> "SkillDetail":
        return SkillDetail(
            id=skill.id,
            name=skill.name,
            description=skill.description,
            tags=skill.tags,
            modules=skill.modules,
        )


class LessonDetail(BaseModel):
    """Detailed lesson response."""
    lesson: Lesson


class MarkCompleteRequest(BaseModel):
    """Request body to mark a lesson as completed."""
    user_id: str = Field(..., description="User performing the completion")
    skill_id: str = Field(..., description="Skill id")
    module_id: str = Field(..., description="Module id")
    lesson_id: str = Field(..., description="Lesson id")
    score: Optional[float] = Field(None, description="Optional score between 0-100")


class ProgressEntryResponse(BaseModel):
    """Response wrapper for a single progress entry."""
    entry: ProgressEntry


class UserProgressResponse(BaseModel):
    """Response wrapper for a user's aggregated progress."""
    progress: UserProgress
