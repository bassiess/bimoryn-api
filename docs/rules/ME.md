# MEP Rules (ME)

MEP rules validate that mechanical, electrical, and plumbing elements are correctly defined, connected, and sized for downstream coordination and O&M documentation.

---

## ME-001 — MEP element not assigned to a system

**Severity:** ERROR
**Category:** MEP
**Standards:** ISO 19650-2:2018 §5.5.3 (exchange information requirements), ISO 16739-1:2018 §8.5 (IfcSystem grouping)

Every `IfcDistributionFlowElement` (ducts, pipes, fittings, equipment) must belong to an `IfcSystem` or `IfcDistributionSystem`. Unassigned elements are invisible to system-based clash detection, O&M handover, and commissioning workflows.

**Pass:** Element is referenced by `IfcRelAssignsToGroup` pointing to an `IfcSystem`.
**Fail:** Element has no system assignment.
**Fix:** Assign the element to the appropriate system in your MEP authoring tool.

---

## ME-002 — Unconnected MEP port

**Severity:** WARNING
**Category:** MEP
**Standards:** General BIM hygiene (incomplete MEP routing; no specific clause)

`IfcDistributionPort` instances not in any `IfcRelConnectsPorts` relationship represent open (unfinished) connections. This typically indicates incomplete routing or a connection lost during export.

**Note:** Some terminal ports are intentionally open (service points, future expansion). Review before fixing.

**Pass:** Port is referenced by at least one `IfcRelConnectsPorts`.
**Fail:** Port has no connection relationship.
**Fix:** Route the connection to its counterpart port or mark the element as a deliberate open end.

---

## ME-003 — Duct missing nominal size

**Severity:** ERROR
**Category:** MEP
**Standards:** ISO 19650-2:2018 §5.5.3 (exchange information requirements), NL BIM Loket BIMQ-I §4.3 (MEP element properties)

**Checks:** `Pset_DuctSegmentTypeCommon.NominalWidth`, `.NominalHeight`, `.NominalDiameter`, or `Qto_DuctSegmentBaseQuantities.CrossSectionArea`

Duct segments without size data cannot be used in airflow calculations, coordination drawings, or procurement schedules.

**Pass:** At least one size property is present.
**Fail:** All size properties absent.
**Fix:** Add size parameters to the duct type in your MEP authoring tool.

---

## ME-004 — Pipe missing nominal diameter

**Severity:** ERROR
**Category:** MEP
**Standards:** ISO 19650-2:2018 §5.5.3 (exchange information requirements), NL BIM Loket BIMQ-I §4.3 (MEP element properties)

**Checks:** `Pset_PipeSegmentTypeCommon.NominalDiameter` or `.OutsideDiameter`

Pipes without a diameter cannot be used in flow calculations, clashing against insulation offsets, or procurement.

**Pass:** At least one diameter property is present.
**Fail:** Both diameter properties absent.
**Fix:** Add nominal diameter to the pipe type.

---

## ME-005 — Flow terminal missing flow direction

**Severity:** WARNING
**Category:** MEP
**Standards:** General BIM hygiene (airflow modelling prerequisite; no specific clause)

Flow terminals (diffusers, grilles, sanitary fixtures) should have at least one `IfcDistributionPort` with a defined `FlowDirection` (SOURCE, SINK, or SOURCEANDSINK). This property drives airflow modelling and commissioning documentation.

**Pass:** At least one port has a non-NOTDEFINED FlowDirection.
**Fail:** No port with defined FlowDirection.
**Fix:** Set FlowDirection on the terminal's distribution port.

---

## ME-006 — Cable carrier missing voltage rating

**Severity:** WARNING
**Category:** MEP
**Standards:** General BIM hygiene (electrical safety classification; no specific ISO 19650 clause)

**Checks:** `Pset_CableCarrierSegmentTypeCommon.NominalVoltageRating` or `Pset_ElectricalDeviceCommon.NominalVoltage`

Mixing low-voltage and high-voltage cables in an unrated carrier is a safety and code issue. Voltage rating is required for electrical BIM coordination.

**Pass:** Voltage property present.
**Fail:** No voltage rating found.
**Fix:** Add the voltage rating to the cable carrier type.
