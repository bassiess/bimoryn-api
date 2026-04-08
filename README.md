# BIMoryn — BIM Validation Engine

Automated rule-based QA for IFC models. Catch naming errors, missing parameters, geometry faults, and MEP coordination issues before they reach downstream workflows.

---

## Prerequisites

- Python 3.11 or later
- `pip` (bundled with Python)

## Install

```bash
pip install -e .
```

This installs the `bimoryn` command and all dependencies (ifcopenshell, pydantic, typer, rich).

## Usage

```bash
# Validate a model — prints issue table to terminal
bimoryn validate model.ifc

# Save a JSON report
bimoryn validate model.ifc --output report.json

# Save a BCF issue file (open in Revit, Solibri, BIM Collab)
bimoryn validate model.ifc --output issues.bcfzip --format bcf

# Only show errors and warnings (skip info)
bimoryn validate model.ifc --min-severity warning

# Skip specific rules
bimoryn validate model.ifc --disable NM-003,PM-006

# Run the bundled demo
bimoryn validate samples/demo.ifc
```

Exit code `0` = pass (no errors), `2` = errors found. Useful for CI pipelines.

---

## Sample output

```
Model:    BIMoryn Demo Project
Schema:   IFC4
Elements: 4  |  Rules run: 31  |  Time: 54ms

Issues: 12 errors  7 warnings  4 info  (23 total)

SEV      RULE     CATEGORY     ELEMENT                MESSAGE
ERROR    GE-001   geometry                            GlobalId '...' is shared by 2 elements
ERROR    PM-002   parameters   IfcSpace  OFFICE_01    Space 'OFFICE_01' has no floor area quantity
ERROR    ST-002   structure    IfcColumn S-COL-01     IfcColumn 'S-COL-01' has no material association
WARNING  NM-001   naming       IfcWall                IfcWall has no Name value
WARNING  PM-001   parameters   IfcWall   A-EXT-WALL   Wall 'A-EXT-WALL' has no FireRating in Pset_WallCommon
WARNING  NM-005   naming       IfcBuild  Level_01     Storey name 'Level_01' does not match convention
WARNING  ST-001   structure    IfcColumn S-COL-01     Column 'S-COL-01' has no LoadBearing property
WARNING  ST-005   structure    IfcWall   A-EXT-WALL   Wall 'A-EXT-WALL' has no IsExternal property
INFO     GE-006   geometry     IfcProje               No TrueNorth defined in any context
INFO     NM-007   naming       IfcSpace  OFFICE_01    Space 'OFFICE_01' has no LongName or Description
```

---

## Rule library (31 rules)

### Naming (NM)

| ID     | Severity | Name                                  |
|--------|----------|---------------------------------------|
| NM-001 | warning  | Missing element name                  |
| NM-002 | warning  | Space name does not match convention  |
| NM-003 | info     | Type name missing discipline prefix   |
| NM-004 | error    | Duplicate door/window mark            |
| NM-005 | warning  | Building storey name does not match convention |
| NM-006 | warning  | Generic / default type name detected  |
| NM-007 | info     | Space missing long name / description |

### Parameters (PM)

| ID     | Severity | Name                                        |
|--------|----------|---------------------------------------------|
| PM-001 | warning  | Wall missing fire rating                    |
| PM-002 | error    | Space missing area quantity                 |
| PM-003 | warning  | Structural element missing LoadBearing property |
| PM-004 | info     | Door missing hardware set reference         |
| PM-005 | error    | Element not assigned to a building storey   |
| PM-006 | info     | Element missing classification reference    |
| PM-007 | warning  | Slab missing thickness                      |

### Geometry (GE)

| ID     | Severity | Name                                  |
|--------|----------|---------------------------------------|
| GE-001 | error    | Duplicate GlobalId (GUID)             |
| GE-002 | error    | Wall has zero or near-zero length     |
| GE-003 | warning  | Element has no spatial containment    |
| GE-004 | warning  | Duplicate wall placement detected     |
| GE-005 | warning  | Opening element has no host           |
| GE-006 | info     | Project true north not defined        |

### Structure (ST)

| ID     | Severity | Name                                        |
|--------|----------|---------------------------------------------|
| ST-001 | warning  | Column not flagged as load-bearing          |
| ST-002 | error    | Structural element missing material         |
| ST-003 | warning  | Slab PredefinedType is NOTDEFINED or missing |
| ST-004 | warning  | Foundation missing depth quantity           |
| ST-005 | warning  | Wall missing IsExternal property            |

### MEP (ME)

| ID     | Severity | Name                                        |
|--------|----------|---------------------------------------------|
| ME-001 | error    | MEP element not assigned to a system        |
| ME-002 | warning  | Unconnected MEP port                        |
| ME-003 | error    | Duct missing nominal size                   |
| ME-004 | error    | Pipe missing nominal diameter               |
| ME-005 | warning  | Flow terminal missing flow direction        |
| ME-006 | warning  | Cable carrier missing voltage rating        |

```bash
# List all rules in the terminal
bimoryn rules list

# Filter by category
bimoryn rules list --category geometry
```

---

## Output formats

### JSON (default)

Machine-readable. Suitable for dashboards, CI integrations, and API consumers.

```bash
bimoryn validate model.ifc --output report.json --format json
```

See [JSON schema documentation](docs/output-schema.md) for the full field reference.

### BCF (BIM Collaboration Format)

Opens directly in Revit, Solibri, BIM Collab Zoom, and most BIM coordination tools.

```bash
bimoryn validate model.ifc --output issues.bcfzip --format bcf
```

---

## Project structure

```
bimoryn/
  cli.py          — Typer CLI entry point
  engine.py       — Validation loop (IFC → rules → issues → result)
  models.py       — Data contracts (Issue, ValidationResult, RuleConfig)
  rules/
    base.py       — Rule base class and registry
    naming.py     — NM-001–NM-007
    parameters.py — PM-001–PM-007
    geometry.py   — GE-001–GE-006
    structure.py  — ST-001–ST-005
    mep.py        — ME-001–ME-006
  output/
    json_report.py — JSON serialiser
    bcf.py         — BCF/ZIP exporter
samples/
  demo.ifc        — Intentionally flawed demo model (exercises all categories)
```

---

## License

Proprietary — BIMoryn pilot use only. Contact hello@bimoryn.com for licensing.
