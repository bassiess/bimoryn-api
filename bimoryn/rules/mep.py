"""MEP (Mechanical, Electrical, Plumbing) rules (ME-001 – ME-006)."""

from __future__ import annotations

from typing import Iterator

from bimoryn.models import Issue, RuleCategory, RuleConfig, Severity
from bimoryn.rules.base import Rule, register

_CAT = RuleCategory.MEP


@register
class MEPElementMissingSystem(Rule):
    """ME-001 — Every MEP distribution element must belong to a system.

    Unassigned elements won't appear in system-based schedules, clash
    detection by system, or handover O&M documentation.
    """

    id       = "ME-001"
    name     = "MEP element not assigned to a system"
    category = _CAT
    severity = Severity.ERROR

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        # Build set of GUIDs that ARE in a system
        in_system: set[str] = set()
        for sys_rel in model.by_type("IfcRelAssignsToGroup"):
            group = sys_rel.RelatingGroup
            if group.is_a("IfcSystem") or group.is_a("IfcDistributionSystem"):
                for obj in sys_rel.RelatedObjects:
                    in_system.add(obj.GlobalId)

        for el in model.by_type("IfcDistributionFlowElement"):
            if el.GlobalId not in in_system:
                yield self._issue(
                    el,
                    f"{el.is_a()} '{el.Name}' is not assigned to any MEP system",
                    detail="Assign to IfcSystem or IfcDistributionSystem",
                )


@register
class UnconnectedMEPPort(Rule):
    """ME-002 — MEP ports should be connected (no open ends on distribution segments).

    Open ports typically mean unfinished routing, connection drops during
    model export, or accidental deletions. Flagged as WARNING — some terminal
    ports are intentionally open (service points, future connections).
    """

    id       = "ME-002"
    name     = "Unconnected MEP port"
    category = _CAT
    severity = Severity.WARNING

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        # Ports that are in a connection are "connected"
        connected_ports: set[str] = set()
        for conn in model.by_type("IfcRelConnectsPorts"):
            if conn.RealizingElement is not None or True:  # always collect both ends
                p1 = getattr(conn, "RelatingPort", None)
                p2 = getattr(conn, "RelatedPort", None)
                if p1:
                    connected_ports.add(p1.GlobalId)
                if p2:
                    connected_ports.add(p2.GlobalId)

        for port in model.by_type("IfcDistributionPort"):
            if port.GlobalId not in connected_ports:
                # Find host element for context
                host = self._find_port_host(model, port)
                yield self._issue(
                    host or port,
                    f"MEP port '{port.Name}' (GUID {port.GlobalId}) is not connected",
                    detail="Open port — verify routing is complete",
                )

    def _find_port_host(self, model, port):
        for rel in model.by_type("IfcRelNests"):
            if port in rel.RelatedObjects:
                return rel.RelatingObject
        return None


@register
class DuctMissingSizeParameter(Rule):
    """ME-003 — Ducts must carry nominal width/height or diameter.

    Without size data, airflow calculations and coordination drawings
    cannot be generated.
    """

    id       = "ME-003"
    name     = "Duct missing nominal size"
    category = _CAT
    severity = Severity.ERROR

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        for duct in model.by_type("IfcDuctSegment"):
            has_size = (
                self._has_pset_value(duct, "Pset_DuctSegmentTypeCommon", "NominalWidth")
                or self._has_pset_value(duct, "Pset_DuctSegmentTypeCommon", "NominalHeight")
                or self._has_pset_value(duct, "Pset_DuctSegmentTypeCommon", "NominalDiameter")
                or self._has_pset_value(duct, "Qto_DuctSegmentBaseQuantities", "CrossSectionArea")
            )
            if not has_size:
                yield self._issue(
                    duct,
                    f"Duct '{duct.Name}' has no nominal size (width/height or diameter)",
                    detail="Required for airflow calculations and procurement",
                )


@register
class PipeMissingSizeParameter(Rule):
    """ME-004 — Pipes must carry nominal diameter."""

    id       = "ME-004"
    name     = "Pipe missing nominal diameter"
    category = _CAT
    severity = Severity.ERROR

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        for pipe in model.by_type("IfcPipeSegment"):
            has_size = (
                self._has_pset_value(pipe, "Pset_PipeSegmentTypeCommon", "NominalDiameter")
                or self._has_pset_value(pipe, "Pset_PipeSegmentTypeCommon", "OutsideDiameter")
            )
            if not has_size:
                yield self._issue(
                    pipe,
                    f"Pipe '{pipe.Name}' has no nominal diameter",
                    detail="Required for flow calculations and procurement",
                )


@register
class FlowTerminalMissingFlowDirection(Rule):
    """ME-005 — Flow terminals (diffusers, grilles, outlets) must declare flow direction.

    SOURCEANDSINK / SOURCE / SINK drives airflow modelling and commissioning.
    """

    id       = "ME-005"
    name     = "Flow terminal missing flow direction"
    category = _CAT
    severity = Severity.WARNING

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        for terminal in model.by_type("IfcFlowTerminal"):
            # Check ports for FlowDirection
            has_direction = False
            for rel in model.by_type("IfcRelNests"):
                if rel.RelatingObject.GlobalId == terminal.GlobalId:
                    for port in rel.RelatedObjects:
                        if port.is_a("IfcDistributionPort"):
                            flow = getattr(port, "FlowDirection", None)
                            if flow and str(flow) not in ("NOTDEFINED", "None"):
                                has_direction = True
                                break
            if not has_direction:
                yield self._issue(
                    terminal,
                    f"Flow terminal '{terminal.Name}' has no port with a defined FlowDirection",
                    detail="Set port FlowDirection to SOURCE, SINK, or SOURCEANDSINK",
                )


@register
class CableCarrierMissingVoltage(Rule):
    """ME-006 — Electrical cable carriers should declare voltage rating.

    Mixing voltage levels in an unrated carrier is a safety and code issue.
    """

    id       = "ME-006"
    name     = "Cable carrier missing voltage rating"
    category = _CAT
    severity = Severity.WARNING

    def check(self, model, config: RuleConfig) -> Iterator[Issue]:
        for carrier in model.by_type("IfcCableCarrierSegment"):
            has_voltage = (
                self._has_pset_value(carrier, "Pset_CableCarrierSegmentTypeCommon", "NominalVoltageRating")
                or self._has_pset_value(carrier, "Pset_ElectricalDeviceCommon", "NominalVoltage")
            )
            if not has_voltage:
                yield self._issue(
                    carrier,
                    f"Cable carrier '{carrier.Name}' has no nominal voltage rating",
                    detail="Required for electrical coordination and safety compliance",
                )
