"""Naming convention rules (NM-001 – NM-007).

Checks that element names, type names, space names, and level names meet
the expected conventions. Most pilots have their own naming standards;
these defaults are based on ISO 19650 and common UK/EU practice.
Override patterns via rule config params.
"""

from __future__ import annotations

import re
from typing import Iterator

from bimoryn.models import Issue, RuleCategory, RuleConfig, Severity
from bimoryn.rules.base import Rule, register

_CAT = RuleCategory.NAMING

# Default discipline prefixes expected in type names (configurable)
_DEFAULT_DISCIPLINE_PREFIXES = {"A-", "S-", "M-", "E-", "P-", "C-", "L-"}

# IFC element types that must have non-empty Name
_NAMED_TYPES = (
    "IfcWall", "IfcSlab", "IfcColumn", "IfcBeam", "IfcDoor", "IfcWindow",
    "IfcSpace", "IfcStair", "IfcRamp", "IfcRoof",
    "IfcDistributionElement", "IfcBuildingElementProxy",
)


@register
class MissingElementName(Rule):
    """NM-001 — Named elements must have a non-empty Name attribute."""

    id       = "NM-001"
    name     = "Missing element name"
    category = _CAT
    severity = Severity.WARNING

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        for ifc_type in _NAMED_TYPES:
            for el in model.by_type(ifc_type):
                if not el.Name or not el.Name.strip():
                    yield self._issue(
                        el,
                        f"{el.is_a()} has no Name value",
                        detail=f"GlobalId={el.GlobalId}",
                    )


@register
class SpaceNamingConvention(Rule):
    """NM-002 — Space names must match the configured pattern.

    Default pattern: one or more word-chars + optional dash/underscore/number.
    Rejects names with leading/trailing whitespace, special chars, or blank.
    """

    id       = "NM-002"
    name     = "Space name does not match convention"
    category = _CAT
    severity = Severity.WARNING

    _DEFAULT_PATTERN = r"^[\w][\w\-/ ]{0,49}$"

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        pattern = re.compile(config.params.get("pattern", self._DEFAULT_PATTERN))
        for space in model.by_type("IfcSpace"):
            name = (space.Name or "").strip()
            if not name:
                yield self._issue(space, "IfcSpace has no name", severity=Severity.ERROR)
            elif not pattern.match(name):
                yield self._issue(
                    space,
                    f"Space name '{name}' does not match naming convention",
                    detail=f"Pattern: {pattern.pattern}",
                )


@register
class TypeNameDisciplinePrefix(Rule):
    """NM-003 — IfcTypeObject names should carry a discipline prefix.

    Helps distinguish architectural vs structural vs MEP types at a glance.
    Controlled via config param ``prefixes`` (list of allowed prefixes).
    """

    id       = "NM-003"
    name     = "Type name missing discipline prefix"
    category = _CAT
    severity = Severity.INFO

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        allowed = set(config.params.get("prefixes", list(_DEFAULT_DISCIPLINE_PREFIXES)))
        for obj_type in model.by_type("IfcTypeObject"):
            name = (obj_type.Name or "").strip()
            if not name:
                continue  # caught by NM-001 if applicable
            has_prefix = any(name.startswith(p) for p in allowed)
            if not has_prefix:
                yield self._issue(
                    obj_type,
                    f"Type '{name}' is missing a discipline prefix",
                    detail=f"Expected one of: {', '.join(sorted(allowed))}",
                )


@register
class DuplicateDoorWindowMark(Rule):
    """NM-004 — Door and window marks must be unique within the model."""

    id       = "NM-004"
    name     = "Duplicate door/window mark"
    category = _CAT
    severity = Severity.ERROR

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        seen: dict[str, list] = {}
        for el in [*model.by_type("IfcDoor"), *model.by_type("IfcWindow")]:
            tag = getattr(el, "Tag", None) or getattr(el, "Name", None)
            if not tag:
                continue
            seen.setdefault(tag, []).append(el)

        for mark, elements in seen.items():
            if len(elements) > 1:
                for el in elements:
                    yield self._issue(
                        el,
                        f"Mark '{mark}' is used by {len(elements)} elements",
                        detail=f"GUIDs: {', '.join(e.GlobalId for e in elements)}",
                    )


@register
class LevelNamingConvention(Rule):
    """NM-005 — Building storey names must follow a recognisable floor pattern.

    Accepted by default: B2, B1, GF, L01-L99, RF (roof), M01 (mezzanine), etc.
    Configurable via ``pattern`` param.
    """

    id       = "NM-005"
    name     = "Building storey name does not match convention"
    category = _CAT
    severity = Severity.WARNING

    _DEFAULT_PATTERN = r"^(B\d+|GF|L\d{1,2}|RF|M\d{1,2}|UG|SB|P\d{1,2}|Ground|Basement|Roof)$"

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        pattern = re.compile(
            config.params.get("pattern", self._DEFAULT_PATTERN),
            re.IGNORECASE,
        )
        for storey in model.by_type("IfcBuildingStorey"):
            name = (storey.Name or "").strip()
            if not name:
                yield self._issue(storey, "Building storey has no name", severity=Severity.ERROR)
            elif not pattern.match(name):
                yield self._issue(
                    storey,
                    f"Storey name '{name}' does not match convention",
                    detail=f"Pattern: {pattern.pattern}",
                )


@register
class GenericDefaultTypeName(Rule):
    """NM-006 — Element type names that look like Revit/ArchiCAD defaults should be renamed.

    Flags names matching known default patterns (e.g. 'Basic Wall', 'Generic - 200mm',
    'Default', 'Standard', '<unnamed>').
    """

    id       = "NM-006"
    name     = "Generic / default type name detected"
    category = _CAT
    severity = Severity.WARNING

    _GENERIC_PATTERNS = [
        re.compile(r"^(Basic|Generic|Default|Standard|Unnamed|New\s)", re.IGNORECASE),
        re.compile(r"^\<"),          # <unnamed>, <By Category>
        re.compile(r"^\d+mm$"),      # "200mm" with no qualifier
    ]

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        for obj_type in model.by_type("IfcTypeObject"):
            name = (obj_type.Name or "").strip()
            if not name:
                continue
            for pat in self._GENERIC_PATTERNS:
                if pat.search(name):
                    yield self._issue(
                        obj_type,
                        f"Type name '{name}' appears to be an unrenamed default",
                    )
                    break


@register
class MissingSpaceDescription(Rule):
    """NM-007 — IfcSpace should have a LongName or Description for room-book use."""

    id       = "NM-007"
    name     = "Space missing long name / description"
    category = _CAT
    severity = Severity.INFO

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        for space in model.by_type("IfcSpace"):
            long = getattr(space, "LongName", None)
            desc = getattr(space, "Description", None)
            if not long and not desc:
                yield self._issue(
                    space,
                    f"Space '{space.Name}' has no LongName or Description",
                    detail="Required for room schedules and handover documentation",
                )


@register
class IFC2x3SchemaVersion(Rule):
    """NM-008 — IFC2x3 schema is deprecated; IFC4 is the current standard.

    Several BIMoryn rules have reduced or zero coverage on IFC2x3 models.
    This is an INFO — flag to the user so they can consider re-exporting.
    """

    id       = "NM-008"
    name     = "IFC schema version is IFC2x3"
    category = _CAT
    severity = Severity.INFO

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        schema = getattr(model, "schema", "") or ""
        if "2X3" in schema.upper() or "2x3" in schema:
            projects = model.by_type("IfcProject")
            target = projects[0] if projects else None
            yield self._issue(
                target,
                f"Model uses IFC schema '{schema}' — IFC4 is recommended",
                detail="Re-export using IFC4 for full BIMoryn rule coverage",
            )
