from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.api.relational_schemas import SkillCreate, SkillRead, ModuleRead
from src.db.relational_models import Skill, Subject, Module

router = APIRouter(tags=["Skills"])


# PUBLIC_INTERFACE
@router.get(
    "/skills",
    summary="List skills",
    description="Retrieve all skills, optionally filtered by subject (topic) and progression level.",
    response_model=List[SkillRead],
)
def list_skills(
    subject_slug: Optional[str] = Query(None, description="Filter by subject slug (topic)"),
    level: Optional[str] = Query(None, description="Filter by progression level: Beginner|Intermediate|Advanced"),
    db: Session = Depends(get_db),
):
    """
    List skills available in the catalog.

    Parameters:
    - subject_slug: Filter skills by parent subject slug
    - level: Filter by progression level (Beginner|Intermediate|Advanced)

    Returns:
    - List of SkillRead
    """
    q = db.query(Skill).filter(Skill.deleted == False)
    if subject_slug:
        subj = db.query(Subject).filter(Subject.slug == subject_slug, Subject.deleted == False).first()
        if not subj:
            return []
        q = q.filter(Skill.subject_id == subj.id)
    if level:
        q = q.filter(Skill.level == level)
    return q.order_by(Skill.created_at.asc()).all()


# PUBLIC_INTERFACE
@router.post(
    "/skills",
    summary="Create skill",
    description="Create a new skill under a subject with a progression level.",
    response_model=SkillRead,
)
def create_skill(payload: SkillCreate, db: Session = Depends(get_db)):
    """
    Create a new skill.

    Validations:
    - Subject must exist and not be deleted.
    - Slug must be unique.
    - One skill per level per subject enforced by DB constraint.
    """
    subject = db.query(Subject).filter(Subject.id == payload.subject_id, Subject.deleted == False).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Ensure unique slug
    existing = db.query(Skill).filter(Skill.slug == payload.slug, Skill.deleted == False).first()
    if existing:
        raise HTTPException(status_code=409, detail="Skill slug already exists")

    skill = Skill(
        subject_id=payload.subject_id,
        name=payload.name,
        slug=payload.slug,
        description=payload.description,
        level=payload.level,
        tags=payload.tags or [],
    )
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


# PUBLIC_INTERFACE
@router.get(
    "/skills/{skill_slug}",
    summary="Get skill detail",
    description="Retrieve a specific skill by slug.",
    response_model=SkillRead,
)
def get_skill(skill_slug: str, db: Session = Depends(get_db)):
    skill = (
        db.query(Skill)
        .filter(Skill.slug == skill_slug, Skill.deleted == False)
        .first()
    )
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


# PUBLIC_INTERFACE
@router.put(
    "/skills/{skill_slug}",
    summary="Update skill",
    description="Update an existing skill by slug.",
    response_model=SkillRead,
)
def update_skill(skill_slug: str, updates: Dict[str, Any], db: Session = Depends(get_db)):
    skill = db.query(Skill).filter(Skill.slug == skill_slug, Skill.deleted == False).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    for k, v in updates.items():
        if k in {"name", "description", "level", "tags"}:
            setattr(skill, k, v)
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


# PUBLIC_INTERFACE
@router.delete(
    "/skills/{skill_slug}",
    summary="Delete skill",
    description="Soft delete a skill by slug.",
)
def delete_skill(skill_slug: str, db: Session = Depends(get_db)):
    skill = db.query(Skill).filter(Skill.slug == skill_slug, Skill.deleted == False).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    skill.deleted = True
    db.add(skill)
    db.commit()
    return {"status": "deleted"}


# PUBLIC_INTERFACE
@router.get(
    "/skills/{skill_slug}/modules",
    summary="List modules for a skill",
    description="Return modules associated with the given skill slug.",
    response_model=List[ModuleRead],
)
def list_modules_for_skill(skill_slug: str, db: Session = Depends(get_db)):
    skill = db.query(Skill).filter(Skill.slug == skill_slug, Skill.deleted == False).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    modules = (
        db.query(Module)
        .filter(Module.skill_id == skill.id, Module.deleted == False)
        .order_by(Module.order_index.asc())
        .all()
    )
    return modules
