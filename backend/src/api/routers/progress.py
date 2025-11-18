"""Progress API routes."""

from typing import List

from fastapi import APIRouter

from src.api.dependencies import ProgressRepoDep, SkillRepoDep
from src.api.schemas import MarkCompleteRequest, ProgressEntryResponse, UserProgressResponse
from src.services.progress_service import ProgressService

router = APIRouter(prefix="/progress", tags=["Progress"])


@router.get(
    "/{user_id}",
    summary="Get user progress",
    description="Return aggregated progress entries for a user.",
    response_model=UserProgressResponse,
)
def get_user_progress(user_id: str, progress_repo: ProgressRepoDep, skill_repo: SkillRepoDep) -> UserProgressResponse:
    """Fetch user progress aggregate."""
    service = ProgressService(progress_repo, skill_repo)
    progress = service.get_user_progress(user_id)
    return UserProgressResponse(progress=progress)


@router.post(
    "/complete",
    summary="Mark lesson completed",
    description="Mark a specific lesson as completed for a user with an optional score.",
    response_model=ProgressEntryResponse,
)
def mark_lesson_complete(
    req: MarkCompleteRequest, progress_repo: ProgressRepoDep, skill_repo: SkillRepoDep
) -> ProgressEntryResponse:
    """Create a completion entry for a lesson."""
    service = ProgressService(progress_repo, skill_repo)
    entry = service.mark_lesson_completed(
        user_id=req.user_id,
        skill_id=req.skill_id,
        module_id=req.module_id,
        lesson_id=req.lesson_id,
        score=req.score,
    )
    return ProgressEntryResponse(entry=entry)


@router.get(
    "/{user_id}/lesson/{lesson_id}",
    summary="Get progress for lesson",
    description="Return all progress entries for a given user and lesson.",
    response_model=List[dict],
)
def get_progress_for_lesson(
    user_id: str, lesson_id: str, progress_repo: ProgressRepoDep, skill_repo: SkillRepoDep
):
    """Return entries for a specific lesson."""
    service = ProgressService(progress_repo, skill_repo)
    entries = service.get_progress_for_lesson(user_id, lesson_id)
    # Return list of dicts to keep response simple; could wrap with schema if needed
    return [e.model_dump() for e in entries]
