import os
import json
import logging
from typing import List, Optional
from dataclasses import dataclass, field
import httpx

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DEFAULT_TIMEOUT = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "20"))

@dataclass
class QuizQuestion:
    """Represents a single generated quiz question."""
    question: str
    options: List[str]
    answerIndex: int

@dataclass
class GeneratedQuiz:
    """Represents a generated quiz with metadata."""
    lesson_id: int
    title: str
    pass_score: float
    questions: List[QuizQuestion] = field(default_factory=list)

class OpenAIConfigError(Exception):
    """Raised when OpenAI configuration is missing or invalid."""

class OpenAIQuizGenerator:
    """
    PUBLIC_INTERFACE
    Generates quiz questions for a lesson using OpenAI.

    This class encapsulates prompt construction and response parsing, and provides
    defensive error handling around network timeouts and malformed LLM outputs.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, timeout_seconds: Optional[float] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise OpenAIConfigError("OPENAI_API_KEY is not configured. Please set it in the environment.")
        self.model = model or DEFAULT_MODEL
        self.timeout_seconds = timeout_seconds or DEFAULT_TIMEOUT

    def _build_system_prompt(self) -> str:
        return (
            "You are an assistant that generates multiple-choice quizzes for short lessons. "
            "Return strictly valid JSON with fields: questions (array of 3 objects), each having "
            "question (string), options (array of 4 strings), answerIndex (0-3 integer). "
            "Avoid extra commentary; return JSON only."
        )

    def _build_user_prompt(self, lesson_title: str, lesson_content: str, difficulty: str = "Beginner") -> str:
        return (
            f"Generate a 3-question multiple-choice quiz for the lesson.\n"
            f"Title: {lesson_title}\n"
            f"Difficulty: {difficulty}\n"
            f"Content:\n{lesson_content}\n\n"
            "Ensure:\n"
            "- Questions target key points from the content.\n"
            "- Each has exactly 4 concise options.\n"
            "- answerIndex correctly identifies the best option.\n"
            "Return JSON with shape:\n"
            "{\n"
            '  "questions": [\n'
            '    {"question": "...", "options": ["...","...","...","..."], "answerIndex": 0},\n'
            '    {"question": "...", "options": ["...","...","...","..."], "answerIndex": 2},\n'
            '    {"question": "...", "options": ["...","...","...","..."], "answerIndex": 1}\n'
            "  ]\n"
            "}"
        )

    async def generate_quiz(self, lesson_id: int, lesson_title: str, lesson_content: str, pass_score: float = 70.0, difficulty: str = "Beginner") -> GeneratedQuiz:
        """
        PUBLIC_INTERFACE
        Generate a quiz for a lesson using OpenAI.

        Args:
            lesson_id: Numeric lesson ID.
            lesson_title: Title of the lesson.
            lesson_content: Lesson content in text/markdown.
            pass_score: Score percentage required to pass (default 70).
            difficulty: Difficulty label for prompt context.

        Returns:
            GeneratedQuiz with three questions.

        Raises:
            OpenAIConfigError if OPENAI_API_KEY is missing.
            RuntimeError for network or parsing errors.
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(lesson_title, lesson_content, difficulty)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except httpx.TimeoutException as te:
            logger.error("OpenAI API timeout: %s", te)
            raise RuntimeError("OpenAI API request timed out") from te
        except httpx.HTTPStatusError as he:
            # do not log API key or full response content
            logger.error("OpenAI API error status=%s", he.response.status_code)
            raise RuntimeError(f"OpenAI API returned error: {he.response.status_code}") from he
        except Exception as e:
            logger.exception("Unexpected error calling OpenAI API")
            raise RuntimeError("Unexpected error calling OpenAI API") from e

        try:
            content = data["choices"][0]["message"]["content"]
            # Strip code fences if model wraps output
            content_stripped = content.strip()
            if content_stripped.startswith("```"):
                # remove backticks wrapper
                content_stripped = content_stripped.strip("`")
                # handle optional json language tag
                if content_stripped.startswith("json"):
                    content_stripped = content_stripped[4:].strip()
            parsed = json.loads(content_stripped)
            questions_raw = parsed.get("questions", [])
            questions: List[QuizQuestion] = []
            for q in questions_raw[:3]:
                question = str(q.get("question", "")).strip()
                options = list(map(str, q.get("options", [])))
                answer_idx = int(q.get("answerIndex", 0))
                if not question or len(options) != 4 or not (0 <= answer_idx <= 3):
                    continue
                questions.append(QuizQuestion(question=question, options=options, answerIndex=answer_idx))
            if len(questions) != 3:
                raise ValueError("Model did not return exactly 3 valid questions.")
            return GeneratedQuiz(lesson_id=lesson_id, title=f"{lesson_title} - Quiz", pass_score=float(pass_score), questions=questions)
        except Exception as pe:
            logger.error("Failed to parse OpenAI response: %s", str(pe))
            raise RuntimeError("Failed to parse OpenAI quiz response") from pe
