"""Rule registry — all rules must be imported here to be auto-discovered."""

from bimoryn.rules.base import Rule, RuleRegistry, REGISTRY

# Import all rule modules to trigger their @register decorators
from bimoryn.rules import naming, parameters, geometry, structure, mep  # noqa: F401

__all__ = ["Rule", "RuleRegistry", "REGISTRY"]
