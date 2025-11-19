# OpenAI-powered Quiz Generation

This backend integrates with OpenAI to generate lesson quizzes and supports adaptive unlocking.

Configure environment:
- OPENAI_API_KEY must be set
- Optional:
  - OPENAI_MODEL (default gpt-4o-mini)
  - OPENAI_TIMEOUT_SECONDS (default 20)

Endpoints:
- POST /ai/quiz/generate -> create a quiz Activity for a lesson
- GET /ai/quiz/lesson/{lesson_id} -> fetch existing quiz for a lesson
- POST /ai/quiz/submit -> grade and record attempt; unlock next lesson if score >= pass threshold

See docs/OPENAI_QUIZ.md for details.
