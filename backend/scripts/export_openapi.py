"""
Export OpenAPI JSON schema from Legal-Lens Docket API.
Mounts api_v1_router cleanly without loading heavy ML dependencies.
"""

import json
import os
import sys
from fastapi import FastAPI

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.api.v1 import api_v1_router  # noqa: E402


def export_openapi(output_path: str) -> None:
    app = FastAPI(
        title="LegalLens Docket API",
        version="1.0.0",
        description="Comprehensive Hearing and Deadline Reminder API",
    )
    app.include_router(api_v1_router, prefix="/api/v1")
    schema = app.openapi()

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
    print(
        f"Exported OpenAPI schema ({len(schema['paths'])} endpoints) to {output_path}"
    )


if __name__ == "__main__":
    out = (
        sys.argv[1]
        if len(sys.argv) > 1
        else os.path.join(
            os.path.dirname(__file__), "..", "..", "frontend", "openapi.json"
        )
    )
    export_openapi(out)
