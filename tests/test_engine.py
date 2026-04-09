"""Engine integration tests.

These tests run the engine against programmatically-built IFC models
to assert that specific rules fire (or don't fire) correctly.
"""

from __future__ import annotations

import pytest
import ifcopenshell
import ifcopenshell.api

from bimoryn.engine import Engine, EngineConfig
from bimoryn.models import Severity, RuleCategory
from bimoryn.rules import REGISTRY


# ---------------------------------------------------------------------------
# Registry sanity
# ---------------------------------------------------------------------------

def test_registry_has_expected_rule_count():
    assert len(REGISTRY) >= 35, f"Expected >=35 rules, got {len(REGISTRY)}"


def test_all_rules_have_unique_ids():
    ids = [r.id for r in REGISTRY.all_rules()]
    assert len(ids) == len(set(ids)), "Duplicate rule IDs detected"


def test_all_rules_have_required_attributes():
    for rule_cls in REGISTRY.all_rules():
        assert hasattr(rule_cls, "id"),       f"{rule_cls} missing .id"
        assert hasattr(rule_cls, "name"),     f"{rule_cls} missing .name"
        assert hasattr(rule_cls, "category"), f"{rule_cls} missing .category"
        assert hasattr(rule_cls, "severity"), f"{rule_cls} missing .severity"


# ---------------------------------------------------------------------------
# Rule: NM-001 missing element name
# ---------------------------------------------------------------------------

def test_nm001_fires_on_unnamed_wall(model_with_unnamed_wall, tmp_path):
    ifc_path = tmp_path / "test.ifc"
    model_with_unnamed_wall.write(str(ifc_path))

    result = Engine(EngineConfig(enabled_rules=["NM-001"])).run(ifc_path)
    rule_issues = [i for i in result.issues if i.rule_id == "NM-001"]

    assert len(rule_issues) >= 1
    assert all(i.element_type == "IfcWall" for i in rule_issues)


def test_nm001_clean_model_no_false_positives(tmp_path):
    model = ifcopenshell.file(schema="IFC4")
    project = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcProject", name="P")
    ifcopenshell.api.run("unit.assign_unit", model)
    site     = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcSite", name="Site")
    building = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcBuilding", name="Bldg")
    storey   = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcBuildingStorey", name="L01")
    wall     = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcWall", name="EXT-WALL-001")

    ifcopenshell.api.run("aggregate.assign_object", model, relating_object=project, product=site)
    ifcopenshell.api.run("aggregate.assign_object", model, relating_object=site, product=building)
    ifcopenshell.api.run("aggregate.assign_object", model, relating_object=building, product=storey)
    ifcopenshell.api.run("spatial.assign_container", model, relating_structure=storey, product=wall)

    ifc_path = tmp_path / "named.ifc"
    model.write(str(ifc_path))

    result = Engine(EngineConfig(enabled_rules=["NM-001"])).run(ifc_path)
    assert not result.issues, f"Expected no issues, got: {result.issues}"


# ---------------------------------------------------------------------------
# Rule: GE-001 duplicate GlobalId
# ---------------------------------------------------------------------------

def test_ge001_fires_on_duplicate_guid(model_with_duplicate_guid, tmp_path):
    ifc_path = tmp_path / "dup_guid.ifc"
    model_with_duplicate_guid.write(str(ifc_path))

    result = Engine(EngineConfig(enabled_rules=["GE-001"])).run(ifc_path)
    rule_issues = [i for i in result.issues if i.rule_id == "GE-001"]
    assert len(rule_issues) >= 2, "Expected at least 2 issues for 2 elements sharing a GUID"


# ---------------------------------------------------------------------------
# Engine config: disabled rules
# ---------------------------------------------------------------------------

def test_disabled_rules_produce_no_issues(tmp_path):
    model = ifcopenshell.file(schema="IFC4")
    ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcProject", name="P")
    ifcopenshell.api.run("unit.assign_unit", model)

    ifc_path = tmp_path / "empty.ifc"
    model.write(str(ifc_path))

    all_rule_ids = [r.id for r in REGISTRY.all_rules()]
    result = Engine(EngineConfig(disabled_rules=all_rule_ids)).run(ifc_path)
    assert result.issues == [], "All rules disabled — expected zero issues"


# ---------------------------------------------------------------------------
# Engine config: min_severity filter
# ---------------------------------------------------------------------------

def test_min_severity_error_filters_warnings(model_with_unnamed_wall, tmp_path):
    ifc_path = tmp_path / "warn.ifc"
    model_with_unnamed_wall.write(str(ifc_path))

    result = Engine(EngineConfig(min_severity=Severity.ERROR)).run(ifc_path)
    for issue in result.issues:
        assert issue.severity == Severity.ERROR, (
            f"Expected only ERROR issues, got {issue.severity} for {issue.rule_id}"
        )


# ---------------------------------------------------------------------------
# Summary correctness
# ---------------------------------------------------------------------------

def test_summary_counts_match_issues(model_with_unnamed_wall, tmp_path):
    ifc_path = tmp_path / "summary.ifc"
    model_with_unnamed_wall.write(str(ifc_path))

    result = Engine().run(ifc_path)
    s = result.summary

    assert s.total_issues == len(result.issues)
    assert s.errors   == sum(1 for i in result.issues if i.severity == Severity.ERROR)
    assert s.warnings == sum(1 for i in result.issues if i.severity == Severity.WARNING)
    assert s.infos    == sum(1 for i in result.issues if i.severity == Severity.INFO)
    assert s.duration_ms > 0


# ---------------------------------------------------------------------------
# Output: JSON round-trip
# ---------------------------------------------------------------------------

def test_json_output_roundtrip(model_with_unnamed_wall, tmp_path):
    import json
    ifc_path = tmp_path / "rt.ifc"
    model_with_unnamed_wall.write(str(ifc_path))

    result = Engine().run(ifc_path)

    from bimoryn.output.json_report import write_json
    out = tmp_path / "report.json"
    write_json(result, out)

    assert out.exists()
    data = json.loads(out.read_text())
    assert "issues" in data
    assert "summary" in data
    assert data["summary"]["total_issues"] == len(result.issues)


# ---------------------------------------------------------------------------
# Output: BCF zip structure
# ---------------------------------------------------------------------------

def test_bcf_output_is_valid_zip(model_with_unnamed_wall, tmp_path):
    import zipfile
    ifc_path = tmp_path / "bcf_test.ifc"
    model_with_unnamed_wall.write(str(ifc_path))

    result = Engine().run(ifc_path)

    from bimoryn.output.bcf import write_bcf
    out = tmp_path / "issues.bcfzip"
    write_bcf(result, out)

    assert out.exists()
    with zipfile.ZipFile(out) as zf:
        names = zf.namelist()
    assert "bcf.version" in names
    assert "project.bcfp" in names
    # Should have at least one topic folder
    topic_folders = {n.split("/")[0] for n in names if "/" in n}
    assert len(topic_folders) > 0
