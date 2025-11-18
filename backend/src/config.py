"""Application configuration and feature flags.

Loads environment variables and exposes a Config object for use across the app.
Uses python-dotenv if present to support local development via a .env file.

Note: Do not hardcode any secrets. All configuration must come from the environment.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

try:
    # python-dotenv is included in requirements; safe to load if .env exists
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()  # Load .env when running locally
except Exception:
    # If python-dotenv isn't available for some reason in runtime, continue
    pass


class Config:
    """Application runtime configuration loaded from environment variables."""

    def __init__(self) -> None:
        self.node_env: str = os.getenv("REACT_APP_NODE_ENV", "development")
        self.backend_url: Optional[str] = os.getenv("REACT_APP_BACKEND_URL")
        self.frontend_url: Optional[str] = os.getenv("REACT_APP_FRONTEND_URL")
        self.ws_url: Optional[str] = os.getenv("REACT_APP_WS_URL")
        self.port: int = int(os.getenv("REACT_APP_PORT", "3001"))
        self.trust_proxy: bool = os.getenv("REACT_APP_TRUST_PROXY", "false").lower() == "true"
        self.log_level: str = os.getenv("REACT_APP_LOG_LEVEL", "info")
        self.healthcheck_path: str = os.getenv("REACT_APP_HEALTHCHECK_PATH", "/")
        self.experiments_enabled: bool = os.getenv("REACT_APP_EXPERIMENTS_ENABLED", "false").lower() == "true"

        # Feature flags can be provided as JSON string or comma-separated flags
        features_raw = os.getenv("REACT_APP_FEATURE_FLAGS", "{}")
        self.feature_flags: Dict[str, Any] = self._parse_feature_flags(features_raw)

    def _parse_feature_flags(self, value: str) -> Dict[str, Any]:
        """Parse feature flags from either JSON or comma-separated key[:value] pairs."""
        # Try JSON first
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

        # Fallback: comma-separated list like "flagA,flagB=true,flagC=42"
        flags: Dict[str, Any] = {}
        for part in [p.strip() for p in value.split(",") if p.strip()]:
            if "=" in part:
                k, v = part.split("=", 1)
                k = k.strip()
                v = v.strip()
                if v.lower() in ("true", "false"):
                    flags[k] = v.lower() == "true"
                else:
                    # Attempt to parse numeric, else keep as string
                    try:
                        flags[k] = int(v)
                    except ValueError:
                        try:
                            flags[k] = float(v)
                        except ValueError:
                            flags[k] = v
            else:
                flags[part] = True
        return flags


# Singleton-like config for import convenience
# PUBLIC_INTERFACE
def get_config() -> Config:
    """Return the application configuration singleton.

    Ensures a single instance is created per process.
    """
    global _CONFIG_INSTANCE  # type: ignore  # module-level global
    try:
        return _CONFIG_INSTANCE  # type: ignore
    except NameError:
        _CONFIG_INSTANCE = Config()  # type: ignore
        return _CONFIG_INSTANCE  # type: ignore
