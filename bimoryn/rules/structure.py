"""Structural integrity rules (ST-001 – ST-005)."""

from __future__ import annotations

from typing import Iterator

from bimoryn.models import Issue, RuleCategory, RuleConfig, Severity
from bimoryn.rules.base import Rule, register

_CAT = RuleCategory.STRUCTURE


@register
class ColumnMissingStructuralRole(Rule):
    """ST-001 — IfcColumn must carry LoadBearing=True in Pset_ColumnCommon.

    A column that isn't flagged as load-bearing will be excluded from
    structural analysis exports and cost schedules.
    """

    id       = "ST-001"
    name     = "Column not flagged as load-bearing"
    category = _CAT
    severity = Severity.WARNING

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        for col in model.by_type("IfcColumn"):
            val = self._get_pset_value(col, "Pset_ColumnCommon", "LoadBearing")
            if val is None:
                yield self._issue(
                    col,
                    f"Column '{col.Name}' has no LoadBearing property",
                    detail="Set LoadBearing=True in Pset_ColumnCommon",
                )
            elif hasattr(val, "wrappedValue"):
                if not val.wrappedValue:
                    yield self._issue(
                        col,
                        f"Column '{col.Name}' is marked LoadBearing=False",
                        detail="Verify — most columns are structural",
                        severity=Severity.INFO,
                    )


@register
class BeamMissingMaterial(Rule):
    """ST-002 — Beams and columns must have a material assignment.

    Without a material, structural analysis and quantity take-offs
    for steel/concrete tonnage are impossible.
    """

    id       = "ST-002"
    name     = "Structural element missing material"
    category = _CAT
    severity = Severity.ERROR

    _STRUCTURAL_TYPES = ("IfcBeam", "IfcColumn", "IfcMember", "IfcFooting")

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        # Build set of GUIDs that have material associations
        has_material: set[str] = set()
        for rel in model.by_type("IfcRelAssociatesMaterial"):
            for obj in rel.RelatedObjects:
                has_material.add(obj.GlobalId)

        for ifc_type in self._STRUCTURAL_TYPES:
            for el in model.by_type(ifc_type):
                if el.GlobalId not in has_material:
                    yield self._issue(
                        el,
                        f"{el.is_a()} '{el.Name}' has no material association",
                        detail="Required for structural analysis and material scheduling",
                    )


@register
class SlabMissingStructuralFunction(Rule):
    """ST-003 — Slabs must declare their PredefinedType.

    FLOOR, ROOF, LANDING, BASESLAB each have different structural
    implications; NOTDEFINED will cause issues in analysis tools.
    """

    id       = "ST-003"
    name     = "Slab PredefinedType is NOTDEFINED or missing"
    category = _CAT
    severity = Severity.WARNING

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        for slab in model.by_type("IfcSlab"):
            ptype = getattr(slab, "PredefinedType", None)
            if ptype is None or str(ptype) in ("NOTDEFINED", "USERDEFINED", "None"):
                yield self._issue(
                    slab,
                    f"Slab '{slab.Name}' PredefinedType is '{ptype}' — set FLOOR/ROOF/LANDING/BASESLAB",
                )


@register
class FoundationMissingDepth(Rule):
    """ST-004 — IfcFooting should carry a depth/embedment quantity.

    Without depth information, foundation design cannot be verified and
    excavation quantities cannot be computed.
    """

    id       = "ST-004"
    name     = "Foundation missing depth quantity"
    category = _CAT
    severity = Severity.WARNING

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        for footing in model.by_type("IfcFooting"):
            has_depth = (
                self._has_pset_value(footing, "Qto_FootingBaseQuantities", "Depth")
                or self._has_pset_value(footing, "BaseQuantities", "Depth")
                or self._has_pset_value(footing, "Pset_FootingCommon", "NominalDepth")
            )
            if not has_depth:
                yield self._issue(
                    footing,
                    f"Footing '{footing.Name}' has no depth quantity",
                    detail="Required for earthworks and structural design verification",
                )


@register
class WallMissingIsExternal(Rule):
    """ST-005 — Walls must declare IsExternal (Pset_WallCommon).

    Exterior/interior distinction drives thermal analysis, façade
    schedules, and access control modelling.
    """

    id       = "ST-005"
    name     = "Wall missing IsExternal property"
    category = _CAT
    severity = Severity.WARNING

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        for wall in model.by_type("IfcWall"):
            if not self._has_pset_value(wall, "Pset_WallCommon", "IsExternal"):
                yield self._issue(
                    wall,
                    f"Wall '{wall.Name}' has no IsExternal property in Pset_WallCommon",
                    detail="Required for thermal bridging and energy analysis",
                )


@register
class WallPredefinedTypeNotDefined(Rule):
    """ST-006 — IfcWall.PredefinedType should be set to a meaningful value.

    NOTDEFINED prevents automated classification in structural and architectural
    analysis tools. Accepted values: STANDARD, POLYGONAL, SHEAR, PARTITIONING,
    PLUMBINGWALL, MOVABLE, SOLIDWALL, ELEMENTEDWALL.
    """

    id       = "ST-006"
    name     = "Wall PredefinedType is NOTDEFINED"
    category = _CAT
    severity = Severity.WARNING

    _UNDEFINED = {"NOTDEFINED", "USERDEFINED", "None", ""}

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        for wall in model.by_type("IfcWall"):
            ptype = getattr(wall, "PredefinedType", None)
            ptype_str = str(ptype) if ptype is not None else "None"
            if ptype_str in self._UNDEFINED:
                yield self._issue(
                    wall,
                    f"Wall '{wall.Name}' PredefinedType is '{ptype_str}'",
                    detail="Set to STANDARD, PARTITIONING, SHEAR, or appropriate type",
                )
