"""Environment isolation and output sanitization for agent execution.

Prevents credential leakage and enforces security boundaries.
"""

import re
from collections.abc import Callable

# Sensitive environment variables to block
BLOCKED_ENV_VARS = [
    # Cloud provider credentials
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "GOOGLE_API_KEY",
    "AZURE_CLIENT_SECRET",
    "AZURE_CLIENT_ID",
    "AZURE_TENANT_ID",
    # API keys
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "OPENAI_ORG_ID",
    "GITHUB_TOKEN",
    "GITLAB_TOKEN",
    "SLACK_TOKEN",
    "SLACK_BOT_TOKEN",
    "DISCORD_TOKEN",
    # Database credentials
    "DATABASE_URL",
    "REDIS_PASSWORD",
    "POSTGRES_PASSWORD",
    "MYSQL_PASSWORD",
    "MONGODB_PASSWORD",
    "DB_PASSWORD",
    # General secrets
    "SECRET_KEY",
    "SECRET_KEY_BASE",
    "PRIVATE_KEY",
    "API_SECRET",
    "JWT_SECRET",
    "ENCRYPTION_KEY",
    "SESSION_SECRET",
]

# Safe environment variables that should always be passed
SAFE_ENV_VARS = [
    "PATH",
    "HOME",
    "USER",
    "LANG",
    "LC_ALL",
    "SHELL",
    "TERM",
    "PWD",
    "OLDPWD",
    "TMPDIR",
    "TMP",
    "TEMP",
]

# Patterns for credential detection in output
# Each pattern is (regex, replacement)
# Replacement can be a string or a callable that takes the match and returns a string
CREDENTIAL_PATTERNS: list[tuple[str, str | Callable[[re.Match[str]], str]]] = [
    # AWS access keys
    (r"AKIA[0-9A-Z]{16}", "[AWS_ACCESS_KEY_REDACTED]"),
    (r"aws_secret_access_key\s*=\s*[^\s]+", "aws_secret_access_key=[REDACTED]"),
    # Generic API keys (with common prefixes)
    (r"(api[_-]?key|apikey)\s*[:=]\s*['\"]?([a-zA-Z0-9_-]{20,})['\"]?", lambda m: f"{m.group(1)}=[REDACTED]"),
    (r"(sk|pk)_(?:test|live)_[a-zA-Z0-9]{20,}", "[API_KEY_REDACTED]"),
    # JWT tokens
    (r"eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+", "[JWT_TOKEN_REDACTED]"),
    # Bearer tokens
    (r"Bearer\s+[a-zA-Z0-9_-]{20,}", "Bearer [REDACTED]"),
    # Private keys (PEM format)
    (
        r"-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----.*?-----END (?:RSA |EC |DSA )?PRIVATE KEY-----",
        "[PRIVATE_KEY_REDACTED]",
    ),
    # Generic secrets (long base64/hex strings)
    (r"(secret|password|passwd|pwd)\s*[:=]\s*['\"]?([a-zA-Z0-9+/=]{40,})['\"]?", lambda m: f"{m.group(1)}=[REDACTED]"),
    # OAuth tokens
    (r"oauth_token\s*[:=]\s*['\"]?([a-zA-Z0-9_-]{20,})['\"]?", "oauth_token=[REDACTED]"),
    # GitHub tokens
    (r"gh[ps]_[a-zA-Z0-9]{36,}", "[GITHUB_TOKEN_REDACTED]"),
    # Slack tokens
    (r"xox[baprs]-[a-zA-Z0-9-]+", "[SLACK_TOKEN_REDACTED]"),
    # Anthropic API keys
    (r"sk-ant-[a-zA-Z0-9_-]+", "[ANTHROPIC_API_KEY_REDACTED]"),
    # OpenAI API keys
    (r"sk-[a-zA-Z0-9]{32,}", "[OPENAI_API_KEY_REDACTED]"),
    # Database connection strings
    (r"(postgres|mysql|mongodb)://[^@]+:[^@]+@", lambda m: f"{m.group(1)}://[USER]:[PASSWORD]@"),
]


class EnvironmentIsolation:
    """Manage environment isolation for agent execution."""

    def __init__(self, blocked_vars: list[str] | None = None, allowed_vars: list[str] | None = None):
        """Initialize environment isolation.

        Args:
            blocked_vars: Custom list of blocked variables (extends defaults)
            allowed_vars: Explicitly allowed variables (allowlist mode)
        """
        self.blocked_vars = set(BLOCKED_ENV_VARS)
        if blocked_vars:
            self.blocked_vars.update(blocked_vars)

        # If allowlist is provided, always include safe vars
        self.allowed_vars: set[str] | None
        if allowed_vars is not None:
            self.allowed_vars = set(allowed_vars) | set(SAFE_ENV_VARS)
        else:
            self.allowed_vars = None

    def filter_environment(self, env: dict[str, str]) -> dict[str, str]:
        """Filter environment variables for agent execution.

        Args:
            env: Original environment dictionary

        Returns:
            Filtered environment with sensitive vars removed
        """
        filtered = {}

        for key, value in env.items():
            # Allowlist mode: only pass allowed vars
            if self.allowed_vars is not None:
                if key in self.allowed_vars:
                    filtered[key] = value
                # Log blocked (for debugging)
                # else:
                #     print(f"Blocked env var: {key} (not in allowlist)")

            # Blocklist mode: pass everything except blocked vars
            elif key not in self.blocked_vars:
                filtered[key] = value
                # Log blocked (for debugging)
                # else:
                #     print(f"Blocked env var: {key}")

        # Ensure safe variables are always present
        for safe_var in SAFE_ENV_VARS:
            if safe_var in env and safe_var not in filtered:
                filtered[safe_var] = env[safe_var]

        return filtered

    def sanitize_output(self, output: str) -> str:
        """Sanitize agent output to remove credentials.

        Args:
            output: Raw agent output

        Returns:
            Sanitized output with credentials redacted
        """
        sanitizer = OutputSanitizer()
        return sanitizer.sanitize(output)

    def is_var_blocked(self, var_name: str) -> bool:
        """Check if an environment variable is blocked.

        Args:
            var_name: Variable name to check

        Returns:
            True if blocked, False if allowed
        """
        # Allowlist mode
        if self.allowed_vars is not None:
            return var_name not in self.allowed_vars

        # Blocklist mode
        return var_name in self.blocked_vars

    def add_blocked_var(self, var_name: str) -> None:
        """Add a variable to the blocklist.

        Args:
            var_name: Variable name to block
        """
        self.blocked_vars.add(var_name)

        # If in allowlist mode, remove from allowlist
        if self.allowed_vars is not None and var_name in self.allowed_vars:
            self.allowed_vars.remove(var_name)

    def remove_blocked_var(self, var_name: str) -> None:
        """Remove a variable from the blocklist.

        Args:
            var_name: Variable name to unblock
        """
        self.blocked_vars.discard(var_name)


class OutputSanitizer:
    """Specialized output sanitization for streaming logs."""

    def __init__(self) -> None:
        """Initialize sanitizer with credential patterns."""
        self.patterns: list[tuple[re.Pattern[str], str | Callable[[re.Match[str]], str]]] = [
            (re.compile(pattern, re.DOTALL | re.MULTILINE), replacement) for pattern, replacement in CREDENTIAL_PATTERNS
        ]

    def sanitize(self, text: str) -> str:
        """Sanitize text by redacting credentials.

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text with credentials redacted
        """
        result = text

        for pattern, replacement in self.patterns:
            result = pattern.sub(replacement, result)

        return result

    def sanitize_lines(self, lines: list[str]) -> list[str]:
        """Sanitize multiple lines of text.

        Args:
            lines: List of text lines

        Returns:
            List of sanitized lines
        """
        return [self.sanitize(line) for line in lines]
