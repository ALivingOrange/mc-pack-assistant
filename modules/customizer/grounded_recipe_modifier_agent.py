"""Back-compat shim; all contents have moved to sibling modules.

Phase 3.8 will delete this file once callers have been migrated.
"""

from .agents import recipe_modifier_agent, root_agent, searcher_agent

__all__ = ["recipe_modifier_agent", "root_agent", "searcher_agent"]
