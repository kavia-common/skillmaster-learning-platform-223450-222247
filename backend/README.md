# SkillMaster Backend

FastAPI backend for the SkillMaster micro skill-based learning platform.

## Running locally

- Ensure Python 3.11+
- Install dependencies:

```bash
pip install -r requirements.txt
```

- Copy `.env.example` to `.env` and adjust values as needed.
- Start the app:

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 3001 --reload
```

Open API docs at: http://localhost:3001/docs

## Environment variables

Provide these in `.env`:
- MONGODB_URI=mongodb://<user>:<pass>@<host>:<port>/<db>?retryWrites=true&w=majority
- JWT_SECRET=change-this-later

Other optional frontend config variables are also supported as shown in `.env.example`.

## Seeding initial content

The project includes a seed script to populate initial skills and lessons (with quizzes and badges).

```bash
# Ensure MONGODB_URI is set in your environment or .env
python scripts/seed_skills.py
```

The script is idempotent (upserts by slug) and prints inserted/updated counts.

## Content routes (Mongo-backed)

Public GET endpoints:
- GET `/content/skills` – List skills with filters: `category`, `difficulty`, `search`, `page`, `page_size`
- GET `/content/skills/{slug}` – Skill detail by slug
- GET `/content/skills/{slug}/lessons` – Lessons for a skill
- GET `/content/lessons/{slug}` – Lesson detail (includes quiz and badge)

Admin-only (JWT required; minimal stub):
- POST `/content/skills`
- PUT `/content/skills/{slug}`
- DELETE `/content/skills/{slug}`
- POST `/content/lessons`
- PUT `/content/lessons/{slug}`
- DELETE `/content/lessons/{slug}`

To call admin routes, send a Bearer token signed with `JWT_SECRET` and payload including `"role": "admin"`.

JWT library: This project uses PyJWT (imported as `import jwt`). Ensure your environment installs dependencies via `pip install -r requirements.txt` and avoid creating any local file named `jwt.py` which would shadow the PyJWT package.

## Existing prototype routes (in-memory)

- Health
  - GET `/` – Service health

- Skills
  - GET `/skills` – List skills
  - GET `/skills/{skill_id}` – Skill detail with modules/lessons
  - GET `/skills/{skill_id}/modules` – Modules for a skill

- Lessons
  - GET `/modules/{module_id}/lessons` – Lessons for a module

- Progress
  - GET `/progress/{user_id}` – Aggregated progress for a user
  - POST `/progress/complete` – Mark a lesson completed
  - GET `/progress/{user_id}/lesson/{lesson_id}` – Progress entries for a lesson

## Generating OpenAPI JSON

```bash
python -m src.api.generate_openapi
```

This writes `interfaces/openapi.json`.
