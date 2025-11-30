"""Agent discovery module.

Discovers agents from plugin directories and registers them
in the agent registry.
"""

from mycelium.discovery.scanner import AgentScanner, DiscoveredAgent

__all__ = ["AgentScanner", "DiscoveredAgent"]
