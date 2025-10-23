# Source: wizard-integration.md
# Line: 852
# Valid syntax: True
# Has imports: True
# Has assignments: True

from abc import ABC, abstractmethod

class WizardPlugin(ABC):
    """Base class for wizard plugins."""

    @abstractmethod
    def get_screen_name(self) -> str:
        """Get plugin screen name."""
        pass

    @abstractmethod
    def show_screen(self, state: WizardState) -> dict:
        """Show plugin screen and return data."""
        pass

    @abstractmethod
    def validate(self, state: WizardState) -> list[ValidationError]:
        """Validate plugin-specific state."""
        pass

class MonitoringPlugin(WizardPlugin):
    """Plugin for monitoring configuration."""

    def get_screen_name(self) -> str:
        return "monitoring"

    def show_screen(self, state: WizardState) -> dict:
        # Show monitoring configuration screen
        return {"provider": "prometheus", "port": 9090}

    def validate(self, state: WizardState) -> list[ValidationError]:
        # Validate monitoring settings
        return []

# Plugin registry
class WizardPluginRegistry:
    def __init__(self):
        self.plugins = {}

    def register(self, plugin: WizardPlugin):
        self.plugins[plugin.get_screen_name()] = plugin

    def get_plugin(self, name: str) -> WizardPlugin:
        return self.plugins.get(name)

# Usage
registry = WizardPluginRegistry()
registry.register(MonitoringPlugin())