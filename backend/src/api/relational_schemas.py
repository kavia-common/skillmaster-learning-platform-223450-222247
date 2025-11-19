"""
Pydantic schemas for the relational learning hierarchy.

These schemas support list/detail endpoints and nested reads. They include timestamps
and soft delete flags for admin/maintenance views but typically omit is_deleted on reads.

Includes Skill concept with progression level and binding to Subject.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class _BaseSchema(BaseModel):
    """Base schema with config suitable for ORM mode."""
    # PUBLIC_INTERFACE
    class Config:
        from_attributes = True


# PUBLIC_INTERFACE
class ActivityRead(_BaseSchema):
    """Represents an activity for API reads (content or quiz)."""
    id: int
    lesson_id: int
    type: str = Field(..., description="content | quiz")
    title: str
    content: Optional[str] = None
    order_index: int
    quiz_questions: Optional[list] = Field(None, description="Quiz questions (array)")
    quiz_pass_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime


# PUBLIC_INTERFACE
class LessonRead(_BaseSchema):
    """Lesson detail with nested activities for read endpoints."""
    id: int
    module_id: int
    slug: str
    title: str
    content: str
    order_index: int
    activities: List[ActivityRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


# PUBLIC_INTERFACE
class ModuleRead(_BaseSchema):
    """Module detail including nested lessons."""
    id: int
    subject_id: int
    slug: str
    title: str
    description: Optional[str] = None
    order_index: int
    lessons: List[LessonRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


# PUBLIC_INTERFACE
class SubjectRead(_BaseSchema):
    """Subject detail including nested modules."""
    id: int
    slug: str
    title: str
    description: Optional[str] = None
    modules: List[ModuleRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


# PUBLIC_INTERFACE
class SkillRead(_BaseSchema):
    """Skill read model with progression level."""
    id: int
    subject_id: int
    name: str
    slug: str
    description: Optional[str] = None
    level: str
    tags: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime


# Create/update payloads

# PUBLIC_INTERFACE
class SubjectCreate(_BaseSchema):
    """Create payload for a subject."""
    slug: str = Field(..., min_length=1, max_length=150)
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


# PUBLIC_INTERFACE
class SkillCreate(_BaseSchema):
    """Create payload for a skill under a subject."""
    subject_id: int = Field(..., description="Parent subject/topic id")
    name: str = Field(..., description="Skill display name")
    slug: str = Field(..., description="URL-safe slug")
    description: Optional[str] = Field(None, description="Short description")
    level: str = Field(..., description="Beginner|Intermediate|Advanced")
    tags: Optional[List[str]] = Field(default=None, description="Tags")

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        allowed = {"Beginner", "Intermediate", "Advanced"}
        if v not in allowed:
            raise ValueError("level must be one of Beginner|Intermediate|Advanced")
        return v


# PUBLIC_INTERFACE
class ModuleCreate(_BaseSchema):
    """Create payload for a module."""
    subject_id: int
    slug: str
    title: str
    description: Optional[str] = None
    order_index: int = 0
    skill_id: Optional[int] = Field(default=None, description="Optional link to skill for progression grouping")


# PUBLIC_INTERFACE
class LessonCreate(_BaseSchema):
    """Create payload for a lesson."""
    module_id: int
    slug: str
    title: str
    content: str
    order_index: int = 0


# PUBLIC_INTERFACE
class ActivityCreate(_BaseSchema):
    """Create payload for an activity (content or quiz)."""
    lesson_id: int
    type: str = Field(default="content")
    title: str
    content: Optional[str] = None
    order_index: int = 0
    quiz_questions: Optional[list] = None
    quiz_pass_score: Optional[float] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in ("content", "quiz"):
            raise ValueError("type must be 'content' or 'quiz'")
        return v

    @field_validator("quiz_questions")
    @classmethod
    def validate_quiz(cls, v: Optional[list], info):
        type_val = info.data.get("type")
        if type_val == "quiz":
            if not isinstance(v, list) or len(v) == 0:
                raise ValueError("quiz_questions must be a non-empty list for quiz type")
        return v


# PUBLIC_INTERFACE
class ProgressRead(_BaseSchema):
    """Progress entry read schema."""
    id: int
    user_id: str
    subject_id: Optional[int] = None
    module_id: Optional[int] = None
    lesson_id: Optional[int] = None
    activity_id: Optional[int] = None
    completed: bool = False
    score: Optional[float] = None
    created_at: datetime
    updated_at: datetime


# PUBLIC_INTERFACE
class ProgressCreate(_BaseSchema):
    """Create payload for progress."""
    user_id: str
    subject_id: Optional[int] = None
    module_id: Optional[int] = None
    lesson_id: Optional[int] = None
    activity_id: Optional[int] = None
    completed: bool = True
    score: Optional[float] = Field(None, ge=0, le=100)
