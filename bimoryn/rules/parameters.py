"""Parameter completeness rules (PM-001 – PM-007).

Check that elements carry the required property sets and values for
downstream use: cost estimation, energy analysis, FM handover, etc.
"""

from __future__ import annotations

from typing import Iterator

from bimoryn.models import Issue, RuleCategory, RuleConfig, Severity
from bimoryn.rules.base import Rule, register

_CAT = RuleCategory.PARAMETERS


@register
class WallMissingFireRating(Rule):
    """PM-001 — Walls should carry a FireRating property (Pset_WallCommon)."""

    id       = "PM-001"
    name     = "Wall missing fire rating"
    category = _CAT
    severity = Severity.WARNING

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        for wall in model.by_type("IfcWall"):
            if not self._has_pset_value(wall, "Pset_WallCommon", "FireRating"):
                yield self._issue(
                    wall,
                    f"Wall '{wall.Name}' has no FireRating in Pset_WallCommon",
                    detail="Required for fire compartmentation schedules",
                )


@register
class SpaceMissingArea(Rule):
    """PM-002 — IfcSpace must have a quantified area (Qto_SpaceBaseQuantities)."""

    id       = "PM-002"
    name     = "Space missing area quantity"
    category = _CAT
    severity = Severity.ERROR

    _AREA_QSETS = [
        ("Qto_SpaceBaseQuantities", "NetFloorArea"),
        ("Qto_SpaceBaseQuantities", "GrossFloorArea"),
        ("BaseQuantities", "NetFloorArea"),
        ("BaseQuantities", "GrossFloorArea"),
    ]

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        for space in model.by_type("IfcSpace"):
            has_area = any(
                self._has_pset_value(space, qset, prop)
                for qset, prop in self._AREA_QSETS
            )
            # Also check IfcElementQuantity
            if not has_area:
                has_area = self._check_quantity_set(space)
            if not has_area:
                yield self._issue(
                    space,
                    f"Space '{space.Name}' has no floor area quantity",
                    detail="Required for room schedules and area take-offs",
                )

    def _check_quantity_set(self, element) -> bool:
        for rel in getattr(element, "IsDefinedBy", []):
            if not rel.is_a("IfcRelDefinesByProperties"):
                continue
            pdef = rel.RelatingPropertyDefinition
            if pdef.is_a("IfcElementQuantity"):
                for qty in pdef.Quantities:
                    if "area" in qty.Name.lower():
                        return True
        return False


@register
class ElementMissingLoadBearing(Rule):
    """PM-003 — Structural elements must declare LoadBearing flag."""

    id       = "PM-003"
    name     = "Structural element missing LoadBearing property"
    category = _CAT
    severity = Severity.WARNING

    _STRUCTURAL_TYPES = ("IfcWall", "IfcSlab", "IfcColumn", "IfcBeam", "IfcMember", "IfcFooting")
    _PSETS = ("Pset_WallCommon", "Pset_SlabCommon", "Pset_ColumnCommon",
              "Pset_BeamCommon", "Pset_MemberCommon", "Pset_FootingCommon")

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        for ifc_type, pset in zip(self._STRUCTURAL_TYPES, self._PSETS):
            for el in model.by_type(ifc_type):
                if not self._has_pset_value(el, pset, "LoadBearing"):
                    yield self._issue(
                        el,
                        f"{el.is_a()} '{el.Name}' missing LoadBearing in {pset}",
                        detail="Required for structural coordination",
                    )


@register
class DoorMissingHardwareSet(Rule):
    """PM-004 — Doors should carry a hardware set / hardware group reference."""

    id       = "PM-004"
    name     = "Door missing hardware set reference"
    category = _CAT
    severity = Severity.INFO

    _HARDWARE_PROPS = [
        ("Pset_DoorCommon", "HandicapAccessible"),  # proxy for detailed spec
        ("Pset_DoorCommon", "IsExternal"),
    ]

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        for door in model.by_type("IfcDoor"):
            # Check for any custom hardware pset by searching prop names
            psets = self._all_psets(door)
            has_hardware = any(
                "hardware" in pset_name.lower() or "ironmongery" in pset_name.lower()
                for pset_name in psets
            )
            if not has_hardware:
                yield self._issue(
                    door,
                    f"Door '{door.Name}' has no hardware/ironmongery property set",
                    detail="Required for door schedules and specification",
                )


@register
class ElementNotOnLevel(Rule):
    """PM-005 — Every physical element must be contained in a building storey.

    Unhosted elements won't appear in level-based schedules or clash detection
    by storey.
    """

    id       = "PM-005"
    name     = "Element not assigned to a building storey"
    category = _CAT
    severity = Severity.ERROR

    _PHYSICAL_TYPES = (
        "IfcWall", "IfcSlab", "IfcColumn", "IfcBeam", "IfcDoor", "IfcWindow",
        "IfcStair", "IfcRamp", "IfcRoof", "IfcFurnishingElement",
        "IfcDistributionElement",
    )

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        # Build set of GUIDs that ARE contained in a spatial structure
        contained: set[str] = set()
        for rel in model.by_type("IfcRelContainedInSpatialStructure"):
            for el in rel.RelatedElements:
                contained.add(el.GlobalId)

        for ifc_type in self._PHYSICAL_TYPES:
            for el in model.by_type(ifc_type):
                if el.GlobalId not in contained:
                    yield self._issue(
                        el,
                        f"{el.is_a()} '{el.Name}' is not assigned to any building storey",
                        detail="Assign via IfcRelContainedInSpatialStructure",
                    )


@register
class MissingClassification(Rule):
    """PM-006 — Elements should carry at least one classification reference.

    Checks for IfcRelAssociatesClassification relationships.
    Common systems: OmniClass, Uniclass 2015, ETIM, NBS.
    """

    id       = "PM-006"
    name     = "Element missing classification reference"
    category = _CAT
    severity = Severity.INFO

    _CHECK_TYPES = (
        "IfcWall", "IfcSlab", "IfcColumn", "IfcBeam", "IfcDoor", "IfcWindow",
        "IfcSpace", "IfcDistributionElement",
    )

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        # Build mapping from element GUID -> has classification
        classified: set[str] = set()
        for rel in model.by_type("IfcRelAssociatesClassification"):
            for obj in rel.RelatedObjects:
                classified.add(obj.GlobalId)

        for ifc_type in self._CHECK_TYPES:
            for el in model.by_type(ifc_type):
                if el.GlobalId not in classified:
                    yield self._issue(
                        el,
                        f"{el.is_a()} '{el.Name}' has no classification reference",
                        detail="Assign OmniClass, Uniclass, or equivalent",
                    )


@register
class SlabMissingThickness(Rule):
    """PM-007 — IfcSlab elements must declare a nominal thickness."""

    id       = "PM-007"
    name     = "Slab missing thickness"
    category = _CAT
    severity = Severity.WARNING

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        for slab in model.by_type("IfcSlab"):
            has = (
                self._has_pset_value(slab, "Pset_SlabCommon", "NominalThickness")
                or self._has_pset_value(slab, "Qto_SlabBaseQuantities", "Depth")
                or self._has_pset_value(slab, "BaseQuantities", "Depth")
            )
            if not has:
                yield self._issue(
                    slab,
                    f"Slab '{slab.Name}' has no nominal thickness",
                    detail="Required for structural analysis and material take-offs",
                )


@register
class ProjectMissingAuthorOrganisation(Rule):
    """PM-008 — IfcProject OwnerHistory must carry author and organisation.

    ISO 19650 and the NL BIM Norm require model authorship metadata for
    audit trails, federated delivery, and handover packages.
    """

    id       = "PM-008"
    name     = "IfcProject missing author/organisation"
    category = _CAT
    severity = Severity.WARNING

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        projects = model.by_type("IfcProject")
        if not projects:
            return
        project = projects[0]
        oh = getattr(project, "OwnerHistory", None)
        if oh is None:
            yield self._issue(
                project,
                "IfcProject has no OwnerHistory — author and organisation unknown",
                detail="Set company information in your authoring tool before IFC export",
            )
            return

        person = getattr(oh, "OwningUser", None)
        org = getattr(oh, "OwningApplication", None) or getattr(oh, "OwningOrganization", None)

        person_name = ""
        if person is not None:
            actor = getattr(person, "ThePerson", None) or person
            person_name = (
                getattr(actor, "Identification", None)
                or getattr(actor, "FamilyName", None)
                or ""
            )

        org_name = ""
        if org is not None:
            org_entity = getattr(org, "ApplicationDeveloper", None) or org
            org_name = getattr(org_entity, "Name", None) or ""

        if not person_name and not org_name:
            yield self._issue(
                project,
                "IfcProject OwnerHistory has no identifiable author or organisation",
                detail="Configure company name and user identity in your authoring tool",
            )
