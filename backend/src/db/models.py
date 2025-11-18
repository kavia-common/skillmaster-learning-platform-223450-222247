"""MongoDB document models for SkillMaster using Pydantic for validation.

These are not ODM models but define the document structure stored in MongoDB.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class BadgeModel(BaseModel):
    """Represents a badge awarded for a lesson or skill completion."""
    name: str = Field(..., description="Badge display name")
    points: int = Field(..., ge=0, le=1000, description="Point value for the badge")


class QuizQuestionModel(BaseModel):
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


class LessonModel(BaseModel):
    """Lesson document."""
    _id: Optional[str] = Field(default=None, description="Mongo id (stringified ObjectId)")
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


class SkillModel(BaseModel):
    """Skill document with categorization."""
    _id: Optional[str] = Field(default=None, description="Mongo id (stringified ObjectId)")
    name: str = Field(..., description="Skill name")
    slug: str = Field(..., description="URL-safe slug for the skill")
    category: str = Field(..., description="Skill category grouping")
    description: Optional[str] = Field(None, description="Short description")
    tags: List[str] = Field(default_factory=list, description="Tags")
    difficulty: str = Field(default="Beginner", description="Default difficulty for the skill")
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)


class ProgressModel(BaseModel):
    """User lesson progress entry."""
    _id: Optional[str] = Field(default=None)
    userId: str = Field(..., description="User id")
    skillSlug: str = Field(..., description="Skill slug")
    lessonSlug: str = Field(..., description="Lesson slug")
    completed: bool = Field(default=False)
    score: Optional[float] = Field(None, ge=0, le=100)
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)


class UserModel(BaseModel):
    """User document placeholder (for future auth use)."""
    _id: Optional[str] = Field(default=None)
    email: str = Field(..., description="User email")
    name: Optional[str] = Field(None, description="User name")
    role: str = Field(default="user", description="Role (user/admin)")
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)
