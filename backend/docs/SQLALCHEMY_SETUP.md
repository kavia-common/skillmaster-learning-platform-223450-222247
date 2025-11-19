# SQLAlchemy Setup Notes

This service imports from `src.db.sqlalchemy` and `src.db.relational_models`. Ensure the following are set:

- `DATABASE_URL` in `.env` (see `.env.example`) using an async driver:
  - SQLite: `sqlite+aiosqlite:///./skillmaster.db`
  - Postgres: `postgresql+asyncpg://USER:PASSWORD@HOST:5432/DBNAME`

Installed deps:
- SQLAlchemy 2.x
- aiosqlite (async SQLite)
- asyncpg (async Postgres)
- psycopg2-binary (optional for sync tooling)

No secrets are hardcoded; configuration is via environment variables.
