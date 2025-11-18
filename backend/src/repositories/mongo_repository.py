"""Mongo repository implementation for skills and lessons with pagination and filtering."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from bson import ObjectId  # type: ignore
from pymongo import ASCENDING
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.db.models import LessonModel, SkillModel


def _str_id(v: Any) -> Optional[str]:
    """Helper to convert ObjectId or any truthy value to string id."""
    if v is None:
        return None
    if isinstance(v, ObjectId):
        return str(v)
    try:
        return str(v)
    except Exception:
        return None


class MongoCatalogRepository:
    """Provides CRUD operations for skills and lessons in MongoDB."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._db = db
        self._skills: Collection = db["skills"]
        self._lessons: Collection = db["lessons"]

    async def ensure_indexes(self) -> None:
        await self._skills.create_index([("slug", ASCENDING)], unique=True, name="skill_slug_unique")
        await self._skills.create_index([("category", ASCENDING), ("slug", ASCENDING)], name="skill_category_slug")
        await self._lessons.create_index([("slug", ASCENDING)], unique=True, name="lesson_slug_unique")
        await self._lessons.create_index([("skillSlug", ASCENDING)], name="lesson_skill_slug")
        await self._lessons.create_index([("category", ASCENDING)], name="lesson_category")

    async def list_skills(
        self,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        query: Dict[str, Any] = {}
        if category:
            query["category"] = category
        if difficulty:
            query["difficulty"] = difficulty
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}},
                {"tags": {"$regex": search, "$options": "i"}},
            ]
        total = await self._skills.count_documents(query)
        cursor = (
            self._skills.find(query)
            .sort("name", ASCENDING)
            .skip(max(0, (page - 1) * page_size))
            .limit(page_size)
        )
        results = [self._serialize_skill(doc) async for doc in cursor]
        return results, total

    async def get_skill_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        doc = await self._skills.find_one({"slug": slug})
        return self._serialize_skill(doc) if doc else None

    async def create_skill(self, skill: SkillModel) -> Dict[str, Any]:
        # Use dict excluding the alias/id so Mongo can assign ObjectId
        skill_dict = skill.model_dump(exclude_none=True, by_alias=True)
        skill_dict.pop("_id", None)
        try:
            res = await self._skills.insert_one(skill_dict)
        except DuplicateKeyError as e:
            raise ValueError(f"Skill slug '{skill.slug}' already exists") from e
        # Build response with id as string
        skill_dict["_id"] = _str_id(res.inserted_id)
        return self._serialize_skill(skill_dict)

    async def update_skill(self, slug: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        updates = dict(updates or {})
        updates.pop("_id", None)
        updates.pop("id", None)
        doc = await self._skills.find_one_and_update({"slug": slug}, {"$set": updates}, return_document=True)
        return self._serialize_skill(doc) if doc else None

    async def delete_skill(self, slug: str) -> bool:
        res = await self._skills.delete_one({"slug": slug})
        # Also optional cascade delete lessons for the skill
        await self._lessons.delete_many({"skillSlug": slug})
        return res.deleted_count > 0

    async def list_lessons_for_skill(self, skill_slug: str) -> List[Dict[str, Any]]:
        cursor = self._lessons.find({"skillSlug": skill_slug}).sort("title", ASCENDING)
        return [self._serialize_lesson(doc) async for doc in cursor]

    async def get_lesson_by_slug(self, lesson_slug: str) -> Optional[Dict[str, Any]]:
        doc = await self._lessons.find_one({"slug": lesson_slug})
        return self._serialize_lesson(doc) if doc else None

    async def create_lesson(self, lesson: LessonModel) -> Dict[str, Any]:
        lesson_dict = lesson.model_dump(exclude_none=True, by_alias=True)
        lesson_dict.pop("_id", None)
        try:
            res = await self._lessons.insert_one(lesson_dict)
        except DuplicateKeyError as e:
            raise ValueError(f"Lesson slug '{lesson.slug}' already exists") from e
        lesson_dict["_id"] = _str_id(res.inserted_id)
        return self._serialize_lesson(lesson_dict)

    async def update_lesson(self, slug: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        updates = dict(updates or {})
        updates.pop("_id", None)
        updates.pop("id", None)
        doc = await self._lessons.find_one_and_update({"slug": slug}, {"$set": updates}, return_document=True)
        return self._serialize_lesson(doc) if doc else None

    async def delete_lesson(self, slug: str) -> bool:
        res = await self._lessons.delete_one({"slug": slug})
        return res.deleted_count > 0

    def _serialize_skill(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        if not doc:
            return doc
        result = dict(doc)
        if "_id" in result:
            # Also expose "id" for consumer convenience
            result["_id"] = _str_id(result["_id"])
            result["id"] = result["_id"]
        return result

    def _serialize_lesson(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        if not doc:
            return doc
        result = dict(doc)
        if "_id" in result:
            result["_id"] = _str_id(result["_id"])
            result["id"] = result["_id"]
        return result
