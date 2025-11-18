"""Minimal JWT auth stubs: public GET is open; admin-only for mutations.

For this pass, verification is lenient and can be extended later.
"""

from __future__ import annotations

import os
from typing import Optional

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


bearer_scheme = HTTPBearer(auto_error=False)


# PUBLIC_INTERFACE
def get_jwt_secret() -> Optional[str]:
    """Return JWT secret from environment or None if unset."""
    return os.getenv("JWT_SECRET")


# PUBLIC_INTERFACE
def require_admin(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> None:
    """Authorization dependency requiring an 'admin' role in JWT.

    Behavior:
    - If JWT_SECRET is not set, raise 503 to signal misconfiguration for protected endpoints.
    - If token missing or invalid/role!=admin, raise 401/403.
    """
    secret = get_jwt_secret()
    if not secret:
        raise HTTPException(status_code=503, detail="JWT not configured")

    if creds is None or not creds.credentials:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = creds.credentials
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        role = payload.get("role", "user")
        if role != "admin":
            raise HTTPException(status_code=403, detail="Admin role required")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
