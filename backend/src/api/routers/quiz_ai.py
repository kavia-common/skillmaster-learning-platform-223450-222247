from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, validator
from datetime import datetime
import logging

from ...db.sqlalchemy import get_session
from ...db.relational_models import Lesson, Activity, Progress  # type: ignore
from ...services.openai_quiz_service import OpenAIQuizGenerator, OpenAIConfigError

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ai/quiz",
    tags=["Relational"],
)

# ----- Schemas -----

class QuizQuestion(BaseModel):
    question: str = Field(..., description="Question prompt")
    options: List[str] = Field(..., min_items=4, max_items=4, description="Exactly four options")
    answerIndex: int = Field(..., ge=0, le=3, description="Index into options array (0..3)")

class GenerateQuizRequest(BaseModel):
    lesson_id: int = Field(..., description="Numeric lesson ID to generate quiz for")
    pass_score: float = Field(70.0, ge=0, le=100, description="Score required to pass/unlock next lesson")
    difficulty: Optional[str] = Field("Beginner", description="Optional prompt hint")
    # Optional override for number of questions (currently fixed at 3)
    # num_questions: Optional[int] = Field(3, ge=3, le=3)

class GeneratedQuizResponse(BaseModel):
    activity_id: int = Field(..., description="Created quiz activity id")
    lesson_id: int = Field(..., description="Lesson id")
    title: str = Field(..., description="Quiz activity title")
    quiz_pass_score: float = Field(..., description="Pass score")
    quiz_questions: List[QuizQuestion] = Field(..., min_items=3, max_items=3, description="Generated questions")

class SubmitQuizRequest(BaseModel):
    user_id: str = Field(..., description="User taking the quiz")
    activity_id: int = Field(..., description="Quiz activity id")
    answers: List[int] = Field(..., description="Array of selected option indices corresponding to questions")

    @validator("answers")
    def answers_non_empty(cls, v):
        if not v:
            raise ValueError("answers cannot be empty")
        return v

class SubmitQuizResponse(BaseModel):
    activity_id: int = Field(..., description="Quiz activity id")
    lesson_id: int = Field(..., description="Lesson id")
    total_questions: int = Field(..., description="Total number of questions")
    correct: int = Field(..., description="Number of correct answers")
    score: float = Field(..., description="Score percentage 0..100")
    passed: bool = Field(..., description="Whether passed per quiz_pass_score")
    unlocked_next_lesson_id: Optional[int] = Field(None, description="Unlocked next lesson id if passed and available")

# ----- Helpers -----

def _get_openai_generator() -> OpenAIQuizGenerator:
    try:
        return OpenAIQuizGenerator()
    except OpenAIConfigError as e:
        raise HTTPException(status_code=503, detail=str(e))

def _get_next_lesson(session, current_lesson: Lesson) -> Optional[Lesson]:
    return (
        session.query(Lesson)
        .filter(
            Lesson.module_id == current_lesson.module_id,
            Lesson.order_index > current_lesson.order_index,
        )
        .order_by(Lesson.order_index.asc())
        .first()
    )

# ----- Routes -----

@router.post(
    "/generate",
    response_model=GeneratedQuizResponse,
    summary="Generate quiz via OpenAI for a lesson",
    description="Generates a 3-question multiple-choice quiz for the specified lesson using OpenAI. Persists as an Activity (type=quiz).",
    responses={
        200: {"description": "Quiz generated"},
        400: {"description": "Invalid request"},
        404: {"description": "Lesson not found"},
        503: {"description": "OpenAI not configured or unavailable"},
    },
)
async def generate_quiz(payload: GenerateQuizRequest, session=Depends(get_session)):
    """
    Generate and persist a quiz for a lesson using OpenAI.

    Parameters:
    - payload.lesson_id: target lesson id
    - payload.pass_score: pass/unlock threshold (default 70)
    - payload.difficulty: difficulty hint for LLM prompt

    Returns:
    - activity_id and quiz details that were created.
    """
    # Fetch lesson
    lesson: Lesson = session.query(Lesson).filter(Lesson.id == payload.lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    generator = _get_openai_generator()
    try:
        generated = await generator.generate_quiz(
            lesson_id=lesson.id,
            lesson_title=lesson.title,
            lesson_content=lesson.content or "",
            pass_score=payload.pass_score,
            difficulty=payload.difficulty or "Beginner",
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    # Persist as Activity (type=quiz)
    activity = Activity(
        lesson_id=lesson.id,
        type="quiz",
        title=generated.title,
        content=None,
        order_index=999,  # put at end by default
        quiz_questions=[q.__dict__ for q in generated.questions],
        quiz_pass_score=generated.pass_score,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(activity)
    session.commit()
    session.refresh(activity)

    return GeneratedQuizResponse(
        activity_id=activity.id,
        lesson_id=lesson.id,
        title=activity.title,
        quiz_pass_score=activity.quiz_pass_score or 70.0,
        quiz_questions=[QuizQuestion(**q) for q in activity.quiz_questions or []],
    )

@router.get(
    "/lesson/{lesson_id}",
    summary="Get lesson quiz",
    description="Fetch an existing quiz activity for the given lesson (first quiz found).",
    responses={
        200: {"description": "Quiz found"},
        404: {"description": "Quiz not found for lesson"},
    },
)
def get_lesson_quiz(lesson_id: int, session=Depends(get_session)):
    activity: Activity = (
        session.query(Activity)
        .filter(Activity.lesson_id == lesson_id, Activity.type == "quiz")
        .order_by(Activity.order_index.asc(), Activity.id.asc())
        .first()
    )
    if not activity:
        raise HTTPException(status_code=404, detail="No quiz found for lesson")
    return {
        "activity": {
            "id": activity.id,
            "lesson_id": activity.lesson_id,
            "type": activity.type,
            "title": activity.title,
            "quiz_questions": activity.quiz_questions,
            "quiz_pass_score": activity.quiz_pass_score,
            "created_at": activity.created_at,
            "updated_at": activity.updated_at,
        }
    }

@router.post(
    "/submit",
    response_model=SubmitQuizResponse,
    summary="Submit quiz answers",
    description="Submit quiz answers for grading, records attempt, and unlocks next lesson if passed (score >= quiz_pass_score).",
    responses={
        200: {"description": "Submission graded"},
        400: {"description": "Invalid answers length"},
        404: {"description": "Quiz activity not found"},
    },
)
def submit_quiz(payload: SubmitQuizRequest, session=Depends(get_session)):
    activity: Activity = session.query(Activity).filter(Activity.id == payload.activity_id, Activity.type == "quiz").first()
    if not activity:
        raise HTTPException(status_code=404, detail="Quiz activity not found")

    questions: List[Dict[str, Any]] = activity.quiz_questions or []
    if len(payload.answers) != len(questions):
        raise HTTPException(status_code=400, detail="answers length must equal number of questions")

    # grade
    correct = 0
    for idx, ans in enumerate(payload.answers):
        try:
            correct_idx = int(questions[idx]["answerIndex"])
            if ans == correct_idx:
                correct += 1
        except Exception:
            # malformed stored question; treat as incorrect
            pass

    total = len(questions)
    score = round((correct / total) * 100.0, 2) if total else 0.0
    pass_score = float(activity.quiz_pass_score or 70.0)
    passed = score >= pass_score

    # record attempt into Progress table (activity-level)
    progress = Progress(
        user_id=payload.user_id,
        subject_id=None,
        module_id=None,
        lesson_id=None,
        activity_id=activity.id,
        completed=True,
        score=score,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        deleted_at=None,
    )
    session.add(progress)

    unlocked_next_lesson_id: Optional[int] = None

    # if passed, unlock next lesson by creating a 'lesson' progress entry with status in_progress (or a marker)
    if passed:
        # Also mark this lesson completed with score for consistency
        lesson_progress = Progress(
            user_id=payload.user_id,
            subject_id=None,
            module_id=None,
            lesson_id=activity.lesson_id,
            activity_id=None,
            completed=True,
            score=score,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            deleted_at=None,
        )
        session.add(lesson_progress)

        # find next lesson to unlock
        current_lesson: Lesson = session.query(Lesson).filter(Lesson.id == activity.lesson_id).first()
        if current_lesson:
            next_lesson = _get_next_lesson(session, current_lesson)
            if next_lesson:
                # create a progress entry to indicate unlocked (in_progress=false but not completed)
                unlock_marker = Progress(
                    user_id=payload.user_id,
                    subject_id=None,
                    module_id=None,
                    lesson_id=next_lesson.id,
                    activity_id=None,
                    completed=False,
                    score=None,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    deleted_at=None,
                )
                session.add(unlock_marker)
                unlocked_next_lesson_id = next_lesson.id

    session.commit()

    return SubmitQuizResponse(
        activity_id=activity.id,
        lesson_id=activity.lesson_id,
        total_questions=total,
        correct=correct,
        score=score,
        passed=passed,
        unlocked_next_lesson_id=unlocked_next_lesson_id,
    )
