"""Utility to generate and write the FastAPI OpenAPI schema to interfaces/openapi.json.

Run with:
    python -m src.api.generate_openapi

This imports the FastAPI app without altering runtime settings and writes app.openapi()
output into the backend interfaces directory for clients and documentation consumers.
"""

import json
import os

from src.api.main import app


# PUBLIC_INTERFACE
def generate_openapi_to_file() -> str:
    """Generate the OpenAPI JSON and write it to interfaces/openapi.json.

    Returns:
        str: The absolute path of the written openapi.json file.
    """
    openapi_schema = app.openapi()

    output_dir = "interfaces"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "openapi.json")

    with open(output_path, "w") as f:
        json.dump(openapi_schema, f, indent=2)

    # Return absolute path for logging/verification
    return os.path.abspath(output_path)


if __name__ == "__main__":
    path = generate_openapi_to_file()
    print(f"Wrote OpenAPI schema to: {path}")
