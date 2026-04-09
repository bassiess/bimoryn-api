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

| ID     | Name                                       | Severity | Category   | Standards |
|--------|--------------------------------------------|----------|------------|-----------|
| GE-001 | Duplicate GlobalId (GUID)                  | ERROR    | Geometry   | ISO 16739-1 §5.1.5, ISO 19650-1 §5.7 |
| GE-002 | Wall has zero or near-zero length          | ERROR    | Geometry   | General BIM hygiene |
| GE-003 | Element has no spatial containment         | WARNING  | Geometry   | ISO 19650-2 §5.5.3, ISO 16739-1 §8.3 |
| GE-004 | Duplicate wall placement detected          | WARNING  | Geometry   | General BIM hygiene |
| GE-005 | Opening element has no host                | WARNING  | Geometry   | ISO 16739-1 §6.3 |
| GE-006 | Project true north not defined             | INFO     | Geometry   | ISO 19650-2 §5.3.1, Rgd BIM Norm §3.2 |
| GE-007 | Element placed at world origin (0,0,0)     | WARNING  | Geometry   | ISO 19650-2 §5.5.3, Rgd BIM Norm §3.2 |
| ME-001 | MEP element not assigned to a system       | ERROR    | MEP        | ISO 19650-2 §5.5.3, ISO 16739-1 §8.5 |
| ME-002 | Unconnected MEP port                       | WARNING  | MEP        | General BIM hygiene |
| ME-003 | Duct missing nominal size                  | ERROR    | MEP        | ISO 19650-2 §5.5.3, NL BIM Loket BIMQ-I §4.3 |
| ME-004 | Pipe missing nominal diameter              | ERROR    | MEP        | ISO 19650-2 §5.5.3, NL BIM Loket BIMQ-I §4.3 |
| ME-005 | Flow terminal missing flow direction       | WARNING  | MEP        | General BIM hygiene |
| ME-006 | Cable carrier missing voltage rating       | WARNING  | MEP        | General BIM hygiene |
| NM-001 | Missing element name                       | WARNING  | Naming     | ISO 19650-2 §5.5.3, NL BIM Loket §4.1 |
| NM-002 | Space name does not match convention       | WARNING  | Naming     | ISO 19650-2 §5.3.1, NL BIM Loket §4.2, Rgd BIM Norm §4.1 |
| NM-003 | Type name missing discipline prefix        | INFO     | Naming     | NL BIM Loket §4.1 |
| NM-004 | Duplicate door/window mark                 | ERROR    | Naming     | ISO 19650-2 §5.5.3 |
| NM-005 | Building storey name does not match        | WARNING  | Naming     | ISO 19650-2 §5.3.1, Rgd BIM Norm §4.2, NL BIM Loket §4.2 |
| NM-006 | Generic / default type name detected       | WARNING  | Naming     | General BIM hygiene |
| NM-007 | Space missing long name / description      | INFO     | Naming     | ISO 19650-2 §5.5.3, Rgd BIM Norm §4.1 |
| NM-008 | IFC schema version is IFC2x3               | INFO     | Naming     | ISO 19650-2 §5.4.2, ISO 16739-1:2018 |
| PM-001 | Wall missing fire rating                   | WARNING  | Parameters | ISO 19650-2 §5.5.3, Rgd BIM Norm §5.1, NL BIM Loket §5.2 |
| PM-002 | Space missing area quantity                | ERROR    | Parameters | ISO 19650-2 §5.5.3, NL BIM Loket §4.4, Rgd BIM Norm §4.3 |
| PM-003 | Structural element missing LoadBearing     | WARNING  | Parameters | ISO 19650-2 §5.5.3 |
| PM-004 | Door missing hardware set reference        | INFO     | Parameters | General BIM hygiene |
| PM-005 | Element not assigned to a building storey  | ERROR    | Parameters | ISO 19650-2 §5.5.3, ISO 16739-1 §8.3 |
| PM-006 | Element missing classification reference   | INFO     | Parameters | ISO 19650-2 §5.5.3, NL BIM Loket §4.5, UK BIM Framework §4.3 |
| PM-007 | Slab missing thickness                     | WARNING  | Parameters | ISO 19650-2 §5.5.3, Rgd BIM Norm §5.2 |
| PM-008 | IfcProject missing author/organisation     | WARNING  | Parameters | ISO 19650-2 §5.3.1, ISO 19650-1 §5.6, NL BIM Loket §3.1 |
| ST-001 | Column not flagged as load-bearing         | WARNING  | Structure  | ISO 19650-2 §5.5.3 |
| ST-002 | Structural element missing material        | ERROR    | Structure  | ISO 19650-2 §5.5.3, Rgd BIM Norm §5.2 |
| ST-003 | Slab PredefinedType is NOTDEFINED          | WARNING  | Structure  | ISO 16739-1 §8.2 |
| ST-004 | Foundation missing depth quantity          | WARNING  | Structure  | ISO 19650-2 §5.5.3 |
| ST-005 | Wall missing IsExternal property           | WARNING  | Structure  | ISO 19650-2 §5.5.3, Rgd BIM Norm §5.1, NL BIM Loket §5.2 |
| ST-006 | Wall PredefinedType is NOTDEFINED          | WARNING  | Structure  | ISO 16739-1 §8.2 |

## Standards Coverage Matrix

Every rule maps to at least one standard citation or is marked **General BIM hygiene**.

| Standard | Rules | Coverage |
|----------|-------|----------|
| ISO 19650-2:2018 | GE-001, GE-003, GE-006, GE-007, ME-001, ME-003, ME-004, NM-001, NM-002, NM-004, NM-005, NM-007, NM-008, PM-001, PM-002, PM-003, PM-005, PM-006, PM-007, PM-008, ST-001, ST-002, ST-004, ST-005 | **24/35** |
| ISO 16739-1:2018 (IFC) | GE-001, GE-003, GE-005, ME-001, NM-008, PM-005, ST-003, ST-006 | **8/35** |
| NL BIM Loket | ME-003, ME-004, NM-001, NM-002, NM-003, NM-005, PM-001, PM-002, PM-006, PM-008, ST-005 | **11/35** |
| Rgd BIM Norm | GE-006, GE-007, NM-002, NM-005, NM-007, PM-001, PM-002, PM-007, ST-002, ST-005 | **10/35** |
| ISO 19650-1:2018 | GE-001, PM-008 | **2/35** |
| UK BIM Framework | PM-006 | **1/35** |
| General BIM hygiene | GE-002, GE-004, ME-002, ME-005, ME-006, NM-006, PM-003, PM-004, ST-001, ST-003, ST-004, ST-006 | **12/35** |

> Rules can appear in multiple rows (multi-standard coverage). All 35 rules have at least one citation.

### Key coverage claims for sales conversations

- **24 of 35 rules (69%) map directly to ISO 19650-2** — the dominant standard in UK, NL, BE, and DE public-sector BIM contracts.
- **11 rules cover NL BIM Loket** — directly relevant to Dutch public procurement.
- **10 rules cover Rgd BIM Norm** — the standard for all Dutch government building projects (Rijksgebouwendienst).
- **0 rules are uncited** — every rule has a rationale anchored in a published standard or explicit BIM hygiene justification.

## Configuration

All rules accept a `RuleConfig` with a `params` dict. Rule-specific parameters are documented in each category page.

See also: [Output Schema](../output-schema.md)
