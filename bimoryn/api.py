"""BIMoryn REST API.

Exposes the validation engine over HTTP for programmatic pilot integration.

Endpoints:
    POST /validate   — upload IFC file, receive structured validation report
    GET  /rules      — list all active rules with descriptions and severity
    GET  /health     — liveness check

Authentication:
    Authorization: Bearer <BIMORYN_API_KEY>
    Set BIMORYN_API_KEY env var. If unset, auth is disabled (local/dev mode).

Run:
    uvicorn bimoryn.api:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from bimoryn.engine import Engine
from bimoryn.models import RuleCategory, Severity, ValidationResult
from bimoryn.output.json_report import to_json_str
from bimoryn.rules import REGISTRY

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="BIMoryn Validation API",
    description=(
        "Rule-based BIM validation engine. "
        "Upload an IFC file and receive a structured QA report."
    ),
    version="0.1.0",
    contact={"name": "BIMoryn", "email": "hello@bimoryn.com"},
    license_info={"name": "Proprietary"},
)

_engine = Engine()


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

_API_KEY = os.environ.get("BIMORYN_API_KEY", "")


async def _require_auth(authorization: Annotated[str | None, Header()] = None) -> None:
    """Validate Bearer token. Skipped when BIMORYN_API_KEY is not set (dev mode)."""
    if not _API_KEY:
        return  # auth disabled — local/dev mode
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Unauthorized", "code": "AUTH_MISSING", "details": "Authorization header required"},
        )
    token = authorization[len("Bearer "):]
    if token != _API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "Forbidden", "code": "AUTH_INVALID", "details": "Invalid API key"},
        )


_Auth = Annotated[None, Depends(_require_auth)]


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str
    version: str
    rules_loaded: int


class RuleInfo(BaseModel):
    id: str
    name: str
    category: RuleCategory
    severity: Severity
    description: str


class RulesResponse(BaseModel):
    count: int
    rules: list[RuleInfo]


class ErrorResponse(BaseModel):
    error: str
    code: str
    details: str | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rule_description(rule_cls: type) -> str:
    """Extract first docstring line from rule class, falling back to name."""
    doc = getattr(rule_cls, "__doc__", None) or ""
    first_line = doc.strip().split("\n")[0].strip()
    return first_line or rule_cls.name


def _error(status_code: int, error: str, code: str, details: str | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": error, "code": code, "details": details},
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness check",
    tags=["system"],
)
async def health() -> HealthResponse:
    """Returns 200 when the API is running. No auth required."""
    return HealthResponse(
        status="ok",
        version=app.version,
        rules_loaded=len(REGISTRY),
    )


@app.get(
    "/rules",
    response_model=RulesResponse,
    summary="List all active validation rules",
    tags=["rules"],
    dependencies=[Depends(_require_auth)],
)
async def list_rules() -> RulesResponse:
    """Return all registered rules with id, name, category, severity, and description."""
    rules = REGISTRY.all_rules()
    return RulesResponse(
        count=len(rules),
        rules=[
            RuleInfo(
                id=r.id,
                name=r.name,
                category=r.category,
                severity=r.severity,
                description=_rule_description(r),
            )
            for r in sorted(rules, key=lambda r: r.id)
        ],
    )


@app.post(
    "/validate",
    summary="Validate an IFC file",
    tags=["validation"],
    dependencies=[Depends(_require_auth)],
    responses={
        200: {"description": "Validation report (BCF-compatible JSON)"},
        400: {"model": ErrorResponse, "description": "Invalid or missing IFC file"},
        422: {"model": ErrorResponse, "description": "File processing error"},
    },
)
async def validate(
    file: Annotated[UploadFile, File(description="IFC file to validate (.ifc)")],
) -> Any:
    """
    Upload a `.ifc` file and receive a full validation report.

    The response is a `ValidationResult` JSON object identical to the CLI output.
    Use `summary.errors` and `summary.warnings` to gate downstream workflows.
    """
    # --- basic sanity checks ---
    if not file.filename:
        return _error(400, "Bad Request", "FILE_MISSING", "No file uploaded")
    if not file.filename.lower().endswith(".ifc"):
        return _error(400, "Bad Request", "FILE_TYPE", "Only .ifc files are accepted")

    content = await file.read()
    if not content:
        return _error(400, "Bad Request", "FILE_EMPTY", "Uploaded file is empty")

    # --- write to temp file so ifcopenshell can open it ---
    tmp_suffix = f"_{uuid.uuid4().hex}.ifc"
    with tempfile.NamedTemporaryFile(suffix=tmp_suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        result: ValidationResult = _engine.run(tmp_path)
    except FileNotFoundError as exc:
        return _error(422, "Unprocessable Entity", "FILE_NOT_FOUND", str(exc))
    except Exception as exc:
        return _error(422, "Unprocessable Entity", "PARSE_ERROR", str(exc))
    finally:
        tmp_path.unlink(missing_ok=True)

    # Return same structure as CLI JSON output
    return JSONResponse(
        content=result.model_dump(mode="json"),
        media_type="application/json",
    )
