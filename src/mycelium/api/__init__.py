"""FastAPI-based REST API for Mycelium.

Provides RESTful endpoints for programmatic access to agent and workflow status.
"""

from mycelium.api.app import create_app
from mycelium.api.server import start_server

__all__ = ["create_app", "start_server"]
