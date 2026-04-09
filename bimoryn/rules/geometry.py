"""Geometry and spatial integrity rules (GE-001 – GE-006).

Some checks require extracting geometry via ifcopenshell.geom; those are
clearly marked. Checks that only need property/attribute data run without
the geometry kernel and are fast even on large models.
"""

from __future__ import annotations

from collections import Counter
from typing import Iterator

from bimoryn.models import Issue, RuleCategory, RuleConfig, Severity
from bimoryn.rules.base import Rule, register

_CAT = RuleCategory.GEOMETRY

# Minimum wall length in metres below which we flag as a stub/error
_DEFAULT_MIN_WALL_LENGTH_M = 0.05  # 50 mm


@register
class DuplicateGlobalId(Rule):
    """GE-001 — Every element must have a unique GlobalId (GUID).

    Duplicate GUIDs corrupt BCF references, clash detection, and model merges.
    This is an ERROR — a model with duplicate GUIDs is fundamentally broken.
    """

    id       = "GE-001"
    name     = "Duplicate GlobalId (GUID)"
    category = _CAT
    severity = Severity.ERROR

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        counts: Counter[str] = Counter()
        guid_to_elements: dict[str, list] = {}

        for el in model.by_type("IfcRoot"):
            guid = el.GlobalId
            counts[guid] += 1
            guid_to_elements.setdefault(guid, []).append(el)

        for guid, count in counts.items():
            if count > 1:
                for el in guid_to_elements[guid]:
                    yield self._issue(
                        el,
                        f"GlobalId '{guid}' is shared by {count} elements",
                        detail="GUIDs must be globally unique — regenerate affected elements",
                    )


@register
class ZeroVolumeWall(Rule):
    """GE-002 — Walls must have non-zero length reported via quantity sets.

    Checks Qto_WallBaseQuantities.Length; skips if no quantity set is present
    (that's flagged by a parameter rule). Only fires when Length == 0.
    """

    id       = "GE-002"
    name     = "Wall has zero or near-zero length"
    category = _CAT
    severity = Severity.ERROR

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        min_len = float(config.params.get("min_length_m", _DEFAULT_MIN_WALL_LENGTH_M))
        for wall in model.by_type("IfcWall"):
            length = self._get_quantity(wall, "Qto_WallBaseQuantities", "Length")
            if length is None:
                length = self._get_quantity(wall, "BaseQuantities", "Length")
            if length is not None and float(length) < min_len:
                yield self._issue(
                    wall,
                    f"Wall '{wall.Name}' length {length:.4f}m is below minimum {min_len}m",
                    detail="May be a modelling artefact — review or delete",
                )

    def _get_quantity(self, element, qset_name: str, qty_name: str):
        for rel in getattr(element, "IsDefinedBy", []):
            if not rel.is_a("IfcRelDefinesByProperties"):
                continue
            pdef = rel.RelatingPropertyDefinition
            if not pdef.is_a("IfcElementQuantity"):
                continue
            if pdef.Name != qset_name:
                continue
            for qty in pdef.Quantities:
                if qty.Name == qty_name:
                    return getattr(qty, "LengthValue", None)
        return None


@register
class UncontainedElement(Rule):
    """GE-003 — Physical elements must be spatially contained.

    Elements not in any IfcRelContainedInSpatialStructure won't appear
    in storey-based views, schedules, or model federation workflows.
    (Overlaps with PM-005 but catches non-physical element types too.)
    """

    id       = "GE-003"
    name     = "Element has no spatial containment"
    category = _CAT
    severity = Severity.WARNING

    _PHYSICAL_TYPES = (
        "IfcElement",   # broad catch — covers all physical elements
    )

    # Exclude pure annotation / 2D types
    _EXCLUDE_TYPES = {
        "IfcAnnotation", "IfcGrid", "IfcVirtualElement",
        "IfcSpatialElement", "IfcSpatialStructureElement",
    }

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        contained: set[str] = set()
        for rel in model.by_type("IfcRelContainedInSpatialStructure"):
            for el in rel.RelatedElements:
                contained.add(el.GlobalId)

        aggregated: set[str] = set()
        for rel in model.by_type("IfcRelAggregates"):
            for el in rel.RelatedObjects:
                aggregated.add(el.GlobalId)

        for el in model.by_type("IfcElement"):
            if el.is_a() in self._EXCLUDE_TYPES:
                continue
            if el.GlobalId not in contained and el.GlobalId not in aggregated:
                yield self._issue(
                    el,
                    f"{el.is_a()} '{el.Name}' is not spatially contained or aggregated",
                )


@register
class OverlappingWallsSameStorey(Rule):
    """GE-004 — Detect walls with identical start/end points on the same storey.

    Uses the ObjectPlacement origin as a proxy (full geometry not required).
    Identical placement usually means a copy-paste duplication.
    """

    id       = "GE-004"
    name     = "Duplicate wall placement detected"
    category = _CAT
    severity = Severity.WARNING

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        placement_map: dict[tuple, list] = {}

        for wall in model.by_type("IfcWall"):
            origin = self._get_placement_origin(wall)
            if origin is None:
                continue
            # Round to 3 decimal places (mm precision)
            key = tuple(round(v, 3) for v in origin)
            placement_map.setdefault(key, []).append(wall)

        for origin_key, walls in placement_map.items():
            if len(walls) > 1:
                for wall in walls:
                    yield self._issue(
                        wall,
                        f"Wall shares placement origin {origin_key} with {len(walls)-1} other wall(s)",
                        detail="Possible duplicated wall — verify and remove one",
                    )

    def _get_placement_origin(self, element) -> tuple[float, float, float] | None:
        try:
            placement = element.ObjectPlacement
            if placement is None:
                return None
            local = getattr(placement, "RelativePlacement", None)
            if local is None:
                return None
            loc = getattr(local, "Location", None)
            if loc is None:
                return None
            coords = loc.Coordinates
            return (float(coords[0]), float(coords[1]), float(coords[2]))
        except Exception:
            return None


@register
class OpeningWithoutHost(Rule):
    """GE-005 — IfcOpeningElement must be embedded in a host element.

    An orphaned opening has no effect and indicates a modelling error
    (e.g. a door/window was deleted but its void was left behind).
    """

    id       = "GE-005"
    name     = "Opening element has no host"
    category = _CAT
    severity = Severity.WARNING

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        hosted: set[str] = set()
        for rel in model.by_type("IfcRelVoidsElement"):
            hosted.add(rel.RelatedOpeningElement.GlobalId)

        for opening in model.by_type("IfcOpeningElement"):
            if opening.GlobalId not in hosted:
                yield self._issue(
                    opening,
                    "IfcOpeningElement has no host element (orphaned void)",
                    detail="Delete the orphaned opening or re-attach to a wall/slab",
                )


@register
class MissingProjectNorth(Rule):
    """GE-006 — The IfcProject should declare true north via IfcGeometricRepresentationContext.

    Without true north the model cannot be correctly oriented in site coordination
    or energy analysis workflows.
    """

    id       = "GE-006"
    name     = "Project true north not defined"
    category = _CAT
    severity = Severity.INFO

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        projects = model.by_type("IfcProject")
        if not projects:
            return

        project = projects[0]
        has_true_north = False

        for context in model.by_type("IfcGeometricRepresentationContext"):
            if getattr(context, "TrueNorth", None) is not None:
                has_true_north = True
                break

        if not has_true_north:
            yield self._issue(
                project,
                "No TrueNorth defined in any IfcGeometricRepresentationContext",
                detail="Required for correct site orientation and solar analysis",
            )


@register
class ElementAtWorldOrigin(Rule):
    """GE-007 — Elements placed exactly at (0, 0, 0) are almost always mis-exported.

    In federated models all such elements pile up at the site origin, breaking
    visual coordination and clash detection. This is a WARNING; survey equipment
    and project base point markers are exempt (they are IfcSpatialElement subtypes).
    """

    id       = "GE-007"
    name     = "Element placed at world origin (0,0,0)"
    category = _CAT
    severity = Severity.WARNING

    _EXEMPT_TYPES = {
        "IfcSpatialElement", "IfcSpatialStructureElement",
        "IfcSite", "IfcBuilding", "IfcBuildingStorey",
    }

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        for el in model.by_type("IfcElement"):
            if el.is_a() in self._EXEMPT_TYPES:
                continue
            origin = self._get_placement_origin(el)
            if origin is not None and origin == (0.0, 0.0, 0.0):
                yield self._issue(
                    el,
                    f"{el.is_a()} '{el.Name}' is placed at world origin (0,0,0)",
                    detail="Verify element placement or remove ghost objects",
                )

    def _get_placement_origin(self, element) -> tuple[float, float, float] | None:
        try:
            placement = element.ObjectPlacement
            if placement is None:
                return None
            local = getattr(placement, "RelativePlacement", None)
            if local is None:
                return None
            loc = getattr(local, "Location", None)
            if loc is None:
                return None
            coords = loc.Coordinates
            return (float(coords[0]), float(coords[1]), float(coords[2]))
        except Exception:
            return None
