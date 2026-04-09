"""JSON report formatter.

Produces a structured, machine-readable JSON file from a ValidationResult.
This is the primary output format for API consumers and future dashboard.
"""

from __future__ import annotations

import json
from pathlib import Path

from bimoryn.models import ValidationResult


def write_json(result: ValidationResult, output_path: str | Path) -> Path:
    """Serialise ValidationResult to a JSON file.

    The output is the Pydantic model serialised with ISO timestamps
    and enum values as strings.
    """
    out = Path(output_path)
    data = result.model_dump(mode="json")
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def to_json_str(result: ValidationResult) -> str:
    data = result.model_dump(mode="json")
    return json.dumps(data, indent=2, ensure_ascii=False)
