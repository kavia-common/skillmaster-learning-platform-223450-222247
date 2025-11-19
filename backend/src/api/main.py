from typing import Any, Dict
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from src.api.errors import ApplicationError, application_error_handler, generic_error_handler
from src.api.routers import lessons as lessons_router
from src.api.routers import progress as progress_router
from src.api.routers import skills as skills_router
from src.api.routers import catalog as catalog_router
from src.api.routes import relational as relational_router
from src.api.routers.skill_progressive import router as progressive_skills_router
from src.config import get_config
from src.repositories.memory_repository import InMemoryRepository
from src.db.mongo import init_mongo, close_mongo

# Initialize app with metadata for OpenAPI/Swagger
app = FastAPI(
    title="SkillMaster Backend",
    description="Backend API for SkillMaster micro skill-based learning platform.",
    version="0.1.0",
    openapi_tags=[
        {"name": "Health", "description": "Service health and diagnostics"},
        {"name": "Skills", "description": "Skills, modules and lessons catalog"},
        {"name": "Lessons", "description": "Per-module lessons browsing"},
        {"name": "Progress", "description": "User progress tracking"},
        {"name": "Internal", "description": "Internal utilities"},
        {"name": "Relational", "description": "Relational CRUD for Subjects → Modules → Lessons → Activities/Quiz and Progress"},
    ],
)

# Initialize in-memory repositories and config at startup
config = get_config()
repositories = {"default": InMemoryRepository()}

# Expose repos on app.state for later dependency injection
app.state.repositories = repositories  # type: ignore[attr-defined]
app.state.config = config  # type: ignore[attr-defined]

# Configure CORS based on environment; use explicit origins when credentials are enabled
allow_origins = []
# Always include localhost:3000 for local dev UI
allow_origins.append("http://localhost:3000")
if config.frontend_url:
    allow_origins.append(config.frontend_url)
# Dedupe and filter empties
allow_origins = sorted({o.rstrip("/") for o in allow_origins if o})

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,  # required so browser can send cookies/credentials
    allow_methods=["*"],
    allow_headers=["*"],
)
print("[CORS] allow_origins:", allow_origins, "allow_credentials=True")

# Lifespan events for Mongo + relational schema + optional seeding
@app.on_event("startup")
async def _on_startup() -> None:
    # Dependency/import sanity checks with guidance logs
    try:
        import sqlalchemy  # noqa: F401
    except Exception as e:
        print("[Startup][WARNING] SQLAlchemy not available. Ensure dependencies are installed. Error:", e)

    db_url = os.getenv("SQLALCHEMY_DATABASE_URL")
    if not db_url:
        print("[Startup][INFO] No SQLALCHEMY_DATABASE_URL set. Defaulting to SQLite at sqlite:///./skillmaster.db")
    else:
        if db_url.startswith("postgresql+psycopg2"):
            try:
                import psycopg2  # noqa: F401
            except Exception:
                print("[Startup][WARNING] Postgres URL detected but psycopg2-binary not importable.")

    try:
        await init_mongo()
    except Exception:
        pass

    try:
        from src.db.table_init import create_all_tables
        await create_all_tables()
    except Exception as e:
        print("[Startup][WARNING] Relational table initialization skipped due to error:", e)

    try:
        if os.getenv("SEED_RELATIONAL_DATA", "false").lower() == "true":
            from src.db.sqlalchemy import get_session_factory
            from src.seeds.seed_initial_content import seed_initial_content

            SessionFactory = get_session_factory()
            with SessionFactory() as session:
                seed_initial_content(session)
    except Exception as e:
        print("[Startup][WARNING] Relational data seeding skipped due to error:", e)


@app.on_event("shutdown")
async def _on_shutdown() -> None:
    try:
        await close_mongo()
    except Exception:
        pass


# Register routers
# Existing skills (Mongo-backed content) routes
app.include_router(skills_router.router)
# New progressive relational skills routes
app.include_router(progressive_skills_router)
# Other routes
app.include_router(lessons_router.router)
app.include_router(progress_router.router)
app.include_router(catalog_router.router)  # Mongo content
app.include_router(relational_router.router)  # Relational CRUD

# Error handlers
app.add_exception_handler(ApplicationError, application_error_handler)
app.add_exception_handler(Exception, generic_error_handler)


@app.get("/", tags=["Health"], summary="Health Check", description="Returns a simple health check response.")
def health_check() -> Dict[str, Any]:
    """Health check endpoint.

    Returns:
        JSON response with a message and basic configuration indicators.
    """
    return {
        "message": "Healthy",
        "env": config.node_env,
        "features": config.feature_flags,
        "cors": {
            "allow_origins": app.user_middleware[0].options.get("allow_origins", []) if app.user_middleware else [],
            "allow_credentials": True,
        },
    }


# PUBLIC_INTERFACE
@app.get(
    "/__backend_help",
    response_class=HTMLResponse,
    tags=["Health"],
    summary="Backend Help",
    description="Quick links and environment diagnostics for local development and E2E checks.",
)
def backend_help() -> HTMLResponse:
    """Developer helper page with links to common GET endpoints and seed trigger."""
    frontend = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
    api_base = os.getenv("BACKEND_URL", "http://localhost:3001").rstrip("/")
    html = f"""
    <html><body style="font-family: system-ui; padding: 16px;">
      <h1>SkillMaster Backend Help</h1>
      <p>Frontend origin: <code>{frontend}</code></p>
      <p>API base: <code>{api_base}</code></p>
      <h2>Quick links</h2>
      <ul>
        <li><a href="/docs" target="_blank">/docs</a></li>
        <li><a href="/" target="_blank">/ (health)</a></li>
        <li><a href="/skills" target="_blank">/skills</a></li>
        <li><a href="/content/skills" target="_blank">/content/skills</a></li>
        <li><a href="/subjects" target="_blank">/subjects</a></li>
        <li><a href="/modules?subject_id=1" target="_blank">/modules?subject_id=1</a></li>
        <li><a href="/lessons?module_id=1" target="_blank">/lessons?module_id=1</a></li>
        <li><a href="/__run_seeds" target="_blank">/__run_seeds</a> (run seeds)</li>
      </ul>
      <h2>CORS</h2>
      <p>Ensure CORS allows origin <code>{frontend}</code> with <code>allow_credentials=True</code>.</p>
      <h2>Seeding</h2>
      <p>Run seeds once to populate data:</p>
      <pre>PYTHONPATH=backend python3 -m src.seeds.run_all_seeds</pre>
    </body></html>
    """
    return HTMLResponse(content=html, status_code=200)


# PUBLIC_INTERFACE
@app.get(
    "/__run_seeds",
    tags=["Internal"],
    summary="Run all seeds",
    description="Synchronously execute src.seeds.run_all_seeds to populate relational data for local development.",
)
def run_seeds_endpoint() -> JSONResponse:
    """Invoke the seeding routine synchronously for local/dev convenience."""
    try:
        from src.seeds.run_all_seeds import run_all_seeds
        run_all_seeds()
        return JSONResponse({"ok": True, "message": "Seeds completed"}, status_code=200)
    except SystemExit as e:
        return JSONResponse({"ok": False, "message": f"Seeds exited: {e}"}, status_code=500)
    except Exception as e:
        return JSONResponse({"ok": False, "message": f"Error: {e}"}, status_code=500)
