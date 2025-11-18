"""FastAPI dependencies and common utilities for injecting repositories and config."""

from typing import Annotated

from fastapi import Depends, Request

from src.config import Config
from src.repositories.memory_repository import InMemoryRepository, ProgressRepository, SkillRepository


# PUBLIC_INTERFACE
def get_config_dep(request: Request) -> Config:
    """Return the application configuration stored on app.state."""
    return request.app.state.config  # type: ignore[attr-defined]


# PUBLIC_INTERFACE
def get_repository_dep(request: Request) -> InMemoryRepository:
    """Return the default in-memory repository from app.state."""
    # In this prototype we have a single repo implementing both interfaces.
    return request.app.state.repositories["default"]  # type: ignore[attr-defined]


# Aliases typed for clarity in route signatures
ConfigDep = Annotated[Config, Depends(get_config_dep)]
RepoDep = Annotated[InMemoryRepository, Depends(get_repository_dep)]
SkillRepoDep = Annotated[SkillRepository, Depends(get_repository_dep)]
ProgressRepoDep = Annotated[ProgressRepository, Depends(get_repository_dep)]
