from __future__ import annotations

from typing import Any, Optional

try:
    from bson import ObjectId  # type: ignore
except Exception:  # pragma: no cover - defensive import for environments without bson
    ObjectId = None  # type: ignore


# PUBLIC_INTERFACE
def to_str_id(value: Any) -> Optional[str]:
    """Convert an ObjectId or any truthy value to a string id.

    Returns:
        Optional[str]: Stringified id or None if input is falsy or not convertible.
    """
    if value is None:
        return None
    try:
        # If bson is available and value is ObjectId
        if ObjectId is not None and isinstance(value, ObjectId):  # type: ignore[arg-type]
            return str(value)
        return str(value)
    except Exception:
        return None
