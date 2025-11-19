from typing import Any, Dict
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.errors import ApplicationError, application_error_handler, generic_error_handler
from src.api.routers import lessons as lessons_router
from src.api.routers import progress as progress_router
from src.api.routers import skills as skills_router
from src.api.routers import catalog as catalog_router
from src.api.routes import relational as relational_router
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

# Configure CORS based on environment; default to permissive for dev
allow_origins = ["*"]
if config.frontend_url:
    allow_origins = [config.frontend_url]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lifespan events for Mongo + relational schema + optional seeding
@app.on_event("startup")
async def _on_startup() -> None:
    # Initialize Mongo if env configured; if not, let seed/use log meaningful errors when needed
    try:
        await init_mongo()
    except Exception:
        # Start without Mongo; public in-memory endpoints still function
        pass
    # Ensure relational tables exist (idempotent)
    try:
        from src.db.table_init import create_all_tables
        await create_all_tables()
    except Exception:
        # Do not crash app if DB isn't configured; endpoints will surface errors when used
        pass

    # Optionally run relational data seeding when enabled by env var
    try:
        if os.getenv("SEED_RELATIONAL_DATA", "false").lower() == "true":
            from src.db.sqlalchemy import get_session_factory
            from src.seeds.seed_initial_content import seed_initial_content

            SessionFactory = get_session_factory()
            with SessionFactory() as session:
                seed_initial_content(session)
    except Exception:
        # Seeding is optional; avoid crashing on startup in constrained envs
        pass


@app.on_event("shutdown")
async def _on_shutdown() -> None:
    try:
        await close_mongo()
    except Exception:
        pass


# Register routers
app.include_router(skills_router.router)
app.include_router(lessons_router.router)
app.include_router(progress_router.router)
# New content routes backed by MongoDB
app.include_router(catalog_router.router)
# Relational CRUD routes
app.include_router(relational_router.router)

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
    }
