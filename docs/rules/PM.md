# Parameter Rules (PM)

Parameter rules verify that elements carry the required property sets and quantity values for downstream uses: cost estimation, energy analysis, FM handover, and scheduling.

---

## PM-001 — Wall missing fire rating

**Severity:** WARNING
**Category:** Parameters

**Checks:** `Pset_WallCommon.FireRating`

Fire rating is required for fire compartmentation schedules, regulatory submissions, and FM handover. Missing fire rating means the compartmentation model cannot be verified from the IFC.

**Pass:** `Pset_WallCommon.FireRating` is present.
**Fail:** Property absent.
**Fix:** Set FireRating in the wall's common property set (e.g. "EI 60", "REI 120").

---

## PM-002 — Space missing area quantity

**Severity:** ERROR
**Category:** Parameters

**Checks:** `Qto_SpaceBaseQuantities.NetFloorArea`, `.GrossFloorArea`, or any area quantity

Floor area is essential for GFA calculations, lettable area schedules, and regulatory compliance. A space without area data cannot contribute to any area-based analysis.

**Pass:** At least one area quantity is found.
**Fail:** No area quantity present.
**Fix:** Enable space area computation in your authoring tool before IFC export.

---

## PM-003 — Structural element missing LoadBearing property

**Severity:** WARNING
**Category:** Parameters

**Applies to:** IfcWall, IfcSlab, IfcColumn, IfcBeam, IfcMember, IfcFooting
**Checks:** `Pset_{Type}Common.LoadBearing`

The LoadBearing flag distinguishes structural from non-structural elements. Without it, structural analysis exports and cost schedule filters cannot distinguish these.

**Pass:** LoadBearing property is present.
**Fail:** Property absent.
**Fix:** Set LoadBearing (true/false) in the element's common property set.

---

## PM-004 — Door missing hardware set reference

**Severity:** INFO
**Category:** Parameters

Doors should reference an ironmongery/hardware property set for door schedule generation and specification. The check looks for any property set with "hardware" or "ironmongery" in its name.

**Pass:** A hardware-related property set is found.
**Fail:** No hardware property set present.
**Fix:** Add a hardware schedule property set to the door type.

---

## PM-005 — Element not assigned to a building storey

**Severity:** ERROR
**Category:** Parameters

**Applies to:** IfcWall, IfcSlab, IfcColumn, IfcBeam, IfcDoor, IfcWindow, IfcStair, IfcRamp, IfcRoof, IfcFurnishingElement, IfcDistributionElement

Every physical element must be contained in an `IfcBuildingStorey` via `IfcRelContainedInSpatialStructure`. Elements without a storey assignment are invisible in level-based views, clash detection by storey, and fire compartmentation checks.

**Pass:** Element is in at least one `IfcRelContainedInSpatialStructure`.
**Fail:** No containment relationship found.
**Fix:** Assign the element to the correct level in your authoring tool.

---

## PM-006 — Element missing classification reference

**Severity:** INFO
**Category:** Parameters

**Applies to:** IfcWall, IfcSlab, IfcColumn, IfcBeam, IfcDoor, IfcWindow, IfcSpace, IfcDistributionElement

Elements should carry at least one `IfcRelAssociatesClassification` link to a recognised classification system (OmniClass, Uniclass 2015, ETIM, NBS, NL-SfB). Required for cost estimation, FM asset management, and regulatory submissions.

**Pass:** At least one classification reference is found.
**Fail:** No classification relationship present.
**Fix:** Apply the project's classification system to the element type.

---

## PM-007 — Slab missing thickness

**Severity:** WARNING
**Category:** Parameters

**Checks:** `Pset_SlabCommon.NominalThickness`, `Qto_SlabBaseQuantities.Depth`, or `BaseQuantities.Depth`

Slab thickness is required for structural analysis, material take-offs, and U-value calculations. A slab without thickness data is incomplete for any downstream use.

**Pass:** At least one thickness property is present.
**Fail:** No thickness found.
**Fix:** Set the nominal thickness in the slab type or add it to the base quantity set.

---

## PM-008 — IfcProject missing author/organisation

**Severity:** WARNING
**Category:** Parameters

**Checks:** `IfcProject.OwnerHistory.OwningUser.ThePerson` and `IfcProject.OwnerHistory.OwningOrganization`

ISO 19650 and NL BIM Norm require model authorship metadata. Without it, model provenance cannot be established for audit trails, federated delivery, and handover documentation.

**Pass:** OwnerHistory is present with a non-empty person name or organisation name.
**Fail:** OwnerHistory absent or all name fields empty.
**Fix:** Configure your authoring tool's company information and ensure it is exported with the IFC file.
