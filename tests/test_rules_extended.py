"""Extended per-rule tests — one positive (fires) + one negative (no false positive) per rule.

Each test builds a minimal IFC model in-memory, injects exactly the defect
the rule checks for, and verifies the rule fires. The clean-model variants
verify the rule is silent on valid data.
"""

from __future__ import annotations

import uuid

import ifcopenshell
import ifcopenshell.api

from bimoryn.engine import Engine, EngineConfig
from bimoryn.rules import REGISTRY


def _guid():
    return ifcopenshell.guid.compress(uuid.uuid4().hex)


def _base_model(schema="IFC4"):
    """Minimal project/site/building/storey scaffold."""
    m = ifcopenshell.file(schema=schema)
    project = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcProject", name="P")
    ifcopenshell.api.run("unit.assign_unit", m)
    site     = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcSite", name="Site")
    building = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcBuilding", name="Bldg")
    storey   = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcBuildingStorey", name="L01")
    ifcopenshell.api.run("aggregate.assign_object", m, relating_object=project, products=[site])
    ifcopenshell.api.run("aggregate.assign_object", m, relating_object=site, products=[building])
    ifcopenshell.api.run("aggregate.assign_object", m, relating_object=building, products=[storey])
    return m


def _run(rule_id, model, tmp_path):
    path = tmp_path / f"{rule_id}.ifc"
    model.write(str(path))
    return Engine(EngineConfig(enabled_rules=[rule_id])).run(path)


def _issues_for(rule_id, model, tmp_path):
    return [i for i in _run(rule_id, model, tmp_path).issues if i.rule_id == rule_id]


# ---------------------------------------------------------------------------
# Registry: 35 rules expected
# ---------------------------------------------------------------------------

def test_registry_has_35_rules():
    assert len(REGISTRY) == 35, f"Expected 35 rules, got {len(REGISTRY)}"


# ---------------------------------------------------------------------------
# GE-002 — Zero-volume wall
# ---------------------------------------------------------------------------

def test_ge002_fires_on_zero_length_wall(tmp_path):
    m = _base_model()
    storey = m.by_type("IfcBuildingStorey")[0]
    wall = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcWall", name="StubWall")
    ifcopenshell.api.run("spatial.assign_container", m, relating_structure=storey, products=[wall])

    # Add Qto_WallBaseQuantities with Length=0
    qset = m.create_entity("IfcElementQuantity", GlobalId=_guid(),
                            Name="Qto_WallBaseQuantities")
    qty = m.create_entity("IfcQuantityLength", Name="Length", LengthValue=0.0)
    qset.Quantities = [qty]
    m.create_entity("IfcRelDefinesByProperties", GlobalId=_guid(),
                    RelatedObjects=[wall], RelatingPropertyDefinition=qset)

    issues = _issues_for("GE-002", m, tmp_path)
    assert len(issues) >= 1


def test_ge002_no_false_positive_on_normal_wall(tmp_path):
    m = _base_model()
    storey = m.by_type("IfcBuildingStorey")[0]
    wall = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcWall", name="W1")
    ifcopenshell.api.run("spatial.assign_container", m, relating_structure=storey, products=[wall])

    qset = m.create_entity("IfcElementQuantity", GlobalId=_guid(),
                            Name="Qto_WallBaseQuantities")
    qty = m.create_entity("IfcQuantityLength", Name="Length", LengthValue=3.5)
    qset.Quantities = [qty]
    m.create_entity("IfcRelDefinesByProperties", GlobalId=_guid(),
                    RelatedObjects=[wall], RelatingPropertyDefinition=qset)

    issues = _issues_for("GE-002", m, tmp_path)
    assert issues == []


# ---------------------------------------------------------------------------
# GE-003 — Uncontained element
# ---------------------------------------------------------------------------

def test_ge003_fires_on_uncontained_wall(tmp_path):
    m = _base_model()
    # Wall added but NOT assigned to any storey
    ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcWall", name="Floating")

    issues = _issues_for("GE-003", m, tmp_path)
    assert len(issues) >= 1


def test_ge003_no_false_positive_on_contained_wall(tmp_path):
    m = _base_model()
    storey = m.by_type("IfcBuildingStorey")[0]
    wall = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcWall", name="W")
    ifcopenshell.api.run("spatial.assign_container", m, relating_structure=storey, products=[wall])

    issues = _issues_for("GE-003", m, tmp_path)
    assert issues == []


# ---------------------------------------------------------------------------
# GE-004 — Duplicate wall placement
# ---------------------------------------------------------------------------

def test_ge004_fires_on_same_placement(tmp_path):
    m = _base_model()
    storey = m.by_type("IfcBuildingStorey")[0]

    def _wall_at_origin(name):
        w = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcWall", name=name)
        ifcopenshell.api.run("spatial.assign_container", m, relating_structure=storey, products=[w])
        # Explicitly place both walls at (0,0,0) so the duplicate-placement rule fires
        origin = m.create_entity("IfcCartesianPoint", Coordinates=[0.0, 0.0, 0.0])
        axis2p = m.create_entity("IfcAxis2Placement3D", Location=origin)
        w.ObjectPlacement = m.create_entity("IfcLocalPlacement", RelativePlacement=axis2p)
        return w

    _wall_at_origin("WA")
    _wall_at_origin("WB")

    issues = _issues_for("GE-004", m, tmp_path)
    assert len(issues) >= 2


# ---------------------------------------------------------------------------
# GE-005 — Orphaned opening
# ---------------------------------------------------------------------------

def test_ge005_fires_on_orphaned_opening(tmp_path):
    m = _base_model()
    # Opening not attached to any wall via IfcRelVoidsElement
    m.create_entity("IfcOpeningElement", GlobalId=_guid(), Name="OrphanVoid")

    issues = _issues_for("GE-005", m, tmp_path)
    assert len(issues) >= 1


def test_ge005_no_false_positive_on_hosted_opening(tmp_path):
    m = _base_model()
    storey = m.by_type("IfcBuildingStorey")[0]
    wall = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcWall", name="W")
    ifcopenshell.api.run("spatial.assign_container", m, relating_structure=storey, products=[wall])

    opening = m.create_entity("IfcOpeningElement", GlobalId=_guid(), Name="V1")
    m.create_entity("IfcRelVoidsElement", GlobalId=_guid(),
                    RelatingBuildingElement=wall, RelatedOpeningElement=opening)

    issues = _issues_for("GE-005", m, tmp_path)
    assert issues == []


# ---------------------------------------------------------------------------
# GE-006 — Missing true north
# ---------------------------------------------------------------------------

def test_ge006_fires_when_no_true_north(tmp_path):
    m = _base_model()
    # _base_model creates a context via context.add_context but TrueNorth is not set
    # Remove any existing contexts to ensure none have TrueNorth
    for ctx in m.by_type("IfcGeometricRepresentationContext"):
        ctx.TrueNorth = None

    issues = _issues_for("GE-006", m, tmp_path)
    assert len(issues) >= 1


# ---------------------------------------------------------------------------
# GE-007 — Element at world origin
# ---------------------------------------------------------------------------

def test_ge007_fires_on_element_at_origin(tmp_path):
    m = _base_model()
    wall = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcWall", name="Ghost")

    # Place wall at (0, 0, 0)
    loc = m.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0))
    axis = m.create_entity("IfcAxis2Placement3D", Location=loc)
    placement = m.create_entity("IfcLocalPlacement", RelativePlacement=axis)
    wall.ObjectPlacement = placement

    issues = _issues_for("GE-007", m, tmp_path)
    assert len(issues) >= 1


def test_ge007_no_false_positive_on_placed_element(tmp_path):
    m = _base_model()
    storey = m.by_type("IfcBuildingStorey")[0]
    wall = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcWall", name="W")
    ifcopenshell.api.run("spatial.assign_container", m, relating_structure=storey, products=[wall])

    loc = m.create_entity("IfcCartesianPoint", Coordinates=(5.0, 3.0, 0.0))
    axis = m.create_entity("IfcAxis2Placement3D", Location=loc)
    placement = m.create_entity("IfcLocalPlacement", RelativePlacement=axis)
    wall.ObjectPlacement = placement

    issues = _issues_for("GE-007", m, tmp_path)
    assert issues == []


# ---------------------------------------------------------------------------
# NM-002 — Space naming convention
# ---------------------------------------------------------------------------

def test_nm002_fires_on_invalid_space_name(tmp_path):
    m = _base_model()
    storey = m.by_type("IfcBuildingStorey")[0]
    space = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcSpace", name="  !!BAD NAME!!")
    ifcopenshell.api.run("aggregate.assign_object", m, products=[space], relating_object=storey)

    issues = _issues_for("NM-002", m, tmp_path)
    assert len(issues) >= 1


def test_nm002_no_false_positive_on_valid_name(tmp_path):
    m = _base_model()
    storey = m.by_type("IfcBuildingStorey")[0]
    space = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcSpace", name="Office-01")
    ifcopenshell.api.run("aggregate.assign_object", m, products=[space], relating_object=storey)

    issues = _issues_for("NM-002", m, tmp_path)
    assert issues == []


# ---------------------------------------------------------------------------
# NM-004 — Duplicate door/window mark
# ---------------------------------------------------------------------------

def test_nm004_fires_on_duplicate_door_mark(tmp_path):
    m = _base_model()
    storey = m.by_type("IfcBuildingStorey")[0]
    for _ in range(2):
        door = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcDoor", name="D-001")
        ifcopenshell.api.run("spatial.assign_container", m, relating_structure=storey, products=[door])

    issues = _issues_for("NM-004", m, tmp_path)
    assert len(issues) >= 2


def test_nm004_no_false_positive_on_unique_marks(tmp_path):
    m = _base_model()
    storey = m.by_type("IfcBuildingStorey")[0]
    for i in range(3):
        door = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcDoor", name=f"D-{i:03d}")
        ifcopenshell.api.run("spatial.assign_container", m, relating_structure=storey, products=[door])

    issues = _issues_for("NM-004", m, tmp_path)
    assert issues == []


# ---------------------------------------------------------------------------
# NM-005 — Storey naming convention
# ---------------------------------------------------------------------------

def test_nm005_fires_on_bad_storey_name(tmp_path):
    m = _base_model()
    bad = m.by_type("IfcBuildingStorey")[0]
    bad.Name = "Floor One"  # doesn't match default pattern

    issues = _issues_for("NM-005", m, tmp_path)
    assert len(issues) >= 1


def test_nm005_no_false_positive_on_l01(tmp_path):
    m = _base_model()
    # L01 is already the storey name in _base_model — should pass
    issues = _issues_for("NM-005", m, tmp_path)
    assert issues == []


# ---------------------------------------------------------------------------
# NM-006 — Generic type name
# ---------------------------------------------------------------------------

def test_nm006_fires_on_generic_name(tmp_path):
    m = _base_model()
    m.create_entity("IfcWallType", GlobalId=_guid(), Name="Basic Wall")

    issues = _issues_for("NM-006", m, tmp_path)
    assert len(issues) >= 1


def test_nm006_no_false_positive_on_named_type(tmp_path):
    m = _base_model()
    m.create_entity("IfcWallType", GlobalId=_guid(), Name="A-EXT-200-BRK")

    issues = _issues_for("NM-006", m, tmp_path)
    assert issues == []


# ---------------------------------------------------------------------------
# NM-007 — Space missing description
# ---------------------------------------------------------------------------

def test_nm007_fires_on_space_without_description(tmp_path):
    m = _base_model()
    storey = m.by_type("IfcBuildingStorey")[0]
    space = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcSpace", name="S-01")
    ifcopenshell.api.run("aggregate.assign_object", m, products=[space], relating_object=storey)

    issues = _issues_for("NM-007", m, tmp_path)
    assert len(issues) >= 1


def test_nm007_no_false_positive_when_longname_set(tmp_path):
    m = _base_model()
    storey = m.by_type("IfcBuildingStorey")[0]
    space = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcSpace", name="S-01")
    space.LongName = "Serverruimte"
    ifcopenshell.api.run("aggregate.assign_object", m, products=[space], relating_object=storey)

    issues = _issues_for("NM-007", m, tmp_path)
    assert issues == []


# ---------------------------------------------------------------------------
# NM-008 — IFC2x3 schema
# ---------------------------------------------------------------------------

def test_nm008_fires_on_ifc2x3(tmp_path):
    m = ifcopenshell.file(schema="IFC2X3")
    # Use create_entity directly to avoid owner-history requirement in ifcopenshell 0.8+
    import uuid as _uuid
    m.create_entity("IfcProject", GlobalId=ifcopenshell.guid.compress(_uuid.uuid4().hex), Name="P")

    issues = _issues_for("NM-008", m, tmp_path)
    assert len(issues) >= 1


def test_nm008_no_false_positive_on_ifc4(tmp_path):
    m = _base_model()  # IFC4
    issues = _issues_for("NM-008", m, tmp_path)
    assert issues == []


# ---------------------------------------------------------------------------
# PM-001 — Wall missing fire rating
# ---------------------------------------------------------------------------

def test_pm001_fires_on_wall_without_fire_rating(tmp_path):
    m = _base_model()
    storey = m.by_type("IfcBuildingStorey")[0]
    wall = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcWall", name="W")
    ifcopenshell.api.run("spatial.assign_container", m, relating_structure=storey, products=[wall])

    issues = _issues_for("PM-001", m, tmp_path)
    assert len(issues) >= 1


def test_pm001_no_false_positive_when_fire_rating_set(tmp_path):
    m = _base_model()
    storey = m.by_type("IfcBuildingStorey")[0]
    wall = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcWall", name="W")
    ifcopenshell.api.run("spatial.assign_container", m, relating_structure=storey, products=[wall])

    pset = ifcopenshell.api.run("pset.add_pset", m, product=wall, name="Pset_WallCommon")
    ifcopenshell.api.run("pset.edit_pset", m, pset=pset, properties={"FireRating": "EI 60"})

    issues = _issues_for("PM-001", m, tmp_path)
    assert issues == []


# ---------------------------------------------------------------------------
# PM-002 — Space missing area
# ---------------------------------------------------------------------------

def test_pm002_fires_on_space_without_area(tmp_path):
    m = _base_model()
    storey = m.by_type("IfcBuildingStorey")[0]
    space = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcSpace", name="Rm")
    ifcopenshell.api.run("aggregate.assign_object", m, products=[space], relating_object=storey)

    issues = _issues_for("PM-002", m, tmp_path)
    assert len(issues) >= 1


# ---------------------------------------------------------------------------
# PM-003 — Structural element missing LoadBearing
# ---------------------------------------------------------------------------

def test_pm003_fires_on_column_without_loadbearing(tmp_path):
    m = _base_model()
    storey = m.by_type("IfcBuildingStorey")[0]
    col = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcColumn", name="C1")
    ifcopenshell.api.run("spatial.assign_container", m, relating_structure=storey, products=[col])

    issues = _issues_for("PM-003", m, tmp_path)
    assert len(issues) >= 1


def test_pm003_no_false_positive_when_loadbearing_set(tmp_path):
    m = _base_model()
    storey = m.by_type("IfcBuildingStorey")[0]
    col = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcColumn", name="C1")
    ifcopenshell.api.run("spatial.assign_container", m, relating_structure=storey, products=[col])

    pset = ifcopenshell.api.run("pset.add_pset", m, product=col, name="Pset_ColumnCommon")
    ifcopenshell.api.run("pset.edit_pset", m, pset=pset, properties={"LoadBearing": True})

    issues = _issues_for("PM-003", m, tmp_path)
    assert issues == []


# ---------------------------------------------------------------------------
# PM-005 — Element not on level
# ---------------------------------------------------------------------------

def test_pm005_fires_on_floating_wall(tmp_path):
    m = _base_model()
    ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcWall", name="Unassigned")

    issues = _issues_for("PM-005", m, tmp_path)
    assert len(issues) >= 1


def test_pm005_no_false_positive_on_assigned_wall(tmp_path):
    m = _base_model()
    storey = m.by_type("IfcBuildingStorey")[0]
    wall = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcWall", name="W")
    ifcopenshell.api.run("spatial.assign_container", m, relating_structure=storey, products=[wall])

    issues = _issues_for("PM-005", m, tmp_path)
    assert issues == []


# ---------------------------------------------------------------------------
# PM-006 — Missing classification
# ---------------------------------------------------------------------------

def test_pm006_fires_on_unclassified_wall(tmp_path):
    m = _base_model()
    storey = m.by_type("IfcBuildingStorey")[0]
    wall = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcWall", name="W")
    ifcopenshell.api.run("spatial.assign_container", m, relating_structure=storey, products=[wall])

    issues = _issues_for("PM-006", m, tmp_path)
    assert len(issues) >= 1


def test_pm006_no_false_positive_when_classified(tmp_path):
    m = _base_model()
    storey = m.by_type("IfcBuildingStorey")[0]
    wall = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcWall", name="W")
    ifcopenshell.api.run("spatial.assign_container", m, relating_structure=storey, products=[wall])

    cl_ref = m.create_entity("IfcClassificationReference",
                              Identification="Ss_20_10", Name="Walls")
    m.create_entity("IfcRelAssociatesClassification", GlobalId=_guid(),
                    RelatedObjects=[wall], RelatingClassification=cl_ref)

    issues = _issues_for("PM-006", m, tmp_path)
    assert issues == []


# ---------------------------------------------------------------------------
# PM-007 — Slab missing thickness
# ---------------------------------------------------------------------------

def test_pm007_fires_on_slab_without_thickness(tmp_path):
    m = _base_model()
    storey = m.by_type("IfcBuildingStorey")[0]
    slab = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcSlab", name="S1")
    ifcopenshell.api.run("spatial.assign_container", m, relating_structure=storey, products=[slab])

    issues = _issues_for("PM-007", m, tmp_path)
    assert len(issues) >= 1


def test_pm007_no_false_positive_when_thickness_set(tmp_path):
    m = _base_model()
    storey = m.by_type("IfcBuildingStorey")[0]
    slab = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcSlab", name="S1")
    ifcopenshell.api.run("spatial.assign_container", m, relating_structure=storey, products=[slab])

    pset = ifcopenshell.api.run("pset.add_pset", m, product=slab, name="Pset_SlabCommon")
    ifcopenshell.api.run("pset.edit_pset", m, pset=pset, properties={"NominalThickness": 200.0})

    issues = _issues_for("PM-007", m, tmp_path)
    assert issues == []


# ---------------------------------------------------------------------------
# PM-008 — Project missing author/organisation
# ---------------------------------------------------------------------------

def test_pm008_fires_when_no_owner_history(tmp_path):
    m = ifcopenshell.file(schema="IFC4")
    m.create_entity("IfcProject", GlobalId=_guid(), Name="NoOwner")
    # No OwnerHistory set

    issues = _issues_for("PM-008", m, tmp_path)
    assert len(issues) >= 1


# ---------------------------------------------------------------------------
# ST-001 — Column not load-bearing
# ---------------------------------------------------------------------------

def test_st001_fires_on_column_no_loadbearing(tmp_path):
    m = _base_model()
    storey = m.by_type("IfcBuildingStorey")[0]
    col = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcColumn", name="C1")
    ifcopenshell.api.run("spatial.assign_container", m, relating_structure=storey, products=[col])

    issues = _issues_for("ST-001", m, tmp_path)
    assert len(issues) >= 1


# ---------------------------------------------------------------------------
# ST-002 — Structural element missing material
# ---------------------------------------------------------------------------

def test_st002_fires_on_beam_without_material(tmp_path):
    m = _base_model()
    storey = m.by_type("IfcBuildingStorey")[0]
    beam = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcBeam", name="B1")
    ifcopenshell.api.run("spatial.assign_container", m, relating_structure=storey, products=[beam])

    issues = _issues_for("ST-002", m, tmp_path)
    assert len(issues) >= 1


def test_st002_no_false_positive_when_material_set(tmp_path):
    m = _base_model()
    storey = m.by_type("IfcBuildingStorey")[0]
    beam = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcBeam", name="B1")
    ifcopenshell.api.run("spatial.assign_container", m, relating_structure=storey, products=[beam])

    mat = ifcopenshell.api.run("material.add_material", m, name="Steel S355")
    ifcopenshell.api.run("material.assign_material", m, products=[beam], material=mat)

    issues = _issues_for("ST-002", m, tmp_path)
    assert issues == []


# ---------------------------------------------------------------------------
# ST-003 — Slab PredefinedType NOTDEFINED
# ---------------------------------------------------------------------------

def test_st003_fires_on_undefined_slab_type(tmp_path):
    m = _base_model()
    storey = m.by_type("IfcBuildingStorey")[0]
    slab = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcSlab", name="S1")
    slab.PredefinedType = "NOTDEFINED"
    ifcopenshell.api.run("spatial.assign_container", m, relating_structure=storey, products=[slab])

    issues = _issues_for("ST-003", m, tmp_path)
    assert len(issues) >= 1


def test_st003_no_false_positive_on_floor_slab(tmp_path):
    m = _base_model()
    storey = m.by_type("IfcBuildingStorey")[0]
    slab = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcSlab", name="S1")
    slab.PredefinedType = "FLOOR"
    ifcopenshell.api.run("spatial.assign_container", m, relating_structure=storey, products=[slab])

    issues = _issues_for("ST-003", m, tmp_path)
    assert issues == []


# ---------------------------------------------------------------------------
# ST-005 — Wall missing IsExternal
# ---------------------------------------------------------------------------

def test_st005_fires_on_wall_without_isexternal(tmp_path):
    m = _base_model()
    storey = m.by_type("IfcBuildingStorey")[0]
    wall = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcWall", name="W")
    ifcopenshell.api.run("spatial.assign_container", m, relating_structure=storey, products=[wall])

    issues = _issues_for("ST-005", m, tmp_path)
    assert len(issues) >= 1


def test_st005_no_false_positive_when_isexternal_set(tmp_path):
    m = _base_model()
    storey = m.by_type("IfcBuildingStorey")[0]
    wall = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcWall", name="W")
    ifcopenshell.api.run("spatial.assign_container", m, relating_structure=storey, products=[wall])

    pset = ifcopenshell.api.run("pset.add_pset", m, product=wall, name="Pset_WallCommon")
    ifcopenshell.api.run("pset.edit_pset", m, pset=pset, properties={"IsExternal": True})

    issues = _issues_for("ST-005", m, tmp_path)
    assert issues == []


# ---------------------------------------------------------------------------
# ST-006 — Wall PredefinedType NOTDEFINED
# ---------------------------------------------------------------------------

def test_st006_fires_on_notdefined_wall(tmp_path):
    m = _base_model()
    storey = m.by_type("IfcBuildingStorey")[0]
    wall = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcWall", name="W")
    wall.PredefinedType = "NOTDEFINED"
    ifcopenshell.api.run("spatial.assign_container", m, relating_structure=storey, products=[wall])

    issues = _issues_for("ST-006", m, tmp_path)
    assert len(issues) >= 1


def test_st006_no_false_positive_on_standard_wall(tmp_path):
    m = _base_model()
    storey = m.by_type("IfcBuildingStorey")[0]
    wall = ifcopenshell.api.run("root.create_entity", m, ifc_class="IfcWall", name="W")
    wall.PredefinedType = "STANDARD"
    ifcopenshell.api.run("spatial.assign_container", m, relating_structure=storey, products=[wall])

    issues = _issues_for("ST-006", m, tmp_path)
    assert issues == []
