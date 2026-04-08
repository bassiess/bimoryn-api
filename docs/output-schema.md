# BIMoryn JSON Output Schema

Version: 0.1.0
Format: `bimoryn validate model.ifc --output report.json --format json`

---

## Top-level object: `ValidationResult`

```json
{
  "run_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "model_path": "/path/to/model.ifc",
  "schema": "IFC4",
  "project_name": "My Building Project",
  "started_at": "2026-04-08T14:32:00.000Z",
  "summary": { ... },
  "issues": [ ... ],
  "metadata": {}
}
```

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | string (UUID) | Unique identifier for this validation run |
| `model_path` | string | Absolute path to the IFC file that was validated |
| `schema` | string \| null | IFC schema version detected, e.g. `"IFC4"`, `"IFC2X3"` |
| `project_name` | string \| null | Name from the `IfcProject` entity, if present |
| `started_at` | string (ISO 8601) | UTC timestamp when the run started |
| `summary` | object | Aggregate counts — see below |
| `issues` | array | List of findings — see below |
| `metadata` | object | Reserved for future use (empty in v0.1) |

---

## `summary` object

```json
{
  "total_elements": 142,
  "total_issues": 23,
  "errors": 5,
  "warnings": 12,
  "infos": 6,
  "rules_run": 31,
  "duration_ms": 54.0
}
```

| Field | Type | Description |
|-------|------|-------------|
| `total_elements` | integer | Count of `IfcProduct` entities in the model |
| `total_issues` | integer | Total issues at or above `min_severity` threshold |
| `errors` | integer | Count of `severity = "error"` issues |
| `warnings` | integer | Count of `severity = "warning"` issues |
| `infos` | integer | Count of `severity = "info"` issues |
| `rules_run` | integer | Number of rules executed in this run |
| `duration_ms` | number | Wall-clock time for the full run in milliseconds |

---

## `issues` array — each item: `Issue`

```json
{
  "rule_id": "NM-001",
  "rule_name": "Missing element name",
  "category": "naming",
  "severity": "warning",
  "element_guid": "0LV6XKx81D2PoBP2bNen7C",
  "element_type": "IfcWall",
  "element_name": null,
  "message": "IfcWall has no Name value",
  "detail": "GlobalId=0LV6XKx81D2PoBP2bNen7C",
  "location": null,
  "status": "open"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `rule_id` | string | Stable rule code, e.g. `"NM-001"`. Never changes between versions. |
| `rule_name` | string | Human-readable rule name |
| `category` | string (enum) | Rule category — see values below |
| `severity` | string (enum) | `"error"` \| `"warning"` \| `"info"` |
| `element_guid` | string \| null | IFC `GlobalId` of the offending element |
| `element_type` | string \| null | IFC entity class, e.g. `"IfcWall"`, `"IfcSpace"` |
| `element_name` | string \| null | `Name` attribute of the offending element (may be null) |
| `message` | string | Short, actionable description of the problem |
| `detail` | string \| null | Extra context — actual vs expected value, property set names, etc. |
| `location` | object \| null | Spatial coordinates for BCF viewpoints — see below |
| `status` | string (enum) | `"open"` \| `"resolved"` \| `"waived"` |

### `category` values

| Value | Rules |
|-------|-------|
| `"naming"` | NM-001 – NM-007 |
| `"parameters"` | PM-001 – PM-007 |
| `"geometry"` | GE-001 – GE-006 |
| `"structure"` | ST-001 – ST-005 |
| `"mep"` | ME-001 – ME-006 |

### `severity` values

| Value | Meaning |
|-------|---------|
| `"error"` | Model cannot be used as-is — must be fixed before downstream use |
| `"warning"` | Violates standard or best practice — review required |
| `"info"` | Advisory — improves quality but not blocking |

### `location` object (when present)

```json
{
  "x": 12.5,
  "y": 3.0,
  "z": 0.0
}
```

All coordinates are in **metres**, relative to the IFC world coordinate system. Used to generate BCF viewpoints. Will be `null` if the element has no placement.

---

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Validation passed — no errors |
| `1` | CLI error (file not found, invalid arguments) |
| `2` | Validation completed — one or more ERROR-severity issues found |

Use exit code `2` in CI pipelines to gate deployments on model quality.

---

## Example: minimal integration

```python
import subprocess, json

result = subprocess.run(
    ["bimoryn", "validate", "model.ifc", "--output", "report.json"],
    capture_output=True
)

with open("report.json") as f:
    report = json.load(f)

errors = [i for i in report["issues"] if i["severity"] == "error"]
print(f"{len(errors)} errors found")
for e in errors:
    print(f"  [{e['rule_id']}] {e['element_type']} {e['element_guid']}: {e['message']}")
```
