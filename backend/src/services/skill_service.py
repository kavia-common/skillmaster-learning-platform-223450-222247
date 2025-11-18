"""Business logic related to skills, modules, and lessons."""

from __future__ import annotations

from typing import List, Optional

from src.api.errors import ApplicationError, ErrorCode
from src.domain.models import Lesson, Module, Skill
from src.repositories.memory_repository import SkillRepository


class SkillService:
    """Service for querying skills and related entities."""

    def __init__(self, repo: SkillRepository) -> None:
        self._repo = repo

    # PUBLIC_INTERFACE
    def list_skills(self) -> List[Skill]:
        """Return all skills available in the repository."""
        return self._repo.list_skills()

    # PUBLIC_INTERFACE
    def get_skill(self, skill_id: str) -> Skill:
        """Retrieve a single skill or raise NOT_FOUND ApplicationError."""
        skill: Optional[Skill] = self._repo.get_skill(skill_id)
        if not skill:
            raise ApplicationError(
                message="Skill not found",
                code=ErrorCode.NOT_FOUND,
                status_code=404,
                details={"skill_id": skill_id},
            )
        return skill

    # PUBLIC_INTERFACE
    def list_modules(self, skill_id: str) -> List[Module]:
        """List modules for a skill, validating skill existence first."""
        _ = self.get_skill(skill_id)  # validates existence
        return self._repo.list_modules(skill_id)

    # PUBLIC_INTERFACE
    def list_lessons_for_module(self, module_id: str) -> List[Lesson]:
        """List lessons for a module, or an empty list if module not found."""
        return self._repo.list_lessons(module_id)
