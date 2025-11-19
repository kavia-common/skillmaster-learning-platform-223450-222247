"""
Seed initial relational data for Subjects → Modules → Lessons → Activities/Quizzes.

This module can be executed as:
    python -m src.seeds.seed_initial_content

Or, when SEED_RELATIONAL_DATA=true is set in the environment, it will run once on FastAPI startup
(if integrated into app startup as shown in README).

Idempotent behavior:
- Uses unique slugs/names to upsert subjects, modules, lessons.
- Activities are upserted by (lesson_id, type, title).
- Quizzes are upserted by lesson and will replace prior questions if titles match.

Environment:
- Uses relational DB configured by existing SQLAlchemy setup in src/db/sqlalchemy.py.

PUBLIC_INTERFACE
"""
from __future__ import annotations

import logging
import os
from typing import Dict, List, Tuple, Any

from sqlalchemy.orm import Session

# Use project SQLAlchemy session/engine utilities
from src.db.sqlalchemy import get_engine, get_session_factory
from src.db.relational_models import (
    Subject,
    Module,
    Lesson,
    Activity,
    ActivityType,
    QuizQuestion,
)
from src.db.table_init import init_all_tables  # ensure tables exist before seeding

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# PUBLIC_INTERFACE
def seed_initial_content(session: Session) -> None:
    """Seed the relational database with initial content.

    Idempotent upsert behavior for:
    - Subjects (by name)
    - Modules (by subject + title)
    - Lessons (by module + title)
    - Activities (by lesson + title + type)
    - QuizQuestions (by lesson; replaces questions on re-seed)

    Raises:
        Exception: Propagates DB errors to caller so CI can fail fast if schema mismatches.
    """
    # Data model to insert
    subjects: Dict[str, Dict[str, Any]] = {
        "Programming": {
            "modules": {
                "Web Development": [
                    (
                        "Intro to HTML & CSS",
                        "Understand basics of HTML structure and CSS styling.",
                        [
                            ("content", "Read: HTML Semantics", "Overview of semantic tags"),
                            ("video", "Video: CSS Selectors", "10-minute intro"),
                        ],
                        [
                            {
                                "question": "What does CSS stand for?",
                                "options": [
                                    "Cascading Style Sheets",
                                    "Creative Style System",
                                    "Computer Styled Sections",
                                    "Cascading Simple Styles",
                                ],
                                "answerIndex": 0,
                            },
                            {
                                "question": "Which tag defines a hyperlink in HTML?",
                                "options": ["<div>", "<a>", "<link>", "<href>"],
                                "answerIndex": 1,
                            },
                            {
                                "question": "Which CSS selector targets an element by id 'main'?",
                                "options": ["#main", ".main", "*main", "id(main)"],
                                "answerIndex": 0,
                            },
                        ],
                    ),
                    (
                        "JavaScript Fundamentals",
                        "Learn variables, functions, and DOM basics.",
                        [
                            ("content", "Read: Variables and Types", "let, const overview"),
                            ("coding", "Practice: DOM selectors", "Query elements by id/class"),
                        ],
                        [
                            {
                                "question": "Which keyword defines a block-scoped variable?",
                                "options": ["var", "def", "let", "set"],
                                "answerIndex": 2,
                            },
                            {
                                "question": "Which method finds element by id?",
                                "options": [
                                    "querySelectorAll",
                                    "getElementById",
                                    "getElementsByClassName",
                                    "querySelectorAll('#id')",
                                ],
                                "answerIndex": 1,
                            },
                            {
                                "question": "Which is NOT a JavaScript primitive?",
                                "options": ["string", "number", "object", "boolean"],
                                "answerIndex": 2,
                            },
                        ],
                    ),
                ],
                "Backend": [
                    (
                        "APIs with FastAPI",
                        "Build REST endpoints using FastAPI.",
                        [
                            ("content", "Read: Path params vs query params", "Core routing patterns"),
                            ("video", "Video: FastAPI Intro", "FastAPI quickstart"),
                        ],
                        [
                            {
                                "question": "FastAPI is built atop which ASGI framework?",
                                "options": ["Flask", "Django", "Starlette", "Falcon"],
                                "answerIndex": 2,
                            },
                            {
                                "question": "Pydantic is used primarily for?",
                                "options": ["Templating", "Validation", "ORM", "Routing"],
                                "answerIndex": 1,
                            },
                            {
                                "question": "OpenAPI schema is available by default at:",
                                "options": ["/docs", "/openapi.json", "/schema", "/redoc"],
                                "answerIndex": 1,
                            },
                        ],
                    ),
                ],
                "Python Basics": [
                    (
                        "Data Types and Control Flow",
                        "Learn lists, dicts, loops, and conditionals.",
                        [
                            ("content", "Read: List vs Tuple", "Mutability differences"),
                            ("coding", "Exercise: Dict Comprehensions", "Create dicts concisely"),
                        ],
                        [
                            {
                                "question": "Which is immutable?",
                                "options": ["list", "tuple", "dict", "set"],
                                "answerIndex": 1,
                            },
                            {
                                "question": "Which keyword creates a loop over iterables?",
                                "options": ["iterate", "for", "loop", "each"],
                                "answerIndex": 1,
                            },
                            {
                                "question": "Which creates a dictionary comprehension?",
                                "options": [
                                    "[x for x in xs]",
                                    "{x for x in xs}",
                                    "{k: v for k, v in pairs}",
                                    "(x for x in xs)",
                                ],
                                "answerIndex": 2,
                            },
                        ],
                    ),
                ],
                "APIs & Integration": [
                    (
                        "Consuming REST APIs",
                        "Use requests/HTTPX to call external APIs.",
                        [
                            ("content", "Read: HTTP methods", "GET vs POST etc."),
                            ("coding", "Practice: HTTPX GET", "Fetch JSON and parse"),
                        ],
                        [
                            {
                                "question": "Which status code indicates success?",
                                "options": ["200", "301", "404", "500"],
                                "answerIndex": 0,
                            },
                            {
                                "question": "Which method creates resources?",
                                "options": ["GET", "POST", "PUT", "DELETE"],
                                "answerIndex": 1,
                            },
                            {
                                "question": "JSON stands for:",
                                "options": [
                                    "Java Serialized Object Notation",
                                    "JavaScript Object Notation",
                                    "Just Simple Object Notation",
                                    "Joined Schema Object Notation",
                                ],
                                "answerIndex": 1,
                            },
                        ],
                    ),
                ],
            }
        },
        "Data Science": {
            "modules": {
                "Python for Data Analysis": [
                    (
                        "Working with Pandas",
                        "Load CSV, filter, and aggregate data.",
                        [
                            ("content", "Read: DataFrames vs Series", "Key structures"),
                            ("coding", "Practice: groupby", "Aggregate metrics"),
                        ],
                        [
                            {
                                "question": "Which library provides DataFrame?",
                                "options": ["numpy", "pandas", "matplotlib", "seaborn"],
                                "answerIndex": 1,
                            },
                            {
                                "question": "Which reads CSV into DataFrame?",
                                "options": ["pd.read_csv", "pd.load_csv", "np.read_csv", "pd.csv()"],
                                "answerIndex": 0,
                            },
                            {
                                "question": "Series represents:",
                                "options": ["2D data", "1D labeled array", "Plot line", "Index only"],
                                "answerIndex": 1,
                            },
                        ],
                    )
                ],
                "Pandas & NumPy": [
                    (
                        "Vectorized Computations",
                        "Use NumPy arrays for fast operations.",
                        [
                            ("content", "Read: Broadcasting rules", "Shapes and operations"),
                            ("video", "Video: NumPy Basics", "Intro to arrays"),
                        ],
                        [
                            {
                                "question": "NumPy array type is called:",
                                "options": ["ndarray", "npArray", "array", "matrix"],
                                "answerIndex": 0,
                            },
                            {
                                "question": "Broadcasting enables:",
                                "options": [
                                    "Faster file IO",
                                    "Operations on different shapes",
                                    "Plotting",
                                    "Database joins",
                                ],
                                "answerIndex": 1,
                            },
                            {
                                "question": "Which creates an array of zeros?",
                                "options": ["np.empty", "np.ones", "np.zeros", "np.nan"],
                                "answerIndex": 2,
                            },
                        ],
                    )
                ],
                "Machine Learning": [
                    (
                        "ML Basics",
                        "Understand train/test split and evaluation.",
                        [
                            ("content", "Read: Overfitting vs underfitting", "Generalization"),
                            ("coding", "Practice: train_test_split", "Split dataset"),
                        ],
                        [
                            {
                                "question": "Which library provides train_test_split?",
                                "options": ["pandas", "scikit-learn", "numpy", "matplotlib"],
                                "answerIndex": 1,
                            },
                            {
                                "question": "Overfitting means:",
                                "options": [
                                    "Model too simple",
                                    "Model generalizes well",
                                    "Model memorizes training",
                                    "Insufficient data",
                                ],
                                "answerIndex": 2,
                            },
                            {
                                "question": "Accuracy is:",
                                "options": [
                                    "TP / (TP + FP)",
                                    "(TP+TN)/(TP+TN+FP+FN)",
                                    "FN / (FN + TP)",
                                    "FP / (FP + TN)",
                                ],
                                "answerIndex": 1,
                            },
                        ],
                    )
                ],
                "Power BI & Excel": [
                    (
                        "Dashboards 101",
                        "Build simple dashboards with charts.",
                        [
                            ("content", "Read: Choosing chart types", "Bar/Line/Pie etc."),
                            ("video", "Video: Excel Pivot Basics", "Summarize data"),
                        ],
                        [
                            {
                                "question": "Pivot tables are used to:",
                                "options": [
                                    "Create formulas",
                                    "Aggregate and summarize data",
                                    "Connect to databases",
                                    "Format cells",
                                ],
                                "answerIndex": 1,
                            },
                            {
                                "question": "Power BI is primarily for:",
                                "options": ["Web dev", "Data viz & BI", "ML training", "Data storage"],
                                "answerIndex": 1,
                            },
                            {
                                "question": "Best chart for a trend over time:",
                                "options": ["Pie", "Bar", "Scatter", "Line"],
                                "answerIndex": 3,
                            },
                        ],
                    )
                ],
            }
        },
        "System Architecture": {
            "modules": {
                "RESTful Design": [
                    (
                        "Resources and Endpoints",
                        "Model resources and CRUD correctly.",
                        [
                            ("content", "Read: Resource naming", "Plural nouns, nested paths"),
                            ("coding", "Exercise: Design endpoints", "Map to resources"),
                        ],
                        [
                            {
                                "question": "Which HTTP verb is idempotent?",
                                "options": ["POST", "GET", "PATCH", "OPTIONS"],
                                "answerIndex": 1,
                            },
                            {
                                "question": "Resource naming should be:",
                                "options": [
                                    "Verbs",
                                    "Plural nouns",
                                    "Random strings",
                                    "Uppercase",
                                ],
                                "answerIndex": 1,
                            },
                            {
                                "question": "Which describes filtering?",
                                "options": [
                                    "Path segment",
                                    "Request body",
                                    "Query parameters",
                                    "Headers",
                                ],
                                "answerIndex": 2,
                            },
                        ],
                    )
                ],
                "Modular API Design": [
                    (
                        "Versioning & Modules",
                        "Design modular services with versioning.",
                        [
                            ("content", "Read: URL vs header versioning", "Trade-offs"),
                            ("video", "Video: Modular monolith", "Bounded contexts"),
                        ],
                        [
                            {
                                "question": "Versioning helps:",
                                "options": [
                                    "SEO only",
                                    "Backward compatibility",
                                    "Caching only",
                                    "CI speed",
                                ],
                                "answerIndex": 1,
                            },
                            {
                                "question": "Bounded contexts are part of:",
                                "options": [
                                    "REST spec",
                                    "DDD",
                                    "SQL standard",
                                    "HTML5",
                                ],
                                "answerIndex": 1,
                            },
                            {
                                "question": "Common version prefix:",
                                "options": ["/api", "/v1", "/svc", "/rest"],
                                "answerIndex": 1,
                            },
                        ],
                    )
                ],
                "Database Modeling": [
                    (
                        "Normalization Basics",
                        "Avoid redundancy & anomalies.",
                        [
                            ("content", "Read: 1NF/2NF/3NF", "Normalization forms"),
                            ("coding", "Exercise: ER Modeling", "Relate entities"),
                        ],
                        [
                            {
                                "question": "1NF requires:",
                                "options": [
                                    "Transitive dependencies",
                                    "Atomic values",
                                    "No primary keys",
                                    "Only one table",
                                ],
                                "answerIndex": 1,
                            },
                            {
                                "question": "Foreign key ensures:",
                                "options": [
                                    "Uniqueness",
                                    "Referential integrity",
                                    "Indexing",
                                    "Sharding",
                                ],
                                "answerIndex": 1,
                            },
                            {
                                "question": "Denormalization trades space for:",
                                "options": ["Simplicity", "Speed", "Integrity", "ACID"],
                                "answerIndex": 1,
                            },
                        ],
                    )
                ],
            }
        },
        "Soft Skills": {
            "modules": {
                "Communication": [
                    (
                        "Active Listening",
                        "Improve understanding and feedback.",
                        [
                            ("content", "Read: Reflective listening", "Paraphrase and confirm"),
                            ("video", "Video: Listening skills", "Body language cues"),
                        ],
                        [
                            {
                                "question": "Active listening includes:",
                                "options": ["Interrupting", "Paraphrasing", "Multitasking", "Guessing"],
                                "answerIndex": 1,
                            },
                            {
                                "question": "Eye contact helps:",
                                "options": [
                                    "Distraction",
                                    "Signal attention",
                                    "Intimidation",
                                    "Silence",
                                ],
                                "answerIndex": 1,
                            },
                            {
                                "question": "Clarifying questions are asked:",
                                "options": ["After meeting", "Never", "During conversation", "By email"],
                                "answerIndex": 2,
                            },
                        ],
                    )
                ],
                "Time Management": [
                    (
                        "Prioritization",
                        "Use Eisenhower matrix & batching.",
                        [
                            ("content", "Read: Eisenhower matrix", "Urgent vs important"),
                            ("coding", "Exercise: Task batching", "Group similar tasks"),
                        ],
                        [
                            {
                                "question": "Which is important and not urgent?",
                                "options": ["Deep work", "Firefighting", "Meetings", "Breaks"],
                                "answerIndex": 0,
                            },
                            {
                                "question": "Context switching:",
                                "options": [
                                    "Improves efficiency",
                                    "Is free",
                                    "Has cognitive cost",
                                    "Is mandatory",
                                ],
                                "answerIndex": 2,
                            },
                            {
                                "question": "Batching tasks can:",
                                "options": ["Reduce overhead", "Increase stress", "Waste time", "Add steps"],
                                "answerIndex": 0,
                            },
                        ],
                    )
                ],
                "Problem Solving": [
                    (
                        "Root Cause Analysis",
                        "Apply 5 Whys & fishbone diagrams.",
                        [
                            ("content", "Read: 5 Whys", "Iterative questioning"),
                            ("video", "Video: Fishbone diagram", "Categorize causes"),
                        ],
                        [
                            {
                                "question": "5 Whys helps find:",
                                "options": [
                                    "Symptoms",
                                    "Root cause",
                                    "Quick fixes",
                                    "Stakeholders",
                                ],
                                "answerIndex": 1,
                            },
                            {
                                "question": "Ishikawa is also called:",
                                "options": [
                                    "Tree diagram",
                                    "Fishbone diagram",
                                    "Pie chart",
                                    "SWOT",
                                ],
                                "answerIndex": 1,
                            },
                            {
                                "question": "Corrective actions should be:",
                                "options": ["Temporary", "Random", "Target the cause", "Ignored"],
                                "answerIndex": 2,
                            },
                        ],
                    )
                ],
            }
        },
        "Creative Tech": {
            "modules": {
                "UI/UX Design": [
                    (
                        "Design Principles",
                        "Learn hierarchy, contrast, and spacing.",
                        [
                            ("content", "Read: Visual hierarchy", "Size, color, and spacing"),
                            ("video", "Video: UX heuristics", "Nielsen's principles"),
                        ],
                        [
                            {
                                "question": "Which improves readability?",
                                "options": ["Dense text", "Proper spacing", "Low contrast", "Small font"],
                                "answerIndex": 1,
                            },
                            {
                                "question": "UX stands for:",
                                "options": [
                                    "Unified Experience",
                                    "User Experience",
                                    "Universal Exchange",
                                    "Unique Execution",
                                ],
                                "answerIndex": 1,
                            },
                            {
                                "question": "Primary action buttons should be:",
                                "options": [
                                    "Hidden",
                                    "Same as secondary",
                                    "Visually prominent",
                                    "Random color",
                                ],
                                "answerIndex": 2,
                            },
                        ],
                    )
                ],
                "Branding & Documentation": [
                    (
                        "Style Guides",
                        "Create and use brand style guides.",
                        [
                            ("content", "Read: Tone and voice", "Consistency matters"),
                            ("coding", "Exercise: Template library", "Reusable docs"),
                        ],
                        [
                            {
                                "question": "Style guides improve:",
                                "options": [
                                    "Inconsistency",
                                    "Onboarding and consistency",
                                    "Bugs",
                                    "Runtime speed",
                                ],
                                "answerIndex": 1,
                            },
                            {
                                "question": "Brand voice should be:",
                                "options": ["Random", "Consistent", "Silent", "Aggressive"],
                                "answerIndex": 1,
                            },
                            {
                                "question": "Component libraries provide:",
                                "options": ["Duplication", "Reusability", "Confusion", "None"],
                                "answerIndex": 1,
                            },
                        ],
                    )
                ],
                "Gamification Principles": [
                    (
                        "Motivation & Rewards",
                        "Use points, badges, and challenges.",
                        [
                            ("content", "Read: Intrinsic vs extrinsic", "Balance rewards"),
                            ("video", "Video: Reward schedules", "Keep engagement"),
                        ],
                        [
                            {
                                "question": "Badges are an example of:",
                                "options": [
                                    "Intrinsic motivation",
                                    "Extrinsic motivation",
                                    "Neutral motivation",
                                    "Negative reinforcement",
                                ],
                                "answerIndex": 1,
                            },
                            {
                                "question": "Leaderboards tap into:",
                                "options": ["Collaboration", "Competition", "Confusion", "Rest"],
                                "answerIndex": 1,
                            },
                            {
                                "question": "Excessive rewards can:",
                                "options": [
                                    "Always help",
                                    "Reduce intrinsic motivation",
                                    "Have no effect",
                                    "Guarantee learning",
                                ],
                                "answerIndex": 1,
                            },
                        ],
                    )
                ],
            }
        },
    }

    # Upsert pipeline
    for subject_name, subject_payload in subjects.items():
        subject = _get_or_create_subject(session, subject_name)

        modules: Dict[str, List[Tuple[str, str, List[Tuple[str, str, str]], List[Dict[str, Any]]]]] = subject_payload.get(
            "modules", {}
        )

        for module_order, (module_title, lessons) in enumerate(modules.items(), start=1):
            module = _get_or_create_module(session, subject, module_title, module_order)

            for idx, (lesson_title, lesson_summary, activities, quiz_questions) in enumerate(lessons, start=1):
                lesson = _get_or_create_lesson(session, module, lesson_title, lesson_summary, idx)

                # Upsert activities for each lesson
                for activity in activities:
                    a_type_str, a_title, a_desc = activity
                    a_type = _to_activity_type(a_type_str)
                    _get_or_create_activity(session, lesson, a_type, a_title, a_desc, order=idx)

                # Upsert quiz questions for each lesson: replace on reseed
                _replace_quiz_questions(session, lesson, quiz_questions)

    session.commit()
    logger.info("Seed complete: subjects/modules/lessons/activities/quizzes populated.")


def _to_activity_type(value: str) -> ActivityType:
    v = (value or "").strip().lower()
    if v in ("content", "text", "reading"):
        return ActivityType.CONTENT
    if v in ("video", "media"):
        return ActivityType.VIDEO
    if v in ("coding", "exercise", "code"):
        return ActivityType.CODING
    # Default to content to be safe
    return ActivityType.CONTENT


def _get_or_create_subject(session: Session, name: str) -> Subject:
    subject = session.query(Subject).filter(Subject.name == name).one_or_none()
    if subject:
        return subject
    subject = Subject(name=name, description=f"{name} subject")
    session.add(subject)
    session.flush()
    return subject


def _get_or_create_module(session: Session, subject: Subject, title: str, order: int) -> Module:
    module = (
        session.query(Module)
        .filter(Module.subject_id == subject.id, Module.title == title)
        .one_or_none()
    )
    if module:
        # ensure order stable
        if module.order != order:
            module.order = order
            session.add(module)
        return module
    module = Module(subject_id=subject.id, title=title, description=None, order=order)
    session.add(module)
    session.flush()
    return module


def _get_or_create_lesson(
    session: Session, module: Module, title: str, content: str, order: int
) -> Lesson:
    lesson = (
        session.query(Lesson)
        .filter(Lesson.module_id == module.id, Lesson.title == title)
        .one_or_none()
    )
    if lesson:
        # update content/order if changed
        updated = False
        if lesson.content != content:
            lesson.content = content
            updated = True
        if lesson.order != order:
            lesson.order = order
            updated = True
        if updated:
            session.add(lesson)
        return lesson
    lesson = Lesson(module_id=module.id, title=title, content=content, order=order)
    session.add(lesson)
    session.flush()
    return lesson


def _get_or_create_activity(
    session: Session,
    lesson: Lesson,
    a_type: ActivityType,
    title: str,
    description: str,
    order: int,
) -> Activity:
    activity = (
        session.query(Activity)
        .filter(
            Activity.lesson_id == lesson.id,
            Activity.title == title,
            Activity.type == a_type,
        )
        .one_or_none()
    )
    if activity:
        # Update description/order if needed
        updated = False
        if activity.description != description:
            activity.description = description
            updated = True
        if activity.order != order:
            activity.order = order
            updated = True
        if updated:
            session.add(activity)
        return activity
    activity = Activity(
        lesson_id=lesson.id,
        type=a_type,
        title=title,
        description=description,
        order=order,
    )
    session.add(activity)
    session.flush()
    return activity


def _replace_quiz_questions(session: Session, lesson: Lesson, questions: List[Dict[str, Any]]) -> None:
    # Remove existing questions to keep predictable order and idempotency
    existing = session.query(QuizQuestion).filter(QuizQuestion.lesson_id == lesson.id).all()
    for q in existing:
        session.delete(q)
    session.flush()

    order = 1
    for q in questions:
        session.add(
            QuizQuestion(
                lesson_id=lesson.id,
                question=q["question"],
                option_a=q["options"][0],
                option_b=q["options"][1],
                option_c=q["options"][2],
                option_d=q["options"][3],
                answer_index=q["answerIndex"],
                order=order,
            )
        )
        order += 1


def _should_seed_from_env() -> bool:
    return os.getenv("SEED_RELATIONAL_DATA", "false").lower() == "true"


# PUBLIC_INTERFACE
def main() -> None:
    """CLI entrypoint to run the seed script manually.

    Example:
        python -m src.seeds.seed_initial_content
    """
    engine = get_engine()
    # make sure tables exist
    init_all_tables(engine)
    SessionFactory = get_session_factory(engine)
    with SessionFactory() as session:
        seed_initial_content(session)


if __name__ == "__main__":
    main()
