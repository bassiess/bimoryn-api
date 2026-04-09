# Naming Rules (NM)

Naming rules enforce element naming conventions that enable reliable coordination, scheduling, and data exchange. Default patterns follow ISO 19650 and common NL/EU practice; all patterns are configurable per project.

---

## NM-001 — Missing element name

**Severity:** WARNING
**Category:** Naming

**Applies to:** IfcWall, IfcSlab, IfcColumn, IfcBeam, IfcDoor, IfcWindow, IfcSpace, IfcStair, IfcRamp, IfcRoof, IfcDistributionElement, IfcBuildingElementProxy

The `Name` attribute must be non-empty. Unnamed elements cause blank rows in schedules and make it impossible to identify elements in BCF issues or clash reports.

**Pass:** Element has a non-empty `Name`.
**Fail:** `Name` is null, empty, or whitespace-only.
**Fix:** Add a name that follows your project naming standard.

---

## NM-002 — Space name does not match convention

**Severity:** WARNING (ERROR if blank)
**Category:** Naming

Space names must match the configured regex pattern. The default pattern allows alphanumeric names with dashes, slashes, and spaces, up to 50 characters.

**Config params:**

| Param | Default | Description |
|-------|---------|-------------|
| `pattern` | `^[\w][\w\-/ ]{0,49}$` | Regex pattern for valid space names |

**Pass:** Name matches pattern.
**Fail:** Name is blank (ERROR) or doesn't match pattern (WARNING).
**Fix:** Rename the space according to the project's room-naming convention.

---

## NM-003 — Type name missing discipline prefix

**Severity:** INFO
**Category:** Naming

`IfcTypeObject` names should start with a recognised discipline prefix: `A-` (Architecture), `S-` (Structure), `M-` (Mechanical), `E-` (Electrical), `P-` (Plumbing), `C-` (Civil), `L-` (Landscape).

**Config params:**

| Param | Default | Description |
|-------|---------|-------------|
| `prefixes` | `["A-","S-","M-","E-","P-","C-","L-"]` | List of allowed prefixes |

**Pass:** Type name starts with an allowed prefix.
**Fail:** No matching prefix found.
**Fix:** Rename the type with the appropriate discipline prefix.

---

## NM-004 — Duplicate door/window mark

**Severity:** ERROR
**Category:** Naming

Door and window marks (Tag or Name) must be unique across the model. Duplicate marks corrupt door/window schedules and make element identification in BCF impossible.

**Pass:** Each mark appears on exactly one element.
**Fail:** Two or more elements share the same mark.
**Fix:** Renumber the duplicate elements.

---

## NM-005 — Building storey name does not match convention

**Severity:** WARNING (ERROR if blank)
**Category:** Naming

Building storey names should follow a recognisable floor pattern. Default accepted formats: `B2`, `B1`, `GF`, `L01`–`L99`, `RF`, `M01`, `UG`, `SB`, `P01`–`P99`, `Ground`, `Basement`, `Roof`.

**Config params:**

| Param | Default | Description |
|-------|---------|-------------|
| `pattern` | `^(B\d+\|GF\|L\d{1,2}\|RF\|M\d{1,2}\|UG\|SB\|P\d{1,2}\|Ground\|Basement\|Roof)$` | Pattern (case-insensitive) |

**Pass:** Storey name matches pattern.
**Fail:** Name is blank (ERROR) or doesn't match (WARNING).
**Fix:** Rename the storey to a recognised floor designation.

---

## NM-006 — Generic / default type name detected

**Severity:** WARNING
**Category:** Naming

Type names that look like Revit or ArchiCAD defaults (e.g. "Basic Wall", "Generic - 200mm", "Default", "<unnamed>") indicate the model was not properly cleaned up before export.

**Detected patterns:** Names starting with Basic, Generic, Default, Standard, Unnamed, New, or matching `<…>` or bare thickness strings like `200mm`.

**Pass:** Type name does not match any generic pattern.
**Fail:** Type name matches a generic/default pattern.
**Fix:** Rename the type to a project-specific identifier.

---

## NM-007 — Space missing long name / description

**Severity:** INFO
**Category:** Naming

`IfcSpace` elements should carry either a `LongName` or `Description` to support room-book generation and handover documentation.

**Pass:** At least one of `LongName` or `Description` is non-empty.
**Fail:** Both are absent.
**Fix:** Add a long name (e.g. "Meeting Room" or "Serverruimte") to the space.

---

## NM-008 — IFC schema version is IFC2x3

**Severity:** INFO
**Category:** Naming

The model uses the IFC2x3 schema. IFC4 is the current standard and offers significantly improved property set coverage, quantity take-offs, and MEP connectivity. Several BIMoryn rules have reduced coverage on IFC2x3 models.

**Pass:** Model schema is IFC4 or newer.
**Fail:** Model schema is IFC2x3 or older.
**Fix:** Re-export the model using IFC4 from your authoring tool.
