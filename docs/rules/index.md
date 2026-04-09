# BIMoryn Validation Rules

35 rules across 5 categories. All rules run on IFC4 models (IFC2x3 supported with degraded coverage).

## Categories

| Prefix | Category   | Count | Description |
|--------|-----------|-------|-------------|
| GE     | Geometry  | 7     | Spatial integrity, duplicate detection, placement errors |
| ME     | MEP       | 6     | Mechanical, electrical, plumbing system completeness |
| NM     | Naming    | 8     | Element names, space names, storey conventions |
| PM     | Parameters| 8     | Required property sets and quantities |
| ST     | Structure | 6     | Structural element properties and materials |

## Severity Levels

| Level   | Meaning |
|---------|---------|
| ERROR   | Model is broken or unusable downstream — must fix before handover |
| WARNING | Data gap that affects downstream workflows — should fix |
| INFO    | Best-practice recommendation — review and address if applicable |

## Full Rule List

| ID     | Name                                       | Severity | Category   |
|--------|--------------------------------------------|----------|------------|
| GE-001 | Duplicate GlobalId (GUID)                  | ERROR    | Geometry   |
| GE-002 | Wall has zero or near-zero length          | ERROR    | Geometry   |
| GE-003 | Element has no spatial containment         | WARNING  | Geometry   |
| GE-004 | Duplicate wall placement detected          | WARNING  | Geometry   |
| GE-005 | Opening element has no host                | WARNING  | Geometry   |
| GE-006 | Project true north not defined             | INFO     | Geometry   |
| GE-007 | Element placed at world origin (0,0,0)     | WARNING  | Geometry   |
| ME-001 | MEP element not assigned to a system       | ERROR    | MEP        |
| ME-002 | Unconnected MEP port                       | WARNING  | MEP        |
| ME-003 | Duct missing nominal size                  | ERROR    | MEP        |
| ME-004 | Pipe missing nominal diameter              | ERROR    | MEP        |
| ME-005 | Flow terminal missing flow direction       | WARNING  | MEP        |
| ME-006 | Cable carrier missing voltage rating       | WARNING  | MEP        |
| NM-001 | Missing element name                       | WARNING  | Naming     |
| NM-002 | Space name does not match convention       | WARNING  | Naming     |
| NM-003 | Type name missing discipline prefix        | INFO     | Naming     |
| NM-004 | Duplicate door/window mark                 | ERROR    | Naming     |
| NM-005 | Building storey name does not match        | WARNING  | Naming     |
| NM-006 | Generic / default type name detected       | WARNING  | Naming     |
| NM-007 | Space missing long name / description      | INFO     | Naming     |
| NM-008 | IFC schema version is IFC2x3               | INFO     | Naming     |
| PM-001 | Wall missing fire rating                   | WARNING  | Parameters |
| PM-002 | Space missing area quantity                | ERROR    | Parameters |
| PM-003 | Structural element missing LoadBearing     | WARNING  | Parameters |
| PM-004 | Door missing hardware set reference        | INFO     | Parameters |
| PM-005 | Element not assigned to a building storey  | ERROR    | Parameters |
| PM-006 | Element missing classification reference   | INFO     | Parameters |
| PM-007 | Slab missing thickness                     | WARNING  | Parameters |
| PM-008 | IfcProject missing author/organisation     | WARNING  | Parameters |
| ST-001 | Column not flagged as load-bearing         | WARNING  | Structure  |
| ST-002 | Structural element missing material        | ERROR    | Structure  |
| ST-003 | Slab PredefinedType is NOTDEFINED          | WARNING  | Structure  |
| ST-004 | Foundation missing depth quantity          | WARNING  | Structure  |
| ST-005 | Wall missing IsExternal property           | WARNING  | Structure  |
| ST-006 | Wall PredefinedType is NOTDEFINED          | WARNING  | Structure  |

## Configuration

All rules accept a `RuleConfig` with a `params` dict. Rule-specific parameters are documented in each category page.

See also: [Output Schema](../output-schema.md)
