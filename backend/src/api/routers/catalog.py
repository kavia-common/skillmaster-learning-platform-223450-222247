"""Catalog routes for skills and lessons stored in MongoDB.

Public GET endpoints:
- GET /content/skills
- GET /content/skills/{slug}
- GET /content/skills/{slug}/lessons
- GET /content/lessons/{slug}

Admin-only endpoints (use JWT stub):
- POST/PUT/DELETE /content/skills
- POST/PUT/DELETE /content/lessons
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.auth import require_admin
from src.db.models import LessonModel, QuizQuestionModel, SkillModel
from src.db.mongo import get_db
from src.repositories.mongo_repository import MongoCatalogRepository

router = APIRouter(prefix="/content", tags=["Skills"])


async def get_repo() -> MongoCatalogRepository:
    db = get_db()
    repo = MongoCatalogRepository(db)
    await repo.ensure_indexes()
    return repo


# PUBLIC_INTERFACE
@router.get(
    "/skills",
    summary="List skills",
    description="List skills with optional category, difficulty, and search filters. Supports pagination.",
)
async def list_skills(
    category: Optional[str] = Query(None, description="Filter by category"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term against name/description/tags"),
    repo: MongoCatalogRepository = Depends(get_repo),
) -> Dict[str, Any]:
    """Return paginated list of skills matching filters."""
    items, total = await repo.list_skills(category, difficulty, page, page_size, search)
    return {"items": items, "total": total, "page": page, "pageSize": page_size}


# PUBLIC_INTERFACE
@router.get(
    "/skills/{slug}",
    summary="Get skill detail",
    description="Return a single skill by slug.",
)
async def get_skill(slug: str, repo: MongoCatalogRepository = Depends(get_repo)) -> Dict[str, Any]:
    """Get a skill by slug."""
    skill = await repo.get_skill_by_slug(slug)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


# PUBLIC_INTERFACE
@router.post(
    "/skills",
    summary="Create skill",
    description="Create a new skill (admin only).",
    dependencies=[Depends(require_admin)],
)
async def create_skill(payload: SkillModel, repo: MongoCatalogRepository = Depends(get_repo)) -> Dict[str, Any]:
    """Create a skill document."""
    now = datetime.utcnow()
    payload.createdAt = now
    payload.updatedAt = now
    created = await repo.create_skill(payload)
    return created


# PUBLIC_INTERFACE
@router.put(
    "/skills/{slug}",
    summary="Update skill",
    description="Update an existing skill by slug (admin only).",
    dependencies=[Depends(require_admin)],
)
async def update_skill(
    slug: str, updates: Dict[str, Any], repo: MongoCatalogRepository = Depends(get_repo)
) -> Dict[str, Any]:
    """Update a skill by slug."""
    updates["updatedAt"] = datetime.utcnow()
    updated = await repo.update_skill(slug, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Skill not found")
    return updated


# PUBLIC_INTERFACE
@router.delete(
    "/skills/{slug}",
    summary="Delete skill",
    description="Delete a skill by slug (admin only).",
    dependencies=[Depends(require_admin)],
)
async def delete_skill(slug: str, repo: MongoCatalogRepository = Depends(get_repo)) -> Dict[str, Any]:
    """Delete a skill and its lessons."""
    ok = await repo.delete_skill(slug)
    if not ok:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"deleted": True}


# PUBLIC_INTERFACE
@router.get(
    "/skills/{slug}/lessons",
    summary="List lessons for a skill",
    description="Return lessons associated with the given skill slug.",
)
async def list_lessons_for_skill(slug: str, repo: MongoCatalogRepository = Depends(get_repo)) -> List[Dict[str, Any]]:
    """List lessons referencing the provided skill slug."""
    lessons = await repo.list_lessons_for_skill(slug)
    return lessons


# PUBLIC_INTERFACE
@router.get(
    "/lessons/{slug}",
    summary="Get lesson detail",
    description="Return a single lesson by slug, including quiz and badge.",
)
async def get_lesson(slug: str, repo: MongoCatalogRepository = Depends(get_repo)) -> Dict[str, Any]:
    """Get lesson by slug."""
    lesson = await repo.get_lesson_by_slug(slug)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


# PUBLIC_INTERFACE
@router.post(
    "/lessons",
    summary="Create lesson",
    description="Create a new lesson (admin only).",
    dependencies=[Depends(require_admin)],
)
async def create_lesson(payload: LessonModel, repo: MongoCatalogRepository = Depends(get_repo)) -> Dict[str, Any]:
    """Create a lesson document; quiz schema validated by Pydantic."""
    payload.createdAt = datetime.utcnow()
    payload.updatedAt = datetime.utcnow()
    created = await repo.create_lesson(payload)
    return created


# PUBLIC_INTERFACE
@router.put(
    "/lessons/{slug}",
    summary="Update lesson",
    description="Update an existing lesson by slug (admin only).",
    dependencies=[Depends(require_admin)],
)
async def update_lesson(
    slug: str, updates: Dict[str, Any], repo: MongoCatalogRepository = Depends(get_repo)
) -> Dict[str, Any]:
    """Update a lesson by slug."""
    # Validate quiz if present
    if "quiz" in updates and updates["quiz"] is not None:
        quiz = updates["quiz"]
        if not isinstance(quiz, list) or len(quiz) != 3:
            raise HTTPException(status_code=400, detail="Quiz must contain exactly 3 questions")
        try:
            for q in quiz:
                QuizQuestionModel(**q)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid quiz payload: {e}")
    updates["updatedAt"] = datetime.utcnow()
    updated = await repo.update_lesson(slug, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return updated


# PUBLIC_INTERFACE
@router.delete(
    "/lessons/{slug}",
    summary="Delete lesson",
    description="Delete a lesson by slug (admin only).",
    dependencies=[Depends(require_admin)],
)
async def delete_lesson(slug: str, repo: MongoCatalogRepository = Depends(get_repo)) -> Dict[str, Any]:
    """Delete a lesson by slug."""
    ok = await repo.delete_lesson(slug)
    if not ok:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return {"deleted": True}
