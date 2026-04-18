"""BIMoryn validation engine.

Core loop:  IFC file  →  rules  →  issues  →  ValidationResult

Usage::

    from bimoryn.engine import Engine

    result = Engine().run("path/to/model.ifc")
    print(result.summary)
"""

from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any

import ifcopenshell

from bimoryn.models import (
    Issue,
    RuleConfig,
    Severity,
    ValidationResult,
    ValidationSummary,
)
from bimoryn.rules import REGISTRY
from bimoryn.rules.base import Rule


class EngineConfig:
    """Runtime configuration for an engine run.

    Parameters
    ----------
    enabled_rules:
        Explicit list of rule IDs to run. ``None`` means all registered rules.
    disabled_rules:
        Rule IDs to skip. Applied after ``enabled_rules``.
    rule_configs:
        Per-rule config overrides keyed by rule ID.
    min_severity:
        Only emit issues at this severity or higher
        (ERROR > WARNING > INFO).
    """

    _SEVERITY_RANK = {Severity.INFO: 0, Severity.WARNING: 1, Severity.ERROR: 2}

    def __init__(
        self,
        enabled_rules:  list[str] | None = None,
        disabled_rules: list[str] | None = None,
        rule_configs:   dict[str, dict[str, Any]] | None = None,
        min_severity:   Severity = Severity.INFO,
    ) -> None:
        self.enabled_rules  = set(enabled_rules)  if enabled_rules  else None
        self.disabled_rules = set(disabled_rules) if disabled_rules else set()
        self.rule_configs   = rule_configs or {}
        self.min_severity   = min_severity

    def rule_config_for(self, rule_id: str) -> RuleConfig:
        overrides = self.rule_configs.get(rule_id, {})
        return RuleConfig(**overrides)

    def passes_severity(self, severity: Severity) -> bool:
        return (
            self._SEVERITY_RANK[severity]
            >= self._SEVERITY_RANK[self.min_severity]
        )


class Engine:
    """Stateless validation engine.

    Create once, call ``run()`` as many times as needed.
    """

    def __init__(self, config: EngineConfig | None = None) -> None:
        self._cfg = config or EngineConfig()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, model_path: str | Path) -> ValidationResult:
        """Validate an IFC file. Returns a ValidationResult."""
        path = Path(model_path)
        started = time.monotonic()

        model = self._load(path)
        issues = list(self._run_rules(model))
        elapsed_ms = (time.monotonic() - started) * 1000

        # Filter by min_severity
        issues = [i for i in issues if self._cfg.passes_severity(i.severity)]

        summary = ValidationSummary(
            total_elements = self._count_elements(model),
            total_issues   = len(issues),
            errors         = sum(1 for i in issues if i.severity == Severity.ERROR),
            warnings       = sum(1 for i in issues if i.severity == Severity.WARNING),
            infos          = sum(1 for i in issues if i.severity == Severity.INFO),
            rules_run      = len(self._active_rules()),
            duration_ms    = round(elapsed_ms, 1),
        )

        return ValidationResult(
            run_id       = str(uuid.uuid4()),
            model_path   = str(path),
            schema       = model.schema_identifier,
            project_name = self._project_name(model),
            summary      = summary,
            issues       = issues,
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _load(self, path: Path) -> ifcopenshell.file:
        if not path.exists():
            raise FileNotFoundError(f"IFC file not found: {path}")
        return ifcopenshell.open(str(path))

    def _active_rules(self) -> list[type[Rule]]:
        rules = REGISTRY.all_rules()
        if self._cfg.enabled_rules is not None:
            rules = [r for r in rules if r.id in self._cfg.enabled_rules]
        rules = [r for r in rules if r.id not in self._cfg.disabled_rules]
        return rules

    def _run_rules(self, model: ifcopenshell.file):
        for rule_cls in self._active_rules():
            rule_cfg = self._cfg.rule_config_for(rule_cls.id)
            if not rule_cfg.enabled:
                continue
            rule = rule_cls(config=rule_cfg)
            try:
                yield from rule.check(model, rule_cfg)
            except Exception as exc:  # rule must never crash the engine
                yield Issue(
                    rule_id      = rule_cls.id,
                    rule_name    = rule_cls.name,
                    category     = rule_cls.category,
                    severity     = Severity.ERROR,
                    message      = f"Rule '{rule_cls.id}' raised an unexpected error",
                    detail       = str(exc),
                )

    def _count_elements(self, model: ifcopenshell.file) -> int:
        return len(list(model.by_type("IfcProduct")))

    def _project_name(self, model: ifcopenshell.file) -> str | None:
        projects = model.by_type("IfcProject")
        if projects:
            return getattr(projects[0], "Name", None) or getattr(projects[0], "LongName", None)
        return None
