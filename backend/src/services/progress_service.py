"""Business logic related to user progress and lesson completion."""

from __future__ import annotations

from typing import List, Optional

from src.api.errors import ApplicationError, ErrorCode
from src.domain.models import ProgressEntry, UserProgress
from src.repositories.memory_repository import ProgressRepository, SkillRepository


class ProgressService:
    """Service orchestrating user progress operations across repositories."""

    def __init__(self, progress_repo: ProgressRepository, skill_repo: SkillRepository) -> None:
        self._progress_repo = progress_repo
        self._skill_repo = skill_repo

    # PUBLIC_INTERFACE
    def get_user_progress(self, user_id: str) -> UserProgress:
        """Get or initialize a user's progress aggregate."""
        return self._progress_repo.get_user_progress(user_id)

    # PUBLIC_INTERFACE
    def mark_lesson_completed(
        self, user_id: str, skill_id: str, module_id: str, lesson_id: str, score: Optional[float] = None
    ) -> ProgressEntry:
        """Mark a lesson as completed, validating the skill/module/lesson relationship.

        Raises:
            ApplicationError: If skill/module/lesson relationship is invalid.
        """
        # Validate the skill exists and the module/lesson belong to it
        skill = self._skill_repo.get_skill(skill_id)
        if not skill:
            raise ApplicationError(
                "Skill not found", ErrorCode.NOT_FOUND, 404, {"skill_id": skill_id}
            )

        module = next((m for m in skill.modules if m.id == module_id), None)
        if not module:
            raise ApplicationError(
                "Module not found in skill",
                ErrorCode.NOT_FOUND,
                404,
                {"skill_id": skill_id, "module_id": module_id},
            )

        lesson = next((l for l in module.lessons if l.id == lesson_id), None)
        if not lesson:
            raise ApplicationError(
                "Lesson not found in module",
                ErrorCode.NOT_FOUND,
                404,
                {"skill_id": skill_id, "module_id": module_id, "lesson_id": lesson_id},
            )

        # Basic score validation if provided
        if score is not None:
            if score < 0 or score > 100:
                raise ApplicationError(
                    "Score must be between 0 and 100",
                    ErrorCode.BAD_REQUEST,
                    400,
                    {"score": score},
                )

        return self._progress_repo.mark_lesson_completed(user_id, skill_id, module_id, lesson_id, score)

    # PUBLIC_INTERFACE
    def get_progress_for_lesson(self, user_id: str, lesson_id: str) -> List[ProgressEntry]:
        """Return all progress entries for a given user and lesson."""
        return self._progress_repo.get_progress_for_lesson(user_id, lesson_id)
