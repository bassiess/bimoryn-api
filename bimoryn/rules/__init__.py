"""Rule registry — all rules must be imported here to be auto-discovered."""

# Import all rule modules to trigger their @register decorators
from bimoryn.rules import geometry, mep, naming, parameters, structure  # noqa: F401
from bimoryn.rules.base import REGISTRY, Rule, RuleRegistry

__all__ = ["Rule", "RuleRegistry", "REGISTRY"]
