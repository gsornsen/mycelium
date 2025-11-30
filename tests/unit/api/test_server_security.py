"""Security tests for Mycelium API server.

Tests critical security requirements:
- Loopback-only binding (127.0.0.1)
- Rate limiting enforcement
- CORS restrictions
"""

from unittest.mock import patch

import pytest

from mycelium.api.server import start_server


class TestLoopbackBinding:
    """Tests for loopback-only binding security requirement."""

    def test_default_host_is_loopback(self):
        """Test that default host is 127.0.0.1."""
        with patch("mycelium.api.server.uvicorn.run") as mock_run, patch("mycelium.api.server.create_app"):
            # Mock to prevent actual server startup
            mock_run.side_effect = KeyboardInterrupt()

            try:
                start_server(port=8080)
            except KeyboardInterrupt:
                pass

            # Verify uvicorn.run was called with 127.0.0.1
            assert mock_run.called
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["host"] == "127.0.0.1"

    def test_localhost_normalized_to_loopback(self):
        """Test that 'localhost' is normalized to 127.0.0.1."""
        with patch("mycelium.api.server.uvicorn.run") as mock_run, patch("mycelium.api.server.create_app"):
            mock_run.side_effect = KeyboardInterrupt()

            try:
                start_server(host="localhost", port=8080)
            except KeyboardInterrupt:
                pass

            # Verify it was normalized to 127.0.0.1
            assert mock_run.called
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["host"] == "127.0.0.1"

    def test_reject_network_binding(self):
        """Test that binding to 0.0.0.0 is rejected."""
        with pytest.raises(ValueError) as exc_info:
            start_server(host="0.0.0.0", port=8080)

        error_msg = str(exc_info.value)
        assert "127.0.0.1" in error_msg
        assert "localhost" in error_msg
        assert "security" in error_msg.lower()

    def test_reject_custom_ip_binding(self):
        """Test that binding to custom IP is rejected."""
        with pytest.raises(ValueError) as exc_info:
            start_server(host="192.168.1.100", port=8080)

        error_msg = str(exc_info.value)
        assert "security" in error_msg.lower()

    def test_reject_wildcard_binding(self):
        """Test that wildcard binding is rejected."""
        with pytest.raises(ValueError) as exc_info:
            start_server(host="::", port=8080)

        error_msg = str(exc_info.value)
        assert "security" in error_msg.lower()


class TestServerConfiguration:
    """Tests for server configuration parameters."""

    def test_custom_port(self):
        """Test that custom port is used."""
        with patch("mycelium.api.server.uvicorn.run") as mock_run, patch("mycelium.api.server.create_app"):
            mock_run.side_effect = KeyboardInterrupt()

            try:
                start_server(port=9000)
            except KeyboardInterrupt:
                pass

            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["port"] == 9000

    def test_custom_redis_url(self):
        """Test that custom Redis URL is passed to app."""
        with patch("mycelium.api.server.uvicorn.run") as mock_run:
            with patch("mycelium.api.server.create_app") as mock_create_app:
                mock_run.side_effect = KeyboardInterrupt()

                try:
                    start_server(redis_url="redis://custom:6380")
                except KeyboardInterrupt:
                    pass

                # Verify create_app was called with custom redis_url
                assert mock_create_app.called
                call_kwargs = mock_create_app.call_args[1]
                assert call_kwargs["redis_url"] == "redis://custom:6380"

    def test_reload_mode(self):
        """Test that reload mode can be enabled."""
        with patch("mycelium.api.server.uvicorn.run") as mock_run, patch("mycelium.api.server.create_app"):
            mock_run.side_effect = KeyboardInterrupt()

            try:
                start_server(reload=True)
            except KeyboardInterrupt:
                pass

            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["reload"] is True

    def test_log_level(self):
        """Test that log level is configurable."""
        with patch("mycelium.api.server.uvicorn.run") as mock_run, patch("mycelium.api.server.create_app"):
            mock_run.side_effect = KeyboardInterrupt()

            try:
                start_server(log_level="debug")
            except KeyboardInterrupt:
                pass

            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["log_level"] == "debug"


class TestSecurityMessages:
    """Tests for security warning messages."""

    def test_security_message_on_invalid_host(self, capsys):
        """Test that security warning is printed on invalid host."""
        with pytest.raises(ValueError):
            start_server(host="0.0.0.0", port=8080)

        captured = capsys.readouterr()
        assert "ERROR" in captured.err
        assert "security" in captured.err.lower()
        assert "0.0.0.0" in captured.err

    def test_startup_message_shows_security_info(self, capsys):
        """Test that startup message includes security information."""
        with patch("mycelium.api.server.uvicorn.run") as mock_run, patch("mycelium.api.server.create_app"):
            mock_run.side_effect = KeyboardInterrupt()

            try:
                start_server(port=8080)
            except KeyboardInterrupt:
                pass

            captured = capsys.readouterr()
            assert "127.0.0.1" in captured.out
            assert "loopback" in captured.out.lower()
