"""Data contracts for BIMoryn validation engine.

All public surface area is versioned here. Downstream consumers (CLI, API,
BCF exporter) depend only on these types — never on internal engine state.
"""

from __future__ import annotations

from enum import Enum
from typing import Any
from datetime import datetime, timezone

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Severity(str, Enum):
    """Issue severity, mapped to BCF priority levels."""
    ERROR   = "error"    # Model cannot be used as-is (e.g. duplicate GUIDs)
    WARNING = "warning"  # Violates standard, needs review
    INFO    = "info"     # Advisory, improve quality


class RuleCategory(str, Enum):
    NAMING      = "naming"
    PARAMETERS  = "parameters"
    GEOMETRY    = "geometry"
    STRUCTURE   = "structure"
    MEP         = "mep"


class IssueStatus(str, Enum):
    OPEN     = "open"
    RESOLVED = "resolved"
    WAIVED   = "waived"


# ---------------------------------------------------------------------------
# Issue — one finding from one rule against one element
# ---------------------------------------------------------------------------

class IssueLocation(BaseModel):
    """Spatial location hint for BCF viewpoint. All coordinates in metres."""
    x: float | None = None
    y: float | None = None
    z: float | None = None


class Issue(BaseModel):
    rule_id:      str            = Field(description="Stable rule identifier, e.g. 'NM-001'")
    rule_name:    str
    category:     RuleCategory
    severity:     Severity
    element_guid: str | None    = Field(None, description="IFC GlobalId of offending element")
    element_type: str | None    = Field(None, description="IFC entity class, e.g. 'IfcWall'")
    element_name: str | None    = None
    message:      str           = Field(description="Human-readable description of the problem")
    detail:       str | None    = Field(None, description="Extra context, actual vs expected value")
    location:     IssueLocation | None = None
    status:       IssueStatus   = IssueStatus.OPEN


# ---------------------------------------------------------------------------
# Validation run — top-level result object
# ---------------------------------------------------------------------------

class ValidationSummary(BaseModel):
    total_elements: int
    total_issues:   int
    errors:         int
    warnings:       int
    infos:          int
    rules_run:      int
    duration_ms:    float


class ValidationResult(BaseModel):
    """Output contract. Everything downstream consumes this."""
    run_id:       str
    model_path:   str
    schema:       str | None   = Field(None, description="IFC schema version, e.g. IFC4")
    project_name: str | None   = None
    started_at:   datetime     = Field(default_factory=lambda: datetime.now(timezone.utc))
    summary:      ValidationSummary
    issues:       list[Issue]  = Field(default_factory=list)
    metadata:     dict[str, Any] = Field(default_factory=dict)

    def issues_by_severity(self, severity: Severity) -> list[Issue]:
        return [i for i in self.issues if i.severity == severity]

    def issues_by_category(self, category: RuleCategory) -> list[Issue]:
        return [i for i in self.issues if i.category == category]


# ---------------------------------------------------------------------------
# Rule config — passed to each rule at init time
# ---------------------------------------------------------------------------

class RuleConfig(BaseModel):
    """Per-rule configuration. Rules declare their defaults; overridden by user config."""
    enabled:  bool            = True
    severity: Severity | None = None   # override default severity
    params:   dict[str, Any]  = Field(default_factory=dict)
