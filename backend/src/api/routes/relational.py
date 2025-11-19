"""Relational CRUD API routes for Subjects → Modules → Lessons → Activities/Quiz and Progress.

This module exposes RESTful endpoints powered by SQLAlchemy models defined in
src.db.relational_models and Pydantic schemas in src.api.relational_schemas.

Endpoints:
- Subjects:
  - GET /subjects
  - POST /subjects
  - GET /subjects/{id}
  - PUT /subjects/{id}
  - DELETE /subjects/{id}
  - GET /subjects/{id}/modules

- Modules:
  - GET /modules
  - POST /modules
  - GET /modules/{id}
  - PUT /modules/{id}
  - DELETE /modules/{id}
  - GET /modules/{id}/lessons

- Lessons:
  - GET /lessons
  - POST /lessons
  - GET /lessons/{id}
  - PUT /lessons/{id}
  - DELETE /lessons/{id}
  - GET /lessons/{id}/activities

- Activities (includes quiz as type=quiz):
  - GET /activities
  - POST /activities
  - GET /activities/{id}
  - PUT /activities/{id}
  - DELETE /activities/{id}

- Quizzes (activity type alias):
  - GET /quizzes
  - POST /quizzes
  - GET /quizzes/{id}
  - PUT /quizzes/{id}
  - DELETE /quizzes/{id}

- Progress:
  - GET /progress?user_id=... (list by user with optional filters)
  - POST /progress  (upsert by user_id + (activity|lesson) + status)
  - GET /progress/{id}
  - DELETE /progress/{id}

Query params for list:
- search (applied to title/slug where applicable)
- parent_id (for child entities where relevant)
- page (default 1), page_size (default 20)

All create returns 201; delete returns 204.

Notes:
- This router uses SQLAlchemy sessions from src.db.sqlalchemy and models from src.db.relational_models
- Validation performed using src.api.relational_schemas

Security:
- No hardcoded secrets. Config/use of DB via env var SQLALCHEMY_DATABASE_URL.

"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import selectinload, Session

from src.api.relational_schemas import (
    ActivityCreate,
    ActivityRead,
    LessonCreate,
    LessonRead,
    ModuleCreate,
    ModuleRead,
    ProgressRead,
    SubjectCreate,
    SubjectRead,
)
from src.db.relational_models import Activity, ActivityType, Lesson, Module, Progress, Subject
from src.db.sqlalchemy import db_session_scope

router = APIRouter(tags=["Relational"])

# Utilities


def paginate(query, page: int, page_size: int):
    """Apply pagination to a SQLAlchemy ORM query."""
    offset = (page - 1) * page_size
    return query.offset(offset).limit(page_size)


def like_search(term: Optional[str]) -> Optional[str]:
    """Return SQL LIKE pattern for case-insensitive search."""
    if not term:
        return None
    return f"%{term.strip()}%"


class PaginatedResponse(BaseModel):
    """Generic pagination wrapper."""
    items: List[Any]
    total: int
    page: int
    page_size: int


def to_subject_read(entity: Subject, include_nested: bool = False) -> SubjectRead:
    """Map Subject ORM to SubjectRead Pydantic."""
    modules = []
    if include_nested:
        for m in sorted(entity.modules, key=lambda x: x.order_index):
            modules.append(to_module_read(m, include_nested=True))
    return SubjectRead(
        id=entity.id,
        slug=entity.slug,
        title=entity.title,
        description=entity.description,
        modules=modules,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def to_module_read(entity: Module, include_nested: bool = False) -> ModuleRead:
    """Map Module ORM to ModuleRead Pydantic."""
    lessons = []
    if include_nested:
        for l in sorted(entity.lessons, key=lambda x: x.order_index):
            lessons.append(to_lesson_read(l, include_nested=True))
    return ModuleRead(
        id=entity.id,
        subject_id=entity.subject_id,
        slug=entity.slug,
        title=entity.title,
        description=entity.description,
        order_index=entity.order_index,
        lessons=lessons,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def to_activity_read(entity: Activity) -> ActivityRead:
    """Map Activity ORM to ActivityRead Pydantic."""
    return ActivityRead(
        id=entity.id,
        lesson_id=entity.lesson_id,
        type=entity.type,
        title=entity.title,
        content=entity.content,
        order_index=entity.order_index,
        quiz_questions=entity.quiz_questions,
        quiz_pass_score=entity.quiz_pass_score,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def to_lesson_read(entity: Lesson, include_nested: bool = False) -> LessonRead:
    """Map Lesson ORM to LessonRead Pydantic."""
    activities = []
    if include_nested:
        for a in sorted(entity.activities, key=lambda x: x.order_index):
            activities.append(to_activity_read(a))
    return LessonRead(
        id=entity.id,
        module_id=entity.module_id,
        slug=entity.slug,
        title=entity.title,
        content=entity.content,
        order_index=entity.order_index,
        activities=activities,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def to_progress_read(entity: Progress) -> ProgressRead:
    """Map Progress ORM to ProgressRead Pydantic."""
    return ProgressRead(
        id=entity.id,
        user_id=entity.user_id,
        subject_id=entity.subject_id,
        module_id=entity.module_id,
        lesson_id=entity.lesson_id,
        activity_id=entity.activity_id,
        completed=entity.completed,
        score=entity.score,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


# Subjects

# PUBLIC_INTERFACE
@router.get(
    "/subjects",
    summary="List subjects",
    description="List subjects with pagination and optional search by slug/title.",
)
def list_subjects(
    search: Optional[str] = Query(None, description="Search in slug/title"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> Dict[str, Any]:
    """List subjects with pagination and simple search."""
    pattern = like_search(search)
    with db_session_scope() as session:
        base_q = session.query(Subject).filter(Subject.is_deleted == False)  # noqa: E712
        if pattern:
            base_q = base_q.filter(or_(Subject.slug.ilike(pattern), Subject.title.ilike(pattern)))
        total = base_q.count()
        records = paginate(
            base_q.order_by(Subject.title.asc()), page=page, page_size=page_size
        ).all()
        items = [to_subject_read(s) for s in records]
        return {"items": items, "total": total, "page": page, "page_size": page_size}


# PUBLIC_INTERFACE
@router.post(
    "/subjects",
    status_code=status.HTTP_201_CREATED,
    summary="Create subject",
    description="Create a new subject.",
)
def create_subject(payload: SubjectCreate) -> SubjectRead:
    """Create a subject."""
    with db_session_scope() as session:
        # Uniqueness on slug enforced at DB, but check early for friendlier error
        existing = session.query(Subject).filter(Subject.slug == payload.slug).first()
        if existing:
            raise HTTPException(status_code=409, detail="Subject slug already exists")
        entity = Subject(slug=payload.slug, title=payload.title, description=payload.description)
        session.add(entity)
        session.flush()
        session.refresh(entity)
        return to_subject_read(entity)


# PUBLIC_INTERFACE
@router.get(
    "/subjects/{subject_id}",
    summary="Get subject",
    description="Get a subject by id including nested modules if include_nested=true.",
)
def get_subject(
    subject_id: int, include_nested: bool = Query(False, description="Include modules tree")
) -> SubjectRead:
    """Get subject by id."""
    with db_session_scope() as session:
        q = session.query(Subject)
        if include_nested:
            q = q.options(selectinload(Subject.modules).selectinload(Module.lessons))
        entity = q.filter(Subject.id == subject_id, Subject.is_deleted == False).first()  # noqa: E712
        if not entity:
            raise HTTPException(status_code=404, detail="Subject not found")
        return to_subject_read(entity, include_nested=include_nested)


# PUBLIC_INTERFACE
@router.put(
    "/subjects/{subject_id}",
    summary="Update subject",
    description="Update subject fields.",
)
def update_subject(subject_id: int, updates: Dict[str, Any]) -> SubjectRead:
    """Update subject."""
    allowed = {"slug", "title", "description"}
    cleaned = {k: v for k, v in updates.items() if k in allowed}
    if not cleaned:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    with db_session_scope() as session:
        entity = session.get(Subject, subject_id)
        if not entity or entity.is_deleted:
            raise HTTPException(status_code=404, detail="Subject not found")
        if "slug" in cleaned:
            conflict = (
                session.query(Subject)
                .filter(Subject.slug == cleaned["slug"], Subject.id != subject_id)
                .first()
            )
            if conflict:
                raise HTTPException(status_code=409, detail="Slug already in use")
        for k, v in cleaned.items():
            setattr(entity, k, v)
        session.flush()
        session.refresh(entity)
        return to_subject_read(entity)


# PUBLIC_INTERFACE
@router.delete(
    "/subjects/{subject_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete subject",
    description="Soft delete the subject (and cascade via FK set to CASCADE on children).",
)
def delete_subject(subject_id: int) -> None:
    """Soft delete subject."""
    with db_session_scope() as session:
        entity = session.get(Subject, subject_id)
        if not entity or entity.is_deleted:
            raise HTTPException(status_code=404, detail="Subject not found")
        entity.is_deleted = True
        session.flush()
        return None


# PUBLIC_INTERFACE
@router.get(
    "/subjects/{subject_id}/modules",
    summary="List modules by subject",
    description="List modules for a subject with pagination and search.",
)
def list_modules_for_subject(
    subject_id: int,
    search: Optional[str] = Query(None, description="Search in slug/title"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Dict[str, Any]:
    """List modules for a subject."""
    pattern = like_search(search)
    with db_session_scope() as session:
        base_q = session.query(Module).filter(
            Module.subject_id == subject_id, Module.is_deleted == False  # noqa: E712
        )
        if pattern:
            base_q = base_q.filter(or_(Module.slug.ilike(pattern), Module.title.ilike(pattern)))
        total = base_q.count()
        records = paginate(base_q.order_by(Module.order_index.asc()), page, page_size).all()
        items = [to_module_read(m) for m in records]
        return {"items": items, "total": total, "page": page, "page_size": page_size}


# Modules

# PUBLIC_INTERFACE
@router.get(
    "/modules",
    summary="List modules",
    description="List modules with optional subject filter and search.",
)
def list_modules(
    subject_id: Optional[int] = Query(None, description="Filter by subject id"),
    search: Optional[str] = Query(None, description="Search in slug/title"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Dict[str, Any]:
    """List modules."""
    pattern = like_search(search)
    with db_session_scope() as session:
        base_q = session.query(Module).filter(Module.is_deleted == False)  # noqa: E712
        if subject_id is not None:
            base_q = base_q.filter(Module.subject_id == subject_id)
        if pattern:
            base_q = base_q.filter(or_(Module.slug.ilike(pattern), Module.title.ilike(pattern)))
        total = base_q.count()
        records = paginate(base_q.order_by(Module.order_index.asc()), page, page_size).all()
        items = [to_module_read(m) for m in records]
        return {"items": items, "total": total, "page": page, "page_size": page_size}


# PUBLIC_INTERFACE
@router.post(
    "/modules",
    status_code=status.HTTP_201_CREATED,
    summary="Create module",
    description="Create a new module under a subject.",
)
def create_module(payload: ModuleCreate) -> ModuleRead:
    """Create a module."""
    with db_session_scope() as session:
        parent = session.get(Subject, payload.subject_id)
        if not parent or parent.is_deleted:
            raise HTTPException(status_code=400, detail="Invalid subject_id")
        # Unique per subject_id + slug
        conflict = (
            session.query(Module)
            .filter(Module.subject_id == payload.subject_id, Module.slug == payload.slug)
            .first()
        )
        if conflict:
            raise HTTPException(status_code=409, detail="Module slug already exists for subject")
        entity = Module(
            subject_id=payload.subject_id,
            slug=payload.slug,
            title=payload.title,
            description=payload.description,
            order_index=payload.order_index,
        )
        session.add(entity)
        session.flush()
        session.refresh(entity)
        return to_module_read(entity)


# PUBLIC_INTERFACE
@router.get(
    "/modules/{module_id}",
    summary="Get module",
    description="Get module by id. Include nested lessons if include_nested=true.",
)
def get_module(
    module_id: int, include_nested: bool = Query(False, description="Include lessons tree")
) -> ModuleRead:
    """Get module by id."""
    with db_session_scope() as session:
        q = session.query(Module)
        if include_nested:
            q = q.options(selectinload(Module.lessons).selectinload(Lesson.activities))
        entity = q.filter(Module.id == module_id, Module.is_deleted == False).first()  # noqa: E712
        if not entity:
            raise HTTPException(status_code=404, detail="Module not found")
        return to_module_read(entity, include_nested=include_nested)


# PUBLIC_INTERFACE
@router.put(
    "/modules/{module_id}",
    summary="Update module",
    description="Update fields of a module.",
)
def update_module(module_id: int, updates: Dict[str, Any]) -> ModuleRead:
    """Update module."""
    allowed = {"slug", "title", "description", "order_index", "subject_id"}
    cleaned = {k: v for k, v in updates.items() if k in allowed}
    if not cleaned:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    with db_session_scope() as session:
        entity = session.get(Module, module_id)
        if not entity or entity.is_deleted:
            raise HTTPException(status_code=404, detail="Module not found")
        if "subject_id" in cleaned:
            parent = session.get(Subject, cleaned["subject_id"])
            if not parent or parent.is_deleted:
                raise HTTPException(status_code=400, detail="Invalid subject_id")
        if "slug" in cleaned:
            conflict = (
                session.query(Module)
                .filter(
                    Module.subject_id == cleaned.get("subject_id", entity.subject_id),
                    Module.slug == cleaned["slug"],
                    Module.id != module_id,
                )
                .first()
            )
            if conflict:
                raise HTTPException(status_code=409, detail="Slug already in use for subject")
        for k, v in cleaned.items():
            setattr(entity, k, v)
        session.flush()
        session.refresh(entity)
        return to_module_read(entity)


# PUBLIC_INTERFACE
@router.delete(
    "/modules/{module_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete module",
    description="Soft delete module.",
)
def delete_module(module_id: int) -> None:
    """Soft delete module."""
    with db_session_scope() as session:
        entity = session.get(Module, module_id)
        if not entity or entity.is_deleted:
            raise HTTPException(status_code=404, detail="Module not found")
        entity.is_deleted = True
        session.flush()
        return None


# PUBLIC_INTERFACE
@router.get(
    "/modules/{module_id}/lessons",
    summary="List lessons by module",
    description="List lessons for a module with pagination and search.",
)
def list_lessons_for_module(
    module_id: int,
    search: Optional[str] = Query(None, description="Search in slug/title"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Dict[str, Any]:
    """List lessons for a module."""
    pattern = like_search(search)
    with db_session_scope() as session:
        base_q = session.query(Lesson).filter(
            Lesson.module_id == module_id, Lesson.is_deleted == False  # noqa: E712
        )
        if pattern:
            base_q = base_q.filter(or_(Lesson.slug.ilike(pattern), Lesson.title.ilike(pattern)))
        total = base_q.count()
        records = paginate(base_q.order_by(Lesson.order_index.asc()), page, page_size).all()
        items = [to_lesson_read(l) for l in records]
        return {"items": items, "total": total, "page": page, "page_size": page_size}


# Lessons

# PUBLIC_INTERFACE
@router.get(
    "/lessons",
    summary="List lessons",
    description="List lessons with optional module filter and search.",
)
def list_lessons(
    module_id: Optional[int] = Query(None, description="Filter by module id"),
    search: Optional[str] = Query(None, description="Search in slug/title"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Dict[str, Any]:
    """List lessons."""
    pattern = like_search(search)
    with db_session_scope() as session:
        base_q = session.query(Lesson).filter(Lesson.is_deleted == False)  # noqa: E712
        if module_id is not None:
            base_q = base_q.filter(Lesson.module_id == module_id)
        if pattern:
            base_q = base_q.filter(or_(Lesson.slug.ilike(pattern), Lesson.title.ilike(pattern)))
        total = base_q.count()
        records = paginate(base_q.order_by(Lesson.order_index.asc()), page, page_size).all()
        items = [to_lesson_read(l) for l in records]
        return {"items": items, "total": total, "page": page, "page_size": page_size}


# PUBLIC_INTERFACE
@router.post(
    "/lessons",
    status_code=status.HTTP_201_CREATED,
    summary="Create lesson",
    description="Create a new lesson in a module.",
)
def create_lesson(payload: LessonCreate) -> LessonRead:
    """Create lesson."""
    with db_session_scope() as session:
        parent = session.get(Module, payload.module_id)
        if not parent or parent.is_deleted:
            raise HTTPException(status_code=400, detail="Invalid module_id")
        conflict = (
            session.query(Lesson)
            .filter(Lesson.module_id == payload.module_id, Lesson.slug == payload.slug)
            .first()
        )
        if conflict:
            raise HTTPException(status_code=409, detail="Lesson slug already exists for module")
        entity = Lesson(
            module_id=payload.module_id,
            slug=payload.slug,
            title=payload.title,
            content=payload.content,
            order_index=payload.order_index,
        )
        session.add(entity)
        session.flush()
        session.refresh(entity)
        return to_lesson_read(entity)


# PUBLIC_INTERFACE
@router.get(
    "/lessons/{lesson_id}",
    summary="Get lesson",
    description="Get a lesson by id. Include nested activities if include_nested=true.",
)
def get_lesson(
    lesson_id: int, include_nested: bool = Query(False, description="Include activities")
) -> LessonRead:
    """Get lesson."""
    with db_session_scope() as session:
        q = session.query(Lesson)
        if include_nested:
            q = q.options(selectinload(Lesson.activities))
        entity = q.filter(Lesson.id == lesson_id, Lesson.is_deleted == False).first()  # noqa: E712
        if not entity:
            raise HTTPException(status_code=404, detail="Lesson not found")
        return to_lesson_read(entity, include_nested=include_nested)


# PUBLIC_INTERFACE
@router.put(
    "/lessons/{lesson_id}",
    summary="Update lesson",
    description="Update fields of a lesson.",
)
def update_lesson(lesson_id: int, updates: Dict[str, Any]) -> LessonRead:
    """Update lesson."""
    allowed = {"slug", "title", "content", "order_index", "module_id"}
    cleaned = {k: v for k, v in updates.items() if k in allowed}
    if not cleaned:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    with db_session_scope() as session:
        entity = session.get(Lesson, lesson_id)
        if not entity or entity.is_deleted:
            raise HTTPException(status_code=404, detail="Lesson not found")
        if "module_id" in cleaned:
            parent = session.get(Module, cleaned["module_id"])
            if not parent or parent.is_deleted:
                raise HTTPException(status_code=400, detail="Invalid module_id")
        if "slug" in cleaned:
            conflict = (
                session.query(Lesson)
                .filter(
                    Lesson.module_id == cleaned.get("module_id", entity.module_id),
                    Lesson.slug == cleaned["slug"],
                    Lesson.id != lesson_id,
                )
                .first()
            )
            if conflict:
                raise HTTPException(status_code=409, detail="Slug already in use for module")
        for k, v in cleaned.items():
            setattr(entity, k, v)
        session.flush()
        session.refresh(entity)
        return to_lesson_read(entity)


# PUBLIC_INTERFACE
@router.delete(
    "/lessons/{lesson_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete lesson",
    description="Soft delete lesson.",
)
def delete_lesson(lesson_id: int) -> None:
    """Soft delete lesson."""
    with db_session_scope() as session:
        entity = session.get(Lesson, lesson_id)
        if not entity or entity.is_deleted:
            raise HTTPException(status_code=404, detail="Lesson not found")
        entity.is_deleted = True
        session.flush()
        return None


# PUBLIC_INTERFACE
@router.get(
    "/lessons/{lesson_id}/activities",
    summary="List activities for a lesson",
    description="List activities for a lesson with pagination.",
)
def list_activities_for_lesson(
    lesson_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Dict[str, Any]:
    """List activities for a lesson."""
    with db_session_scope() as session:
        base_q = session.query(Activity).filter(
            Activity.lesson_id == lesson_id, Activity.is_deleted == False  # noqa: E712
        )
        total = base_q.count()
        records = paginate(base_q.order_by(Activity.order_index.asc()), page, page_size).all()
        items = [to_activity_read(a) for a in records]
        return {"items": items, "total": total, "page": page, "page_size": page_size}


# Activities

# PUBLIC_INTERFACE
@router.get(
    "/activities",
    summary="List activities",
    description="List activities with optional lesson_id filter and type ('content'|'quiz').",
)
def list_activities(
    lesson_id: Optional[int] = Query(None, description="Filter by lesson id"),
    type: Optional[str] = Query(None, description="Filter by type: content|quiz"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Dict[str, Any]:
    """List activities."""
    with db_session_scope() as session:
        base_q = session.query(Activity).filter(Activity.is_deleted == False)  # noqa: E712
        if lesson_id is not None:
            base_q = base_q.filter(Activity.lesson_id == lesson_id)
        if type is not None:
            if type not in (ActivityType.CONTENT, ActivityType.QUIZ):
                raise HTTPException(status_code=400, detail="Invalid type filter")
            base_q = base_q.filter(Activity.type == type)
        total = base_q.count()
        records = paginate(base_q.order_by(Activity.order_index.asc()), page, page_size).all()
        items = [to_activity_read(a) for a in records]
        return {"items": items, "total": total, "page": page, "page_size": page_size}


# PUBLIC_INTERFACE
@router.post(
    "/activities",
    status_code=status.HTTP_201_CREATED,
    summary="Create activity",
    description="Create an activity of type content or quiz. For quiz, provide quiz_questions and optional quiz_pass_score.",
)
def create_activity(payload: ActivityCreate) -> ActivityRead:
    """Create an activity."""
    with db_session_scope() as session:
        parent = session.get(Lesson, payload.lesson_id)
        if not parent or parent.is_deleted:
            raise HTTPException(status_code=400, detail="Invalid lesson_id")
        entity = Activity(
            lesson_id=payload.lesson_id,
            type=payload.type,
            title=payload.title,
            content=payload.content,
            order_index=payload.order_index,
            quiz_questions=payload.quiz_questions,
            quiz_pass_score=payload.quiz_pass_score,
        )
        session.add(entity)
        session.flush()
        session.refresh(entity)
        return to_activity_read(entity)


# PUBLIC_INTERFACE
@router.get(
    "/activities/{activity_id}",
    summary="Get activity",
    description="Get activity by id.",
)
def get_activity(activity_id: int) -> ActivityRead:
    """Get activity."""
    with db_session_scope() as session:
        entity = session.get(Activity, activity_id)
        if not entity or entity.is_deleted:
            raise HTTPException(status_code=404, detail="Activity not found")
        return to_activity_read(entity)


# PUBLIC_INTERFACE
@router.put(
    "/activities/{activity_id}",
    summary="Update activity",
    description="Update activity fields.",
)
def update_activity(activity_id: int, updates: Dict[str, Any]) -> ActivityRead:
    """Update activity."""
    allowed = {"lesson_id", "type", "title", "content", "order_index", "quiz_questions", "quiz_pass_score"}
    cleaned = {k: v for k, v in updates.items() if k in allowed}
    if not cleaned:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    with db_session_scope() as session:
        entity = session.get(Activity, activity_id)
        if not entity or entity.is_deleted:
            raise HTTPException(status_code=404, detail="Activity not found")
        if "lesson_id" in cleaned:
            parent = session.get(Lesson, cleaned["lesson_id"])
            if not parent or parent.is_deleted:
                raise HTTPException(status_code=400, detail="Invalid lesson_id")
        if "type" in cleaned and cleaned["type"] not in (ActivityType.CONTENT, ActivityType.QUIZ):
            raise HTTPException(status_code=400, detail="Invalid type")
        for k, v in cleaned.items():
            setattr(entity, k, v)
        session.flush()
        session.refresh(entity)
        return to_activity_read(entity)


# PUBLIC_INTERFACE
@router.delete(
    "/activities/{activity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete activity",
    description="Soft delete activity.",
)
def delete_activity(activity_id: int) -> None:
    """Soft delete activity."""
    with db_session_scope() as session:
        entity = session.get(Activity, activity_id)
        if not entity or entity.is_deleted:
            raise HTTPException(status_code=404, detail="Activity not found")
        entity.is_deleted = True
        session.flush()
        return None


# Quizzes (alias on activities with type='quiz')

# PUBLIC_INTERFACE
@router.get(
    "/quizzes",
    summary="List quizzes",
    description="List quiz activities (type=quiz) with optional lesson filter.",
)
def list_quizzes(
    lesson_id: Optional[int] = Query(None, description="Filter by lesson id"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Dict[str, Any]:
    """List quizzes."""
    return list_activities(lesson_id=lesson_id, type=ActivityType.QUIZ, page=page, page_size=page_size)


# PUBLIC_INTERFACE
@router.post(
    "/quizzes",
    status_code=status.HTTP_201_CREATED,
    summary="Create quiz",
    description="Create a quiz activity (type=quiz).",
)
def create_quiz(payload: ActivityCreate) -> ActivityRead:
    """Create quiz (forces type=quiz)."""
    payload = ActivityCreate(
        lesson_id=payload.lesson_id,
        type=ActivityType.QUIZ,
        title=payload.title,
        content=payload.content,
        order_index=payload.order_index,
        quiz_questions=payload.quiz_questions,
        quiz_pass_score=payload.quiz_pass_score,
    )
    return create_activity(payload)


# PUBLIC_INTERFACE
@router.get(
    "/quizzes/{quiz_id}",
    summary="Get quiz",
    description="Get quiz by id.",
)
def get_quiz(quiz_id: int) -> ActivityRead:
    """Get quiz activity, validating type."""
    with db_session_scope() as session:
        entity = session.get(Activity, quiz_id)
        if not entity or entity.is_deleted or entity.type != ActivityType.QUIZ:
            raise HTTPException(status_code=404, detail="Quiz not found")
        return to_activity_read(entity)


# PUBLIC_INTERFACE
@router.put(
    "/quizzes/{quiz_id}",
    summary="Update quiz",
    description="Update a quiz activity fields.",
)
def update_quiz(quiz_id: int, updates: Dict[str, Any]) -> ActivityRead:
    """Update quiz activity."""
    updates = dict(updates or {})
    updates["type"] = ActivityType.QUIZ
    return update_activity(quiz_id, updates)


# PUBLIC_INTERFACE
@router.delete(
    "/quizzes/{quiz_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete quiz",
    description="Soft delete quiz activity.",
)
def delete_quiz(quiz_id: int) -> None:
    """Delete quiz activity."""
    return delete_activity(quiz_id)


# Progress

class ProgressUpsertPayload(BaseModel):
    """Payload for progress upsert.

    entity_type: one of 'subject' | 'module' | 'lesson' | 'activity'
    entity_id: numeric id of the entity
    status: 'completed' or 'in_progress'
    score: optional number 0..100 (primarily for quiz/activity/lesson)
    completed_at: optional datetime in ISO format
    """
    user_id: str = Field(..., description="User id")
    entity_type: str = Field(..., description="subject|module|lesson|activity")
    entity_id: int = Field(..., description="Entity id")
    status: str = Field(..., description="completed|in_progress")
    score: Optional[float] = Field(None, ge=0, le=100)
    completed_at: Optional[datetime] = None


def _resolve_progress_targets(payload: ProgressUpsertPayload) -> Dict[str, Optional[int]]:
    """Map entity_type/entity_id into progress foreign keys."""
    m: Dict[str, Optional[int]] = {"subject_id": None, "module_id": None, "lesson_id": None, "activity_id": None}
    if payload.entity_type == "subject":
        m["subject_id"] = payload.entity_id
    elif payload.entity_type == "module":
        m["module_id"] = payload.entity_id
    elif payload.entity_type == "lesson":
        m["lesson_id"] = payload.entity_id
    elif payload.entity_type == "activity":
        m["activity_id"] = payload.entity_id
    else:
        raise HTTPException(status_code=400, detail="Invalid entity_type")
    return m


def _validate_references(session: Session, refs: Dict[str, Optional[int]]) -> None:
    """Ensure referenced ids exist."""
    if refs["subject_id"] is not None and not session.get(Subject, refs["subject_id"]):
        raise HTTPException(status_code=400, detail="Invalid subject_id")
    if refs["module_id"] is not None and not session.get(Module, refs["module_id"]):
        raise HTTPException(status_code=400, detail="Invalid module_id")
    if refs["lesson_id"] is not None and not session.get(Lesson, refs["lesson_id"]):
        raise HTTPException(status_code=400, detail="Invalid lesson_id")
    if refs["activity_id"] is not None and not session.get(Activity, refs["activity_id"]):
        raise HTTPException(status_code=400, detail="Invalid activity_id")


# PUBLIC_INTERFACE
@router.get(
    "/progress",
    summary="List progress",
    description="List progress entries for a user with optional filters and pagination.",
)
def list_progress(
    user_id: str = Query(..., description="User id"),
    subject_id: Optional[int] = Query(None),
    module_id: Optional[int] = Query(None),
    lesson_id: Optional[int] = Query(None),
    activity_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Dict[str, Any]:
    """List progress entries."""
    with db_session_scope() as session:
        base_q = session.query(Progress).filter(Progress.user_id == user_id, Progress.is_deleted == False)  # noqa: E712
        if subject_id is not None:
            base_q = base_q.filter(Progress.subject_id == subject_id)
        if module_id is not None:
            base_q = base_q.filter(Progress.module_id == module_id)
        if lesson_id is not None:
            base_q = base_q.filter(Progress.lesson_id == lesson_id)
        if activity_id is not None:
            base_q = base_q.filter(Progress.activity_id == activity_id)
        total = base_q.count()
        records = paginate(base_q.order_by(Progress.updated_at.desc()), page, page_size).all()
        items = [to_progress_read(p) for p in records]
        return {"items": items, "total": total, "page": page, "page_size": page_size}


# PUBLIC_INTERFACE
@router.post(
    "/progress",
    status_code=status.HTTP_201_CREATED,
    summary="Upsert progress",
    description="Create or update a progress entry for a user and entity.",
)
def upsert_progress(payload: ProgressUpsertPayload) -> ProgressRead:
    """Create a new progress record or update latest matching one."""
    if payload.status not in ("completed", "in_progress"):
        raise HTTPException(status_code=400, detail="Invalid status")
    completed = payload.status == "completed"

    with db_session_scope() as session:
        refs = _resolve_progress_targets(payload)
        _validate_references(session, refs)

        # heuristic: update most recent record for same keys, else insert
        q = session.query(Progress).filter(
            Progress.user_id == payload.user_id,
            Progress.subject_id.is_(refs["subject_id"]) if refs["subject_id"] is None else Progress.subject_id == refs["subject_id"],  # type: ignore
            Progress.module_id.is_(refs["module_id"]) if refs["module_id"] is None else Progress.module_id == refs["module_id"],  # type: ignore
            Progress.lesson_id.is_(refs["lesson_id"]) if refs["lesson_id"] is None else Progress.lesson_id == refs["lesson_id"],  # type: ignore
            Progress.activity_id.is_(refs["activity_id"]) if refs["activity_id"] is None else Progress.activity_id == refs["activity_id"],  # type: ignore
            Progress.is_deleted == False,  # noqa: E712
        ).order_by(Progress.updated_at.desc())

        existing = q.first()
        if existing:
            existing.completed = completed
            existing.score = payload.score
            session.flush()
            session.refresh(existing)
            return to_progress_read(existing)

        entity = Progress(
            user_id=payload.user_id,
            subject_id=refs["subject_id"],
            module_id=refs["module_id"],
            lesson_id=refs["lesson_id"],
            activity_id=refs["activity_id"],
            completed=completed,
            score=payload.score,
        )
        session.add(entity)
        session.flush()
        session.refresh(entity)
        return to_progress_read(entity)


# PUBLIC_INTERFACE
@router.get(
    "/progress/{progress_id}",
    summary="Get progress by id",
    description="Return a single progress entry.",
)
def get_progress(progress_id: int) -> ProgressRead:
    """Get progress record by id."""
    with db_session_scope() as session:
        entity = session.get(Progress, progress_id)
        if not entity or entity.is_deleted:
            raise HTTPException(status_code=404, detail="Progress not found")
        return to_progress_read(entity)


# PUBLIC_INTERFACE
@router.delete(
    "/progress/{progress_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete progress",
    description="Soft delete a progress record.",
)
def delete_progress(progress_id: int) -> None:
    """Soft delete progress record."""
    with db_session_scope() as session:
        entity = session.get(Progress, progress_id)
        if not entity or entity.is_deleted:
            raise HTTPException(status_code=404, detail="Progress not found")
        entity.is_deleted = True
        session.flush()
        return None
