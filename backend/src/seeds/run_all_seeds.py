"""
PUBLIC_INTERFACE
Seed Runner - Execute all seed scripts to populate both content and relational data.

This module provides a single entry point to run all seeding logic required for
local development or initial environment bootstrapping.

Usage:
    PYTHONPATH=backend python3 -m src.seeds.run_all_seeds

Behavior:
- Ensures relational tables exist
- Seeds initial subjects, skills (progressive), modules, lessons, activities
- Seeds initial content for /content/* endpoints if present

Notes:
- Idempotent: Seeding can be safely re-run multiple times
- Configuration: Uses environment variables read by backend config
"""
import importlib
import logging
import os
import sys
from typing import List, Tuple

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("seed_runner")


def _import_seed(path: str):
    """
    Dynamically import a module by dotted path. Returns module or raises ImportError.
    """
    return importlib.import_module(path)


def _run_callable(fn, name: str):
    try:
        logger.info("Running seed: %s", name)
        fn()
        logger.info("Completed seed: %s", name)
    except Exception as e:
        logger.exception("Seed failed: %s - %s", name, e)
        raise


# PUBLIC_INTERFACE
def run_all_seeds() -> None:
    """Run all available seeds in a deterministic order.

    - Ensures relational DB tables exist (safe, idempotent)
    - Seeds initial relational data
    - Seeds progressive skills and content if present
    """
    seed_steps: List[Tuple[str, str, str]] = [
        # (module_path, callable_name, human_label)
        ("src.db.table_init", "main", "Initialize relational tables"),
        ("src.seeds.seed_initial_content", "run", "Seed initial relational content"),
        ("src.seeds.seed_progressive_skills", "run", "Seed progressive skills"),
    ]

    # Optional: content seeds for /content/* (Mongo-like). If present, run.
    # The backend README indicates /content/* endpoints exist; the seed file name may vary.
    # We look up a scripts/seed_skills.py for content skills.
    optional_seeds: List[Tuple[str, str, str]] = [
        ("src.scripts.seed_skills", "main", "Seed content skills (Mongo-backed)"),
    ]

    failures = 0

    for module_path, callable_name, label in seed_steps:
        try:
            module = _import_seed(module_path)
            fn = getattr(module, callable_name)
            _run_callable(fn, label)
        except ModuleNotFoundError:
            logger.warning("Seed module not found: %s (skipping)", module_path)
        except AttributeError:
            logger.warning(
                "Seed callable '%s' not found in %s (skipping)", callable_name, module_path
            )
        except Exception:
            failures += 1

    for module_path, callable_name, label in optional_seeds:
        try:
            module = _import_seed(module_path)
            fn = getattr(module, callable_name)
            _run_callable(fn, label)
        except ModuleNotFoundError:
            logger.info("Optional seed module not found: %s (skipping)", module_path)
        except AttributeError:
            logger.info(
                "Optional seed callable '%s' not found in %s (skipping)",
                callable_name,
                module_path,
            )
        except Exception:
            failures += 1

    if failures:
        raise SystemExit(f"Seeding completed with {failures} failure(s).")
    logger.info("All seeds completed successfully.")
    return None


if __name__ == "__main__":
    # Allow invoking directly with python src/seeds/run_all_seeds.py
    # but recommended is module form to ensure PYTHONPATH set.
    try:
        run_all_seeds()
    except SystemExit as e:
        raise
    except Exception as e:
        logger.exception("Seeding crashed: %s", e)
        sys.exit(1)
