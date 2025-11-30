"""Unit tests for error handling."""

from mycelium.errors import MyceliumError, RegistryError


def test_mycelium_error_basic():
    """Test basic error creation."""
    error = MyceliumError("Something went wrong")
    # Error message should be plain - formatting is handled by CLI output layer
    assert str(error) == "Something went wrong"


def test_mycelium_error_with_suggestion():
    """Test error with suggestion."""
    error = MyceliumError("Failed to connect", suggestion="Check network connection")
    assert "Failed to connect" in str(error)
    assert "💡 Suggestion:" in str(error)
    assert "Check network connection" in str(error)


def test_mycelium_error_with_docs():
    """Test error with documentation link."""
    error = MyceliumError("Configuration error", docs_url="https://docs.mycelium.dev/config")
    assert "📖 Docs:" in str(error)
    assert "https://docs.mycelium.dev/config" in str(error)


def test_mycelium_error_with_debug_info():
    """Test error with debug information."""
    error = MyceliumError("Process failed", debug_info={"pid": 12345, "exit_code": 1})
    assert "🔍 Debug Info:" in str(error)
    assert "pid: 12345" in str(error)
    assert "exit_code: 1" in str(error)


def test_registry_error():
    """Test registry-specific error."""
    error = RegistryError("Registry unavailable")
    assert isinstance(error, MyceliumError)
    assert "Registry unavailable" in str(error)
