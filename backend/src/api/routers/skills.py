"""Skills API routes."""

from typing import List

from fastapi import APIRouter

from src.api.dependencies import SkillRepoDep
from src.api.schemas import SkillDetail, SkillSummary
from src.services.skill_service import SkillService

router = APIRouter(prefix="/skills", tags=["Skills"])


@router.get("", summary="List skills", description="Retrieve all available skills.", response_model=List[SkillSummary])
def list_skills(repo: SkillRepoDep) -> List[SkillSummary]:
    """Return all skills as summaries."""
    service = SkillService(repo)
    return [SkillSummary.from_skill(s) for s in service.list_skills()]


@router.get(
    "/{skill_id}",
    summary="Get skill detail",
    description="Retrieve a specific skill by ID, including modules and lessons.",
    response_model=SkillDetail,
)
def get_skill(skill_id: str, repo: SkillRepoDep) -> SkillDetail:
    """Get detailed skill information."""
    service = SkillService(repo)
    skill = service.get_skill(skill_id)
    return SkillDetail.from_skill(skill)


@router.get(
    "/{skill_id}/modules",
    summary="List modules for a skill",
    description="Return all modules belonging to the specified skill.",
)
def list_modules(skill_id: str, repo: SkillRepoDep):
    """List modules for a given skill."""
    service = SkillService(repo)
    return service.list_modules(skill_id)
