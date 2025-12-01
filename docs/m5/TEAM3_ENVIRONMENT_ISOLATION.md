# Team 3: Environment Isolation

## Mission

Implement environment variable isolation and output sanitization for secure agent execution.

## Context

- Agents execute via ProcessManager at `/home/gerald/git/mycelium/src/mycelium/supervisor/manager.py`
- Need to prevent credential leakage in both directions:
  - Block sensitive env vars from reaching agents
  - Sanitize agent output to prevent credential exposure

## Tasks

### 1. Create Isolation Module

**File**: `/home/gerald/git/mycelium/src/mycelium/mcp/isolation.py`

Implement environment isolation:

```python
"""Environment isolation and output sanitization for agent execution.

Prevents credential leakage and enforces security boundaries.
"""

import re
from typing import Any

# Sensitive environment variables to block
BLOCKED_ENV_VARS = [
    # Cloud provider credentials
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "AZURE_CLIENT_SECRET",

    # API keys
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "GITHUB_TOKEN",
    "GITLAB_TOKEN",
    "SLACK_TOKEN",

    # Database credentials
    "DATABASE_URL",
    "REDIS_PASSWORD",
    "POSTGRES_PASSWORD",
    "MYSQL_PASSWORD",

    # General secrets
    "SECRET_KEY",
    "PRIVATE_KEY",
    "API_SECRET",
]

# Patterns for credential detection in output
CREDENTIAL_PATTERNS = [
    # AWS keys
    (r"AKIA[0-9A-Z]{16}", "[AWS_ACCESS_KEY_REDACTED]"),
    (r"aws_secret_access_key\s*=\s*[^\s]+", "aws_secret_access_key=[REDACTED]"),

    # API keys (generic)
    (r"[a-zA-Z0-9_-]*api[_-]?key[a-zA-Z0-9_-]*\s*[:=]\s*['\"]?([a-zA-Z0-9_-]{20,})['\"]?",
     lambda m: m.group(0).replace(m.group(1), "[REDACTED]")),

    # JWT tokens
    (r"eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+", "[JWT_TOKEN_REDACTED]"),

    # Private keys
    (r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----.*?-----END (?:RSA |EC )?PRIVATE KEY-----",
     "[PRIVATE_KEY_REDACTED]"),

    # Generic secrets (long base64/hex strings)
    (r"[a-zA-Z0-9_-]*secret[a-zA-Z0-9_-]*\s*[:=]\s*['\"]?([a-zA-Z0-9+/=]{40,})['\"]?",
     lambda m: m.group(0).replace(m.group(1), "[REDACTED]")),
]

class EnvironmentIsolation:
    """Manage environment isolation for agent execution."""

    def __init__(
        self,
        blocked_vars: list[str] | None = None,
        allowed_vars: list[str] | None = None
    ):
        """Initialize environment isolation.

        Args:
            blocked_vars: Custom list of blocked variables (extends defaults)
            allowed_vars: Explicitly allowed variables (allowlist mode)
        """
        self.blocked_vars = set(BLOCKED_ENV_VARS)
        if blocked_vars:
            self.blocked_vars.update(blocked_vars)

        self.allowed_vars = set(allowed_vars) if allowed_vars else None

    def filter_environment(self, env: dict[str, str]) -> dict[str, str]:
        """Filter environment variables for agent execution.

        Args:
            env: Original environment dictionary

        Returns:
            Filtered environment with sensitive vars removed
        """
        # Implementation requirements:
        # 1. If allowlist mode, only pass allowed_vars
        # 2. Otherwise, remove all blocked_vars
        # 3. Always pass safe variables: PATH, HOME, USER, LANG
        # 4. Log blocked variables (for debugging)
        # 5. Return clean environment
        pass

    def sanitize_output(self, output: str) -> str:
        """Sanitize agent output to remove credentials.

        Args:
            output: Raw agent output

        Returns:
            Sanitized output with credentials redacted
        """
        # Implementation requirements:
        # 1. Apply all CREDENTIAL_PATTERNS
        # 2. For each pattern, replace matches with redaction
        # 3. Support both string and callable replacements
        # 4. Log redactions (for security auditing)
        # 5. Return sanitized output
        pass

    def is_var_blocked(self, var_name: str) -> bool:
        """Check if an environment variable is blocked.

        Args:
            var_name: Variable name to check

        Returns:
            True if blocked, False if allowed
        """
        # Implementation:
        # 1. If allowlist mode, check if in allowed_vars
        # 2. Otherwise, check if in blocked_vars
        pass

    def add_blocked_var(self, var_name: str) -> None:
        """Add a variable to the blocklist.

        Args:
            var_name: Variable name to block
        """
        self.blocked_vars.add(var_name)

    def remove_blocked_var(self, var_name: str) -> None:
        """Remove a variable from the blocklist.

        Args:
            var_name: Variable name to unblock
        """
        self.blocked_vars.discard(var_name)

class OutputSanitizer:
    """Specialized output sanitization for streaming logs."""

    def __init__(self):
        """Initialize sanitizer with credential patterns."""
        self.patterns = [
            (re.compile(pattern, re.DOTALL | re.MULTILINE), replacement)
            for pattern, replacement in CREDENTIAL_PATTERNS
        ]

    def sanitize(self, text: str) -> str:
        """Sanitize text by redacting credentials.

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text
        """
        result = text
        for pattern, replacement in self.patterns:
            if callable(replacement):
                result = pattern.sub(replacement, result)
            else:
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
```

### 2. Integration Points

**ProcessManager Integration**: The isolation module will be used by ProcessManager when starting agents:

```python
# In ProcessManager.start_agent():
from mycelium.mcp.isolation import EnvironmentIsolation

isolation = EnvironmentIsolation()
clean_env = isolation.filter_environment(os.environ.copy())

process = subprocess.Popen(
    command,
    env=clean_env,  # Use filtered environment
    ...
)
```

**Output Sanitization**: Applied when reading agent output:

```python
from mycelium.mcp.isolation import OutputSanitizer

sanitizer = OutputSanitizer()
output = process.stdout.read()
clean_output = sanitizer.sanitize(output)
```

### 3. Testing

**File**: `/home/gerald/git/mycelium/tests/unit/mcp/test_isolation.py`

Test coverage:

- Test environment filtering with blocked vars
- Test environment filtering with allowlist
- Test safe variables always passed (PATH, HOME)
- Test output sanitization for AWS keys
- Test output sanitization for API keys
- Test output sanitization for JWT tokens
- Test output sanitization for private keys
- Test sanitization with callable replacements
- Test is_var_blocked logic
- Test add/remove blocked vars
- Test OutputSanitizer streaming mode

### 4. Security Audit

Create comprehensive test cases for:

- Common credential formats
- Edge cases (embedded credentials)
- Performance with large outputs
- Regex complexity/DoS protection

## Success Criteria

- [ ] EnvironmentIsolation class implemented
- [ ] OutputSanitizer class implemented
- [ ] Comprehensive blocklist of sensitive vars
- [ ] Credential patterns cover common formats
- [ ] All tests pass
- [ ] Integration points documented
- [ ] Security audit completed

## Files to Create

- Create: `/home/gerald/git/mycelium/src/mycelium/mcp/isolation.py`
- Create: `/home/gerald/git/mycelium/tests/unit/mcp/test_isolation.py`

## Coordination

- Update Redis: `mycelium:m5:team3:status` = "in_progress" when starting
- Update Redis: `mycelium:m5:team3:status` = "completed" when done
- Publish event: `mycelium:m5:events` when completed
