# OpenAI Quiz Generation

This backend integrates with OpenAI to generate lesson quizzes and supports adaptive unlocking.

## Endpoints

- POST /ai/quiz/generate
  - Body: { "lesson_id": number, "pass_score": 70, "difficulty": "Beginner" }
  - Creates an Activity (type=quiz) with 3 questions and pass threshold.

- GET /ai/quiz/lesson/{lesson_id}
  - Returns the first quiz Activity for a lesson.

- POST /ai/quiz/submit
  - Body: { "user_id": "user-123", "activity_id": 25, "answers": [0,2,1] }
  - Grades attempt, records Progress for activity and lesson. If passed (score >= quiz_pass_score), unlocks next lesson by creating an unlocked progress entry.

## Configuration

- OPENAI_API_KEY: Required. API key for OpenAI.
- OPENAI_MODEL: Optional. Default "gpt-4o-mini".
- OPENAI_TIMEOUT_SECONDS: Optional. Default "20".

These must be set in the container environment (.env).

## Error Handling

- 503 returned if OpenAI is misconfigured or times out.
- 404 returned if target lesson or quiz is not found.
- 400 returned on validation errors (e.g., answers length mismatch).

## Security

- No secrets are logged.
- The service times out OpenAI requests to avoid request pile-ups.
