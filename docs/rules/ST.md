# Structure Rules (ST)

Structure rules validate that structural elements carry the data required for analysis, coordination, and quantity take-offs.

---

## ST-001 — Column not flagged as load-bearing

**Severity:** WARNING (INFO if explicitly LoadBearing=False)
**Category:** Structure
**Standards:** ISO 19650-2:2018 §5.5.3 (structural analysis exchange requirements), General BIM hygiene

**Checks:** `Pset_ColumnCommon.LoadBearing`

Columns without a LoadBearing flag will be excluded from structural analysis exports and cost schedules. A column with `LoadBearing=False` is flagged as INFO — it may be intentional (architectural column) but warrants review.

**Pass:** `LoadBearing` property present and `True`.
**Fail:** Property absent (WARNING) or `False` (INFO).
**Fix:** Set `LoadBearing=True` in `Pset_ColumnCommon` for structural columns.

---

## ST-002 — Structural element missing material

**Severity:** ERROR
**Category:** Structure
**Standards:** ISO 19650-2:2018 §5.5.3 (exchange information requirements), Rgd BIM Norm §5.2 (materiaalspecificatie structuur)

**Applies to:** IfcBeam, IfcColumn, IfcMember, IfcFooting

Without a material association (`IfcRelAssociatesMaterial`), structural analysis and quantity take-offs for steel/concrete tonnage are impossible. This is an ERROR — the structural model is incomplete without materials.

**Pass:** Element has at least one material association.
**Fail:** No `IfcRelAssociatesMaterial` found for the element.
**Fix:** Assign the structural material in your authoring tool.

---

## ST-003 — Slab PredefinedType is NOTDEFINED or missing

**Severity:** WARNING
**Category:** Structure
**Standards:** ISO 16739-1:2018 §8.2 (IfcSlab.PredefinedType enumeration), General BIM hygiene

`IfcSlab.PredefinedType` must be one of: `FLOOR`, `ROOF`, `LANDING`, `BASESLAB`. Each carries different structural implications. `NOTDEFINED` or `USERDEFINED` causes downstream analysis tools to misclassify the slab.

**Pass:** `PredefinedType` is a defined value (not NOTDEFINED/USERDEFINED/None).
**Fail:** PredefinedType is undefined.
**Fix:** Set the correct PredefinedType on each slab.

---

## ST-004 — Foundation missing depth quantity

**Severity:** WARNING
**Category:** Structure
**Standards:** ISO 19650-2:2018 §5.5.3 (quantity take-off requirements), General BIM hygiene

**Checks:** `Qto_FootingBaseQuantities.Depth`, `BaseQuantities.Depth`, or `Pset_FootingCommon.NominalDepth`

Foundation depth is required for earthwork quantity take-offs and geotechnical verification. An `IfcFooting` without depth data cannot be used in structural or cost analysis.

**Pass:** At least one depth quantity is present.
**Fail:** No depth quantity found.
**Fix:** Add the depth quantity to the footing type or quantity set.

---

## ST-005 — Wall missing IsExternal property

**Severity:** WARNING
**Category:** Structure
**Standards:** ISO 19650-2:2018 §5.5.3 (exchange information requirements), Rgd BIM Norm §5.1 (gevel/schilidentificatie), NL BIM Loket §5.2 (buitenschil)

**Checks:** `Pset_WallCommon.IsExternal`

The `IsExternal` flag distinguishes external walls (subject to weatherproofing, U-value requirements, façade schedules) from internal walls. Without it, thermal analysis, energy modelling, and façade area calculations cannot run correctly.

**Pass:** `Pset_WallCommon.IsExternal` is present.
**Fail:** Property absent.
**Fix:** Set `IsExternal` (true/false) in `Pset_WallCommon` for all walls.

---

## ST-006 — Wall PredefinedType is NOTDEFINED

**Severity:** WARNING
**Category:** Structure
**Standards:** ISO 16739-1:2018 §8.2 (IfcWall.PredefinedType enumeration), General BIM hygiene

`IfcWall.PredefinedType` should be set to a meaningful value: `STANDARD`, `POLYGONAL`, `SHEAR`, `PARTITIONING`, `PLUMBINGWALL`, `MOVABLE`, or `SOLIDWALL`. `NOTDEFINED` prevents automated classification in structural and architectural analysis tools.

**Pass:** `PredefinedType` is a defined value.
**Fail:** PredefinedType is NOTDEFINED, USERDEFINED, or null.
**Fix:** Set the appropriate PredefinedType on each wall in your authoring tool.
