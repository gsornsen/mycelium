"""Privacy-preserving anonymization utilities.

This module provides functions to anonymize sensitive data before transmission.
It ensures that no PII or sensitive information is ever sent to telemetry endpoints.

Privacy principles:
- Hash all user-specific identifiers
- Strip file paths containing usernames
- Anonymize stack traces
- Never collect code content or user input
"""

import hashlib
import re
from typing import Any


class DataAnonymizer:
    """Anonymizes sensitive data before telemetry transmission."""

    def __init__(self, salt: str) -> None:
        """Initialize anonymizer with salt.

        Args:
            salt: Salt for hashing identifiers
        """
        self.salt = salt
        self._path_pattern = re.compile(r'(?:File |at |in )"([^"]+)"', re.IGNORECASE)

    def hash_identifier(self, identifier: str) -> str:
        """Hash an identifier with salt.

        Args:
            identifier: The identifier to hash (e.g., user_id, agent_id)

        Returns:
            SHA-256 hash of the identifier with salt
        """
        combined = f"{identifier}{self.salt}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def anonymize_file_path(self, path: str) -> str:
        """Anonymize a file path by removing username and sensitive directories.

        Args:
            path: The file path to anonymize

        Returns:
            Anonymized path with sensitive parts replaced

        Examples:
            >>> anonymizer = DataAnonymizer("test_salt")
            >>> anonymizer.anonymize_file_path("/home/john/project/file.py")
            '<user>/project/file.py'
            >>> anonymizer.anonymize_file_path("C:\\Users\\jane\\Documents\\code.py")
            '<user>/Documents/code.py'
        """
        original_path = path

        # Replace Unix home directories (/home/username or /Users/username)
        path = re.sub(r"/(?:home|Users)/([^/]+)/", "<user>/", path, flags=re.IGNORECASE)

        # Replace Windows user directories (C:\Users\username or Users\username)
        path = re.sub(
            r"(?:[A-Z]:[/\\])?Users[/\\]([^/\\]+)[/\\]",
            "<user>/",
            path,
            flags=re.IGNORECASE,
        )

        # If path still starts with absolute indicators, remove them
        path = re.sub(r"^(?:[A-Z]:|/)", "", path)

        # Remove leading slashes/backslashes
        path = path.lstrip("/\\")

        # Normalize separators to forward slashes
        path = path.replace("\\", "/")

        # If anonymization didn't work, try keeping only last 3 path components
        if path == original_path or "<user>" not in path:
            try:
                parts = original_path.replace("\\", "/").split("/")
                parts = [p for p in parts if p and p not in ("C:", "D:", "")]
                if len(parts) > 3:
                    path = "/".join(parts[-3:])
                else:
                    path = "/".join(parts)
            except Exception:
                pass

        return path

    def anonymize_stack_trace(self, trace: str) -> str:
        """Anonymize a stack trace by removing file paths and sensitive info.

        Args:
            trace: The stack trace to anonymize

        Returns:
            Anonymized stack trace

        Examples:
            >>> anonymizer = DataAnonymizer("test_salt")
            >>> trace = 'File "/home/user/project/file.py", line 42'
            >>> anonymizer.anonymize_stack_trace(trace)
            'File "<user>/project/file.py", line 42'
        """

        def replace_path(match: re.Match[str]) -> str:
            """Replace matched path with anonymized version."""
            path = match.group(1)
            anonymized = self.anonymize_file_path(path)
            return match.group(0).replace(path, anonymized)

        # Anonymize file paths in stack trace
        trace = self._path_pattern.sub(replace_path, trace)

        # Also anonymize any error messages within the stack trace
        # (which may contain emails, paths, etc.)
        trace = self._anonymize_message(trace)

        return trace

    def anonymize_error(
        self, error_type: str, error_message: str, stack_trace: str | None = None
    ) -> dict[str, Any]:
        """Anonymize error information.

        Args:
            error_type: Type of error (e.g., 'ValueError')
            error_message: Error message
            stack_trace: Optional stack trace

        Returns:
            Dictionary with anonymized error data
        """
        # Keep error type as-is (it's not sensitive)
        anonymized = {
            "error_type": error_type,
            # Remove any file paths from error message
            "error_message": self._anonymize_message(error_message),
        }

        if stack_trace:
            anonymized["stack_trace"] = self.anonymize_stack_trace(stack_trace)

        return anonymized

    def _anonymize_message(self, message: str) -> str:
        """Anonymize an error message by removing file paths.

        Args:
            message: The error message to anonymize

        Returns:
            Anonymized message
        """
        # Replace file paths in message (both quoted and unquoted)
        # First handle quoted paths
        message = self._path_pattern.sub(
            lambda m: m.group(0).replace(
                m.group(1), self.anonymize_file_path(m.group(1))
            ),
            message,
        )

        # Then handle unquoted Unix paths
        message = re.sub(
            r"(/(?:home|Users)/[^\s]+)",
            lambda m: self.anonymize_file_path(m.group(1)),
            message,
            flags=re.IGNORECASE,
        )

        # Handle unquoted Windows paths
        message = re.sub(
            r"([A-Z]:[/\\][^\s]+)",
            lambda m: self.anonymize_file_path(m.group(1)),
            message,
        )

        # Remove passwords and credentials from connection strings
        message = re.sub(r"://[^:]+:([^@]+)@", "://<user>:<password>@", message)

        # Remove any potential email addresses
        message = re.sub(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "<email>", message
        )

        return message

    def anonymize_agent_usage(
        self, agent_id: str, operation: str, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Anonymize agent usage data.

        Args:
            agent_id: Agent identifier
            operation: Operation performed
            metadata: Optional metadata (will be filtered for sensitive data)

        Returns:
            Dictionary with anonymized agent usage data
        """
        anonymized = {
            "agent_id_hash": self.hash_identifier(agent_id),
            "operation": operation,
        }

        if metadata:
            # Filter metadata to remove any sensitive fields
            safe_metadata = self._filter_safe_metadata(metadata)
            if safe_metadata:
                anonymized["metadata"] = safe_metadata

        return anonymized

    def _filter_safe_metadata(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """Filter metadata to keep only safe, non-sensitive fields.

        Args:
            metadata: Raw metadata dictionary

        Returns:
            Filtered metadata with only safe fields
        """
        # Allowlist of safe metadata keys
        safe_keys = {
            "duration_ms",
            "success",
            "retry_count",
            "cache_hit",
            "result_count",
            "status_code",
        }

        return {
            k: v
            for k, v in metadata.items()
            if k in safe_keys and not isinstance(v, (dict, list))
        }

    def anonymize_performance_metric(
        self,
        metric_name: str,
        value: float,
        unit: str,
        tags: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Anonymize performance metric data.

        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Unit of measurement
            tags: Optional tags for the metric

        Returns:
            Dictionary with anonymized metric data
        """
        anonymized = {
            "metric_name": metric_name,
            "value": value,
            "unit": unit,
        }

        if tags:
            # Hash any identifier-like tags
            anonymized_tags = {}
            for k, v in tags.items():
                if k.endswith("_id") or k == "user" or k == "agent":
                    anonymized_tags[k] = self.hash_identifier(v)
                else:
                    anonymized_tags[k] = v
            anonymized["tags"] = anonymized_tags

        return anonymized
