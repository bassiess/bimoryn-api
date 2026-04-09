# Geometry Rules (GE)

Geometry rules validate spatial integrity, element placement, and structural completeness.
Most GE rules operate on IFC attributes only — no geometry kernel required.

---

## GE-001 — Duplicate GlobalId (GUID)

**Severity:** ERROR
**Category:** Geometry

Every IFC element must have a unique GlobalId. Duplicate GUIDs corrupt BCF topic references, break clash detection tools, and cause unpredictable behaviour when federating models.

**Pass:** All `IfcRoot` elements have unique GlobalIds.
**Fail:** Two or more elements share the same GUID — both are flagged.
**Fix:** Regenerate the GlobalId of affected elements in your authoring tool.

---

## GE-002 — Wall has zero or near-zero length

**Severity:** ERROR
**Category:** Geometry

**Checks:** `Qto_WallBaseQuantities.Length`

Walls shorter than 50 mm (configurable via `min_length_m`) are modelling artefacts — typically leftover sketch lines promoted to walls or snapping errors. They inflate element counts and cause area/volume computation errors.

**Config params:**

| Param | Default | Description |
|-------|---------|-------------|
| `min_length_m` | `0.05` | Minimum acceptable wall length in metres |

**Pass:** Wall length ≥ min_length_m, or no length quantity present (not checked).
**Fail:** Wall length < min_length_m.
**Fix:** Delete the stub wall or extend it to a valid length.

---

## GE-003 — Element has no spatial containment

**Severity:** WARNING
**Category:** Geometry

Physical `IfcElement` instances must be associated to the spatial structure via `IfcRelContainedInSpatialStructure` (or aggregated). Uncontained elements are invisible in storey-based views, schedule filters, and cost take-offs.

Excludes annotation types: `IfcAnnotation`, `IfcGrid`, `IfcVirtualElement`.

**Pass:** Element is contained or aggregated.
**Fail:** Element has no spatial relationship.
**Fix:** Assign the element to the correct building storey in your authoring tool.

---

## GE-004 — Duplicate wall placement detected

**Severity:** WARNING
**Category:** Geometry

Walls sharing an identical `ObjectPlacement` origin (rounded to 1 mm) are likely duplicates created by copy-paste without moving. This inflates quantities and causes rendering artefacts.

**Pass:** No two walls share the same origin.
**Fail:** Two or more walls share the same placement origin.
**Fix:** Delete the duplicate wall. Check if it carries any data that should be on the surviving wall.

---

## GE-005 — Opening element has no host

**Severity:** WARNING
**Category:** Geometry

An `IfcOpeningElement` not attached via `IfcRelVoidsElement` is orphaned — it represents a void in no wall or slab. Usually caused by deleting a door/window without cleaning up the associated void.

**Pass:** Every `IfcOpeningElement` is referenced by an `IfcRelVoidsElement`.
**Fail:** Orphaned `IfcOpeningElement` found.
**Fix:** Delete the orphaned opening element.

---

## GE-006 — Project true north not defined

**Severity:** INFO
**Category:** Geometry

The `IfcGeometricRepresentationContext` should declare a `TrueNorth` direction. Without it the model cannot be correctly oriented for site coordination, solar analysis, or energy simulation.

**Pass:** At least one `IfcGeometricRepresentationContext` has a non-null `TrueNorth`.
**Fail:** No representation context defines TrueNorth.
**Fix:** Set True North in your project settings before export.

---

## GE-007 — Element placed at world origin (0,0,0)

**Severity:** WARNING
**Category:** Geometry

Elements placed exactly at (0, 0, 0) in world coordinates are almost always a mis-export or unplaced element. In federated models this causes all elements to pile up at the site origin, breaking coordination.

**Pass:** Element placement origin is not (0.0, 0.0, 0.0).
**Fail:** Element placed at exact world origin.
**Fix:** Verify the element has a valid placement or remove it if it is a ghost object.
