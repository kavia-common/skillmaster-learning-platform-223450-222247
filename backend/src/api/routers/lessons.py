"""Lessons API routes."""

from fastapi import APIRouter

from src.api.dependencies import SkillRepoDep
from src.services.skill_service import SkillService

router = APIRouter(prefix="/modules", tags=["Lessons"])


@router.get(
    "/{module_id}/lessons",
    summary="List lessons for a module",
    description="Retrieve all lessons for a given module.",
)
def list_lessons(module_id: str, repo: SkillRepoDep):
    """Return the lessons contained within a module."""
    service = SkillService(repo)
    return service.list_lessons_for_module(module_id)
