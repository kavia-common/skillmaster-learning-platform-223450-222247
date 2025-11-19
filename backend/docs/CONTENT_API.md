# Content API (Mongo-backed)

Public GET:
- GET /content/skills?category=Digital%20Skills&difficulty=Beginner&search=html&page=1&page_size=10
- GET /content/skills/{slug}
- GET /content/skills/{slug}/lessons
- GET /content/lessons/{slug}

Admin-only (Bearer token with role=admin):
- POST /content/skills
- PUT /content/skills/{slug}
- DELETE /content/skills/{slug}
- POST /content/lessons
- PUT /content/lessons/{slug}
- DELETE /content/lessons/{slug}

Quiz schema:
quiz: [
  { "question": "...", "options": ["a","b","c","d"], "answerIndex": 0 },
  ...
] (exactly 3)

AI Quiz generation and adaptive unlocking (relational-backed):
- POST /ai/quiz/generate
- GET /ai/quiz/lesson/{lesson_id}
- POST /ai/quiz/submit
