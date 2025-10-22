"""Privacy-preserving telemetry infrastructure for Mycelium.

This module provides opt-in telemetry collection with privacy-first design.
All telemetry is DISABLED BY DEFAULT and requires explicit user opt-in.

Privacy Guarantees:
- No PII (Personally Identifiable Information) collected
- No user prompts or responses collected
- No code content or file contents collected
- All identifiers hashed before transmission
- File paths anonymized (usernames stripped)
- Stack traces sanitized
"""

from .client import TelemetryClient
from .config import TelemetryConfig

__all__ = ["TelemetryClient", "TelemetryConfig"]
