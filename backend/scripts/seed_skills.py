"""Seed script to insert initial categories, skills, lessons, quizzes and badges.

Usage:
    python scripts/seed_skills.py

Requirements:
    - Set MONGODB_URI in environment (see .env.example)
    - Script is idempotent (upsert by slug)
"""

from __future__ import annotations

import asyncio
import re
from datetime import datetime
from typing import Dict, List, Tuple

from motor.motor_asyncio import AsyncIOMotorClient


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9\s\-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-{2,}", "-", text)
    return text.strip("-")


def build_quiz(topic: str) -> List[Dict]:
    # Simple generic quiz for the topic
    return [
        {
            "question": f"What is a key concept in {topic}?",
            "options": [f"{topic} basics", "Unrelated topic", "Random guess", "None"],
            "answerIndex": 0,
        },
        {
            "question": f"Which option best applies to {topic}?",
            "options": ["Ignore it", f"Practice {topic}", "Avoid learning", "Skip"],
            "answerIndex": 1,
        },
        {
            "question": f"How do you improve at {topic}?",
            "options": ["Never practice", "Only read once", "Practice and review", "Give up"],
            "answerIndex": 2,
        },
    ]


def build_lesson_content(skill_name: str, summary: str) -> Tuple[str, str]:
    title = f"{skill_name} - Intro Lesson"
    content = f"""# {skill_name}

{summary}

## What you'll learn
- Key concepts and quick wins
- Hands-on examples
- A short quiz to reinforce learning

> Keep practicing to master {skill_name}!
"""
    return title, content


SEED_DATA = {
    "Digital Skills": [
        ("Excel Basics", "Learn SUM, AVERAGE, and IF formulas"),
        ("Intro to HTML", "Build a simple web page with headings and links"),
        ("Keyboard Shortcuts", "Master 10 time-saving shortcuts for Windows"),
    ],
    "Communication Skills": [
        ("Email Etiquette", "Write clear, professional emails"),
        ("Active Listening", "Practice techniques to improve focus and empathy"),
        ("Giving Feedback", "Learn how to be constructive and respectful"),
    ],
    "Soft Skills": [
        ("Time Management", "Use the Pomodoro technique effectively"),
        ("Problem Solving", "Apply the 5 Whys method"),
        ("Teamwork Tips", "Collaborate better in group projects"),
    ],
    "Coding Skills": [
        ("Python Loops", "Write for and while loops with examples"),
        ("Git Commands", "Learn git init, add, commit, and push"),
        ("APIs 101", "Understand how REST APIs work with simple examples"),
    ],
    "Design & Branding": [
        ("Color Theory Basics", "Choose harmonious color palettes"),
        ("Canva for Beginners", "Create a social media post"),
        ("Typography Tips", "Pick fonts that improve readability"),
    ],
    "Career Skills": [
        ("Resume Writing", "Craft a strong summary and bullet points"),
        ("Interview Prep", "Answer common behavioral questions"),
        ("LinkedIn Optimization", "Improve your headline and profile summary"),
    ],
}


async def seed():
    import os

    uri = os.getenv("MONGODB_URI")
    if not uri:
        print("ERROR: MONGODB_URI is not set. Set it in .env or environment and re-run.")
        return

    client = AsyncIOMotorClient(uri)
    db = client["skillmaster"]
    skills = db["skills"]
    lessons = db["lessons"]

    # Indexes
    await skills.create_index("slug", unique=True)
    await skills.create_index([("category", 1), ("slug", 1)])
    await lessons.create_index("slug", unique=True)
    await lessons.create_index("skillSlug")
    await lessons.create_index("category")

    inserted_skills = 0
    inserted_lessons = 0
    updated_skills = 0
    updated_lessons = 0

    for category, entries in SEED_DATA.items():
        for (skill_name, short_desc) in entries:
            skill_slug = slugify(skill_name)
            skill_doc = {
                "name": skill_name,
                "slug": skill_slug,
                "category": category,
                "description": short_desc,
                "tags": [slugify(category), slugify(skill_name)],
                "difficulty": "Beginner",
                "updatedAt": datetime.utcnow(),
            }

            # Upsert skill
            res = await skills.update_one({"slug": skill_slug}, {"$setOnInsert": {"createdAt": datetime.utcnow()}, "$set": skill_doc}, upsert=True)
            if res.matched_count == 0 and res.upserted_id is not None:
                inserted_skills += 1
            else:
                updated_skills += 1

            # Build one lesson per skill
            lesson_slug = f"{skill_slug}-intro"
            title, content = build_lesson_content(skill_name, short_desc)
            lesson_doc = {
                "title": title,
                "slug": lesson_slug,
                "summary": short_desc,
                "content": content,
                "media": "https://example.com/sample-media.jpg",
                "tags": [slugify(category), slugify(skill_name)],
                "difficulty": "Beginner",
                "quiz": build_quiz(skill_name),
                "badge": {"name": f"{skill_name} Starter", "points": 10},
                "skillSlug": skill_slug,
                "category": category,
                "updatedAt": datetime.utcnow(),
            }

            res_lesson = await lessons.update_one(
                {"slug": lesson_slug},
                {"$setOnInsert": {"createdAt": datetime.utcnow()}, "$set": lesson_doc},
                upsert=True,
            )
            if res_lesson.matched_count == 0 and res_lesson.upserted_id is not None:
                inserted_lessons += 1
            else:
                updated_lessons += 1

    print(
        f"Seed complete. Skills: inserted={inserted_skills}, updated={updated_skills}; "
        f"Lessons: inserted={inserted_lessons}, updated={updated_lessons}"
    )

    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
