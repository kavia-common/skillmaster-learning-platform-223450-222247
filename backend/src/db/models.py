"""MongoDB document models for SkillMaster using Pydantic for validation.

These are not ODM models but define the document structure stored in MongoDB.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from bson import ObjectId  # type: ignore
from pydantic import BaseModel, Field, field_validator
from pydantic.config import ConfigDict


def _objectid_encoder(v: Any) -> Optional[str]:
    """Convert Mongo ObjectId to string safely."""
    try:
        if isinstance(v, ObjectId):
            return str(v)
        return str(v) if v is not None else None
    except Exception:
        return None


class _BaseMongoModel(BaseModel):
    """Base Pydantic model for MongoDB documents with alias support and encoders."""
    # PUBLIC_INTERFACE
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: _objectid_encoder},
    )


class BadgeModel(_BaseMongoModel):
    """Represents a badge awarded for a lesson or skill completion."""
    name: str = Field(..., description="Badge display name")
    points: int = Field(..., ge=0, le=1000, description="Point value for the badge")


class QuizQuestionModel(_BaseMongoModel):
    """Single quiz question with four options and a correct answer index."""
    question: str = Field(..., description="Question prompt")
    options: List[str] = Field(..., min_length=4, max_length=4, description="Exactly 4 options")
    answerIndex: int = Field(..., ge=0, le=3, description="Index into options array (0-3)")

    @field_validator("options")
    @classmethod
    def validate_options(cls, v: List[str]) -> List[str]:
        if len(v) != 4:
            raise ValueError("Quiz question must have exactly 4 options")
        if any(not opt.strip() for opt in v):
            raise ValueError("Quiz options must be non-empty strings")
        return v


class LessonModel(_BaseMongoModel):
    """Lesson document."""
    # Use public field name with Mongo alias for compatibility
    id: Optional[str] = Field(default=None, alias="_id", description="Mongo id (stringified ObjectId)")
    title: str = Field(..., description="Lesson title")
    slug: str = Field(..., description="URL-safe slug for the lesson")
    summary: Optional[str] = Field(None, description="Short lesson summary")
    content: str = Field(..., description="Lesson content in markdown")
    media: Optional[str] = Field(None, description="Optional media URL")
    tags: List[str] = Field(default_factory=list, description="Lesson tags")
    difficulty: str = Field(default="Beginner", description="Difficulty level")
    quiz: List[QuizQuestionModel] = Field(..., min_length=3, max_length=3, description="Exactly 3 quiz questions")
    badge: BadgeModel = Field(..., description="Badge awarded upon completion")
    skillSlug: str = Field(..., description="Parent skill slug")
    category: str = Field(..., description="Parent category name")
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)


class SkillModel(_BaseMongoModel):
    """Skill document with categorization."""
    id: Optional[str] = Field(default=None, alias="_id", description="Mongo id (stringified ObjectId)")
    name: str = Field(..., description="Skill name")
    slug: str = Field(..., description="URL-safe slug for the skill")
    category: str = Field(..., description="Skill category grouping")
    description: Optional[str] = Field(None, description="Short description")
    tags: List[str] = Field(default_factory=list, description="Tags")
    difficulty: str = Field(default="Beginner", description="Default difficulty for the skill")
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)


class ProgressModel(_BaseMongoModel):
    """User lesson progress entry."""
    id: Optional[str] = Field(default=None, alias="_id", description="Mongo id (stringified ObjectId)")
    userId: str = Field(..., description="User id")
    skillSlug: str = Field(..., description="Skill slug")
    lessonSlug: str = Field(..., description="Lesson slug")
    completed: bool = Field(default=False)
    score: Optional[float] = Field(None, ge=0, le=100)
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)


class UserModel(_BaseMongoModel):
    """User document placeholder (for future auth use)."""
    id: Optional[str] = Field(default=None, alias="_id", description="Mongo id (stringified ObjectId)")
    email: str = Field(..., description="User email")
    name: Optional[str] = Field(None, description="User name")
    role: str = Field(default="user", description="Role (user/admin)")
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)
