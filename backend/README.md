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

## Endpoints overview

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
