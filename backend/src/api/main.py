from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.errors import ApplicationError, application_error_handler, generic_error_handler
from src.api.routers import lessons as lessons_router
from src.api.routers import progress as progress_router
from src.api.routers import skills as skills_router
from src.config import get_config
from src.repositories.memory_repository import InMemoryRepository

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

# Register routers
app.include_router(skills_router.router)
app.include_router(lessons_router.router)
app.include_router(progress_router.router)

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
