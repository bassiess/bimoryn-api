"""Pytest fixtures — builds minimal in-memory IFC models for testing.

Uses ifcopenshell's API to construct models programmatically so tests
never depend on checked-in binary files.
"""

from __future__ import annotations

import uuid
import pytest
import ifcopenshell
import ifcopenshell.api


def _guid() -> str:
    return ifcopenshell.guid.compress(uuid.uuid4().hex)


@pytest.fixture
def minimal_model() -> ifcopenshell.file:
    """An IFC4 model with one project, one site, one building, one storey."""
    model = ifcopenshell.file(schema="IFC4")
    project = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcProject", name="TestProject")
    ifcopenshell.api.run("unit.assign_unit", model)

    context = ifcopenshell.api.run("context.add_context", model, context_type="Model")

    site     = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcSite", name="Site")
    building = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcBuilding", name="Building")
    storey   = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcBuildingStorey", name="L01")

    ifcopenshell.api.run("aggregate.assign_object", model, relating_object=project,  product=site)
    ifcopenshell.api.run("aggregate.assign_object", model, relating_object=site,     product=building)
    ifcopenshell.api.run("aggregate.assign_object", model, relating_object=building, product=storey)

    return model


@pytest.fixture
def model_with_unnamed_wall(minimal_model) -> ifcopenshell.file:
    """Adds a wall with no Name — should trigger NM-001."""
    model = minimal_model
    wall = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcWall", name="")
    storey = model.by_type("IfcBuildingStorey")[0]
    ifcopenshell.api.run("spatial.assign_container", model, relating_structure=storey, product=wall)
    return model


@pytest.fixture
def model_with_duplicate_guid(minimal_model) -> ifcopenshell.file:
    """Two walls sharing a GlobalId — should trigger GE-001."""
    model = minimal_model
    storey = model.by_type("IfcBuildingStorey")[0]

    shared_guid = _guid()
    wall1 = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcWall", name="Wall-A")
    wall2 = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcWall", name="Wall-B")

    # Force same GlobalId on both — this is intentionally invalid
    wall1.GlobalId = shared_guid
    wall2.GlobalId = shared_guid

    for w in [wall1, wall2]:
        ifcopenshell.api.run("spatial.assign_container", model, relating_structure=storey, product=w)

    return model


@pytest.fixture
def model_clean(minimal_model) -> ifcopenshell.file:
    """A model designed to pass all geometry checks — no issues expected from GE rules."""
    return minimal_model
