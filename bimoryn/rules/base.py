"""Rule base class and global registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Iterator

from bimoryn.models import Issue, RuleCategory, RuleConfig, Severity

if TYPE_CHECKING:
    import ifcopenshell


class Rule(ABC):
    """Base class for all validation rules.

    Subclass, set class attributes, implement ``check()``.
    Register with the ``@register`` decorator in each rule module.

    Example::

        @register
        class MissingNameRule(Rule):
            id       = "NM-001"
            name     = "Missing element name"
            category = RuleCategory.NAMING
            severity = Severity.WARNING

            def check(self, model, config):
                for el in model.by_type("IfcElement"):
                    if not el.Name:
                        yield self._issue(el, "Element has no Name")
    """

    # --- class-level declaration (required) ---
    id:       str
    name:     str
    category: RuleCategory
    severity: Severity

    def __init__(self, config: RuleConfig | None = None) -> None:
        self._config = config or RuleConfig()
        # Allow config to override default severity
        if self._config.severity:
            self.severity = self._config.severity

    @property
    def enabled(self) -> bool:
        return self._config.enabled

    @abstractmethod
    def check(
        self,
        model: "ifcopenshell.file",
        config: RuleConfig,
    ) -> Iterator[Issue]:
        """Yield Issue objects for every violation found."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _issue(
        self,
        element: "ifcopenshell.entity_instance | None",
        message: str,
        detail: str | None = None,
        severity: Severity | None = None,
        location: tuple[float, float, float] | None = None,
    ) -> Issue:
        from bimoryn.models import IssueLocation

        loc = None
        if location:
            loc = IssueLocation(x=location[0], y=location[1], z=location[2])

        guid = None
        etype = None
        ename = None
        if element is not None:
            guid  = getattr(element, "GlobalId", None)
            etype = element.is_a()
            ename = getattr(element, "Name", None)

        return Issue(
            rule_id      = self.id,
            rule_name    = self.name,
            category     = self.category,
            severity     = severity or self.severity,
            element_guid = guid,
            element_type = etype,
            element_name = ename,
            message      = message,
            detail       = detail,
            location     = loc,
        )

    def _get_pset_value(
        self,
        element: "ifcopenshell.entity_instance",
        pset_name: str,
        prop_name: str,
    ):
        """Return a property value from a named Pset, or None if absent."""
        for rel in getattr(element, "IsDefinedBy", []):
            if not rel.is_a("IfcRelDefinesByProperties"):
                continue
            pdef = rel.RelatingPropertyDefinition
            if not pdef.is_a("IfcPropertySet"):
                continue
            if pdef.Name != pset_name:
                continue
            for prop in pdef.HasProperties:
                if prop.Name == prop_name:
                    return getattr(prop, "NominalValue", None)
        return None

    def _has_pset_value(
        self,
        element: "ifcopenshell.entity_instance",
        pset_name: str,
        prop_name: str,
    ) -> bool:
        return self._get_pset_value(element, pset_name, prop_name) is not None

    def _all_psets(
        self,
        element: "ifcopenshell.entity_instance",
    ) -> dict[str, dict[str, object]]:
        """Return {pset_name: {prop_name: value}} for an element."""
        result: dict[str, dict] = {}
        for rel in getattr(element, "IsDefinedBy", []):
            if not rel.is_a("IfcRelDefinesByProperties"):
                continue
            pdef = rel.RelatingPropertyDefinition
            if not pdef.is_a("IfcPropertySet"):
                continue
            props: dict = {}
            for prop in pdef.HasProperties:
                v = getattr(prop, "NominalValue", None)
                props[prop.Name] = v.wrappedValue if v else None
            result[pdef.Name] = props
        return result


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class RuleRegistry:
    def __init__(self) -> None:
        self._rules: dict[str, type[Rule]] = {}

    def register(self, rule_cls: type[Rule]) -> type[Rule]:
        if rule_cls.id in self._rules:
            raise ValueError(f"Duplicate rule ID: {rule_cls.id}")
        self._rules[rule_cls.id] = rule_cls
        return rule_cls

    def all_rules(self) -> list[type[Rule]]:
        return list(self._rules.values())

    def get(self, rule_id: str) -> type[Rule] | None:
        return self._rules.get(rule_id)

    def __len__(self) -> int:
        return len(self._rules)


REGISTRY = RuleRegistry()


def register(cls: type[Rule]) -> type[Rule]:
    """Class decorator — registers a Rule subclass in the global REGISTRY."""
    return REGISTRY.register(cls)
