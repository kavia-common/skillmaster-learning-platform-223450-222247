# SkillMaster Backend

FastAPI backend for the SkillMaster micro skill-based learning platform.

## Relational Data Seeding

This repository includes an idempotent seeding utility to populate Subjects → Skills (Beginner/Intermediate/Advanced) → Modules → Lessons → Activities.

Two ways to run the seed:

1) CLI (recommended for local/dev)
- Ensure your relational DB is configured via environment variables used by the existing SQLAlchemy integration.
- Run:
```
cd backend
python -m src.seeds.seed_initial_content
```
This will:
- Ensure tables exist
- Upsert subjects, progressive skills, modules, lessons, and activities
- Be safe to re-run without creating duplicates

2) Automatic on FastAPI startup
Set the environment variable:
```
SEED_RELATIONAL_DATA=true
```
Then start your API server as usual. On startup, it will:
- Ensure tables exist
- Run the same idempotent seeding logic

Seeded topics:
- Subjects (topics): Digital, Communication, Career, Leadership, Creativity
- For each, Skills (progression levels): Beginner → Intermediate → Advanced
- Minimal content per skill (1 module, 1 lesson, 1 activity) to avoid empty states

## New Endpoints (relational skills)

- GET `/skills?subject_slug={topic}&level={Beginner|Intermediate|Advanced}` — list skills filtered by topic and level
- POST `/skills` — create skill (body: SkillCreate)
- GET `/skills/{skill_slug}` — get skill detail
- PUT `/skills/{skill_slug}` — update skill fields
- DELETE `/skills/{skill_slug}` — soft delete
- GET `/skills/{skill_slug}/modules` — list modules under a given skill

Existing catalog/content endpoints under `/content/*` remain available.

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
- Optional: SQLALCHEMY_DATABASE_URL for relational hierarchy + progress
  - Defaults to SQLite at `sqlite:///./skillmaster.db` if not set (sync engine).
  - Example Postgres (sync): `postgresql+psycopg2://USER:PASSWORD@HOST:5432/DBNAME`

Other optional frontend config variables are also supported as shown in `.env.example`.

## Initialize relational tables (optional)

A relational schema is provided for Subjects → Skills → Modules → Lessons → Activities/Quiz and Progress.
Create the tables locally (uses SQLALCHEMY_DATABASE_URL or defaults to SQLite):

```bash
python -m src.db.table_init
```

This is idempotent and safe to run repeatedly.

## SQLAlchemy & Drivers

- The project uses SQLAlchemy 2.x with a synchronous engine in `src/db/sqlalchemy.py`.
- Default DB URL is SQLite (sync) `sqlite:///./skillmaster.db`.
- For Postgres in production, set `SQLALCHEMY_DATABASE_URL=postgresql+psycopg2://...` and ensure `psycopg2-binary` is installed.

## Content routes (Mongo-backed)

Public GET endpoints:
- GET `/content/skills` – List skills with filters: `category`, `difficulty`, `search`, `page`, `page_size`
- GET `/content/skills/{slug}` – Skill detail by slug
- GET `/content/skills/{slug}/lessons` – Lessons for a skill
- GET `/content/lessons/{slug}` – Lesson detail (includes quiz and badge)

Admin-only (JWT required):
- POST `/content/skills`
- PUT `/content/skills/{slug}`
- DELETE `/content/skills/{slug}`
- POST `/content/lessons`
- PUT `/content/lessons/{slug}`
- DELETE `/content/lessons/{slug}`
