# SkillMaster Backend

FastAPI backend for the SkillMaster micro skill-based learning platform.

## Relational Data Seeding

This repository includes an idempotent seeding utility to populate Subjects → Modules → Lessons → Activities/Quizzes.

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
- Upsert subjects, modules, lessons, activities and quizzes
- Be safe to re-run without creating duplicates

2) Automatic on FastAPI startup
Set the environment variable:
```
SEED_RELATIONAL_DATA=true
```
Then start your API server as usual. On startup, it will:
- Ensure tables exist
- Run the same idempotent seeding logic

Notes:
- The seed script relies on the relational models and SQLAlchemy session already configured in `src/db/sqlalchemy.py` and `src/db/relational_models.py`.
- The seeding content includes:
  - Subjects: Programming, Data Science, System Architecture, Soft Skills, Creative Tech
  - Each subject has several modules
  - Each module includes 1–2 lessons with 1–2 activities (content/video/coding)
  - Each lesson has a short quiz (3 questions)

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

A relational schema is provided for Subjects → Modules → Lessons → Activities/Quiz and Progress.
Create the tables locally (uses SQLALCHEMY_DATABASE_URL or defaults to SQLite):

```bash
python -m src.db.table_init
```

This is idempotent and safe to run repeatedly.

## SQLAlchemy & Drivers

- The project uses SQLAlchemy 2.x with a synchronous engine (`create_engine`) in `src/db/sqlalchemy.py`.
- Default DB URL is SQLite (sync) `sqlite:///./skillmaster.db` so no extra SQLite driver is required beyond stdlib.
- For Postgres in production, set `SQLALCHEMY_DATABASE_URL=postgresql+psycopg2://...` and ensure `psycopg2-binary` is installed (pinned in requirements).
- Async drivers (`aiosqlite`, `asyncpg`) are included for potential future async migration; current code uses sync sessions.

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

Troubleshooting:
- If you see `ModuleNotFoundError: No module named 'jwt'`, verify PyJWT is installed: `python -c "import jwt; print(jwt.__version__)"`
- MongoDB deps: motor 3.6.0 requires `pymongo < 4.10 and >= 4.9`. We pin `pymongo==4.9.2`.
