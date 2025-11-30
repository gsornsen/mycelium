"""Error handling with clear, actionable messages.

Follows DX requirements:
- What went wrong
- Why it happened
- How to fix it
- Link to docs
"""

from typing import Optional


class MyceliumError(Exception):
    """Base exception for Mycelium with enhanced error messages."""

    def __init__(
        self,
        message: str,
        suggestion: Optional[str] = None,
        docs_url: Optional[str] = None,
        debug_info: Optional[dict[str, str | int | None]] = None,
    ):
        """Initialize error with contextual information.

        Args:
            message: What went wrong
            suggestion: How to fix it
            docs_url: Link to relevant documentation
            debug_info: Additional debug information
        """
        self.message = message
        self.suggestion = suggestion
        self.docs_url = docs_url
        self.debug_info = debug_info or {}
        super().__init__(message)

    def __str__(self) -> str:
        """Format error message with all context."""
        # Note: Don't add ✗ prefix here - let the CLI output layer handle formatting
        lines = [self.message]

        if self.suggestion:
            lines.append(f"💡 Suggestion: {self.suggestion}")

        if self.debug_info:
            lines.append("🔍 Debug Info:")
            for key, value in self.debug_info.items():
                lines.append(f"  {key}: {value}")

        if self.docs_url:
            lines.append(f"📖 Docs: {self.docs_url}")

        return "\n".join(lines)


class RegistryError(MyceliumError):
    """Agent registry related errors."""

    pass


class SupervisorError(MyceliumError):
    """Process supervisor related errors."""

    pass


class HealthCheckError(MyceliumError):
    """Health check related errors."""

    pass


class ConfigurationError(MyceliumError):
    """Configuration related errors."""

    pass


class PortAllocationError(MyceliumError):
    """Port allocation related errors."""

    pass
