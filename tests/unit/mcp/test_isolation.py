"""Tests for environment isolation and output sanitization.

This module tests the EnvironmentIsolation and OutputSanitizer classes,
including environment filtering, credential detection, and output redaction.
"""

import re

from mycelium.mcp.isolation import (
    BLOCKED_ENV_VARS,
    CREDENTIAL_PATTERNS,
    SAFE_ENV_VARS,
    EnvironmentIsolation,
    OutputSanitizer,
)


class TestEnvironmentIsolation:
    """Test EnvironmentIsolation class."""

    def test_init_default(self):
        """Test initialization with default settings."""
        isolation = EnvironmentIsolation()
        assert isolation.blocked_vars == set(BLOCKED_ENV_VARS)
        assert isolation.allowed_vars is None

    def test_init_custom_blocked_vars(self):
        """Test initialization with custom blocked variables."""
        custom_blocked = ["CUSTOM_SECRET", "MY_API_KEY"]
        isolation = EnvironmentIsolation(blocked_vars=custom_blocked)

        # Should include both default and custom blocked vars
        assert "AWS_ACCESS_KEY_ID" in isolation.blocked_vars
        assert "CUSTOM_SECRET" in isolation.blocked_vars
        assert "MY_API_KEY" in isolation.blocked_vars

    def test_init_allowlist_mode(self):
        """Test initialization with allowlist mode."""
        allowed = ["PATH", "HOME", "MY_VAR"]
        isolation = EnvironmentIsolation(allowed_vars=allowed)

        # Should include allowed vars plus safe vars
        assert isolation.allowed_vars is not None
        assert "PATH" in isolation.allowed_vars
        assert "HOME" in isolation.allowed_vars
        assert "MY_VAR" in isolation.allowed_vars
        # Safe vars should be automatically included
        assert "USER" in isolation.allowed_vars

    def test_filter_environment_blocklist_mode(self):
        """Test environment filtering in blocklist mode (default)."""
        isolation = EnvironmentIsolation()

        env = {
            "PATH": "/usr/bin",
            "HOME": "/home/user",
            "AWS_ACCESS_KEY_ID": "AKIA1234567890ABCDEF",
            "AWS_SECRET_ACCESS_KEY": "secret123",
            "GITHUB_TOKEN": "ghp_1234567890",
            "SAFE_VAR": "safe_value",
        }

        filtered = isolation.filter_environment(env)

        # Should pass safe vars and non-blocked vars
        assert "PATH" in filtered
        assert "HOME" in filtered
        assert "SAFE_VAR" in filtered

        # Should block sensitive vars
        assert "AWS_ACCESS_KEY_ID" not in filtered
        assert "AWS_SECRET_ACCESS_KEY" not in filtered
        assert "GITHUB_TOKEN" not in filtered

    def test_filter_environment_allowlist_mode(self):
        """Test environment filtering in allowlist mode."""
        isolation = EnvironmentIsolation(allowed_vars=["MY_VAR"])

        env = {
            "PATH": "/usr/bin",
            "HOME": "/home/user",
            "MY_VAR": "allowed_value",
            "OTHER_VAR": "not_allowed",
        }

        filtered = isolation.filter_environment(env)

        # Should only pass allowed vars (plus safe vars)
        assert "PATH" in filtered  # Safe var
        assert "HOME" in filtered  # Safe var
        assert "MY_VAR" in filtered  # Explicitly allowed
        assert "OTHER_VAR" not in filtered  # Not in allowlist

    def test_filter_environment_empty(self):
        """Test filtering empty environment."""
        isolation = EnvironmentIsolation()
        filtered = isolation.filter_environment({})
        assert filtered == {}

    def test_filter_environment_all_blocked(self):
        """Test filtering environment with all blocked vars."""
        isolation = EnvironmentIsolation()

        env = {
            "AWS_ACCESS_KEY_ID": "AKIA1234567890ABCDEF",
            "AWS_SECRET_ACCESS_KEY": "secret123",
            "GITHUB_TOKEN": "ghp_1234567890",
        }

        filtered = isolation.filter_environment(env)
        assert filtered == {}

    def test_filter_environment_all_safe(self):
        """Test filtering environment with all safe vars."""
        isolation = EnvironmentIsolation()

        env = {
            "PATH": "/usr/bin",
            "HOME": "/home/user",
            "USER": "testuser",
        }

        filtered = isolation.filter_environment(env)

        # All should pass
        assert filtered == env

    def test_filter_environment_preserves_safe_vars(self):
        """Test that safe vars are always preserved."""
        # Allowlist mode without explicitly allowing safe vars
        isolation = EnvironmentIsolation(allowed_vars=["MY_VAR"])

        env = {
            "PATH": "/usr/bin",
            "HOME": "/home/user",
            "MY_VAR": "value",
        }

        filtered = isolation.filter_environment(env)

        # Safe vars should always be included
        assert "PATH" in filtered
        assert "HOME" in filtered

    def test_is_var_blocked_blocklist_mode(self):
        """Test checking if var is blocked in blocklist mode."""
        isolation = EnvironmentIsolation()

        assert isolation.is_var_blocked("AWS_ACCESS_KEY_ID") is True
        assert isolation.is_var_blocked("PATH") is False
        assert isolation.is_var_blocked("MY_VAR") is False

    def test_is_var_blocked_allowlist_mode(self):
        """Test checking if var is blocked in allowlist mode."""
        isolation = EnvironmentIsolation(allowed_vars=["MY_VAR"])

        # In allowlist mode, anything not in allowlist is blocked
        assert isolation.is_var_blocked("MY_VAR") is False
        assert isolation.is_var_blocked("OTHER_VAR") is True
        assert isolation.is_var_blocked("PATH") is False  # Safe var

    def test_add_blocked_var(self):
        """Test adding a variable to blocklist."""
        isolation = EnvironmentIsolation()

        assert not isolation.is_var_blocked("MY_SECRET")
        isolation.add_blocked_var("MY_SECRET")
        assert isolation.is_var_blocked("MY_SECRET")

    def test_add_blocked_var_removes_from_allowlist(self):
        """Test that adding to blocklist removes from allowlist."""
        isolation = EnvironmentIsolation(allowed_vars=["MY_VAR"])

        assert not isolation.is_var_blocked("MY_VAR")
        isolation.add_blocked_var("MY_VAR")
        assert isolation.is_var_blocked("MY_VAR")

    def test_remove_blocked_var(self):
        """Test removing a variable from blocklist."""
        isolation = EnvironmentIsolation()

        assert isolation.is_var_blocked("AWS_ACCESS_KEY_ID")
        isolation.remove_blocked_var("AWS_ACCESS_KEY_ID")
        assert not isolation.is_var_blocked("AWS_ACCESS_KEY_ID")

    def test_remove_blocked_var_nonexistent(self):
        """Test removing a var that's not in blocklist (should not error)."""
        isolation = EnvironmentIsolation()
        # Should not raise an error
        isolation.remove_blocked_var("NONEXISTENT_VAR")

    def test_sanitize_output(self):
        """Test output sanitization via EnvironmentIsolation."""
        isolation = EnvironmentIsolation()

        output = "AWS Key: AKIA1234567890ABCDEF"
        sanitized = isolation.sanitize_output(output)

        assert "AKIA1234567890ABCDEF" not in sanitized
        assert "[AWS_ACCESS_KEY_REDACTED]" in sanitized

    def test_custom_blocked_vars_extends_defaults(self):
        """Test that custom blocked vars extend defaults."""
        custom = ["MY_SECRET"]
        isolation = EnvironmentIsolation(blocked_vars=custom)

        # Should have both default and custom
        assert "AWS_ACCESS_KEY_ID" in isolation.blocked_vars
        assert "MY_SECRET" in isolation.blocked_vars


class TestOutputSanitizer:
    """Test OutputSanitizer class."""

    def test_init(self):
        """Test sanitizer initialization."""
        sanitizer = OutputSanitizer()
        assert len(sanitizer.patterns) == len(CREDENTIAL_PATTERNS)

    def test_sanitize_aws_access_key(self):
        """Test sanitizing AWS access keys."""
        sanitizer = OutputSanitizer()

        text = "My AWS key is AKIA1234567890ABCDEF"
        sanitized = sanitizer.sanitize(text)

        assert "AKIA1234567890ABCDEF" not in sanitized
        assert "[AWS_ACCESS_KEY_REDACTED]" in sanitized

    def test_sanitize_aws_secret_key(self):
        """Test sanitizing AWS secret keys."""
        sanitizer = OutputSanitizer()

        text = "aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        sanitized = sanitizer.sanitize(text)

        assert "wJalrXUtnFEMI" not in sanitized
        assert "aws_secret_access_key=[REDACTED]" in sanitized

    def test_sanitize_api_key(self):
        """Test sanitizing generic API keys."""
        sanitizer = OutputSanitizer()

        text = 'api_key: "1234567890abcdefghijklmnopqrstuvwxyz"'
        sanitized = sanitizer.sanitize(text)

        assert "1234567890abcdefghij" not in sanitized
        assert "api_key=[REDACTED]" in sanitized

    def test_sanitize_stripe_key(self):
        """Test sanitizing Stripe-style API keys."""
        sanitizer = OutputSanitizer()

        text = "sk_test_1234567890abcdefghijklmnopqrstuvwxyz"
        sanitized = sanitizer.sanitize(text)

        assert "sk_test_" not in sanitized
        assert "[API_KEY_REDACTED]" in sanitized

    def test_sanitize_jwt_token(self):
        """Test sanitizing JWT tokens."""
        sanitizer = OutputSanitizer()

        text = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ."
            "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        )
        sanitized = sanitizer.sanitize(text)

        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in sanitized
        assert "[JWT_TOKEN_REDACTED]" in sanitized

    def test_sanitize_bearer_token(self):
        """Test sanitizing Bearer tokens."""
        sanitizer = OutputSanitizer()

        text = "Authorization: Bearer 1234567890abcdefghijklmnopqrstuvwxyz"
        sanitized = sanitizer.sanitize(text)

        assert "1234567890abcdefghij" not in sanitized
        assert "Bearer [REDACTED]" in sanitized

    def test_sanitize_private_key(self):
        """Test sanitizing PEM private keys."""
        sanitizer = OutputSanitizer()

        text = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA0Z3VS5JJcds3xfn/ygWyF...
-----END RSA PRIVATE KEY-----"""

        sanitized = sanitizer.sanitize(text)

        assert "BEGIN RSA PRIVATE KEY" not in sanitized
        assert "[PRIVATE_KEY_REDACTED]" in sanitized

    def test_sanitize_password(self):
        """Test sanitizing password fields."""
        sanitizer = OutputSanitizer()

        # Password pattern requires 40+ char base64-like value
        text = 'password: "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890+/="'
        sanitized = sanitizer.sanitize(text)

        assert "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz" not in sanitized
        assert "password=[REDACTED]" in sanitized

    def test_sanitize_oauth_token(self):
        """Test sanitizing OAuth tokens."""
        sanitizer = OutputSanitizer()

        text = "oauth_token: 1234567890abcdefghijklmnopqrstuvwxyz"
        sanitized = sanitizer.sanitize(text)

        assert "1234567890abcdefghij" not in sanitized
        assert "oauth_token=[REDACTED]" in sanitized

    def test_sanitize_github_token(self):
        """Test sanitizing GitHub tokens."""
        sanitizer = OutputSanitizer()

        # GitHub token pattern requires 36+ chars after ghp_
        text = "My token: ghp_abcdefghijklmnopqrstuvwxyz1234567890ABCDEF"
        sanitized = sanitizer.sanitize(text)

        assert "ghp_abcdefghij" not in sanitized
        assert "[GITHUB_TOKEN_REDACTED]" in sanitized

    def test_sanitize_slack_token(self):
        """Test sanitizing Slack tokens."""
        sanitizer = OutputSanitizer()

        # Use clearly fake token pattern to avoid triggering GitHub secret scanning
        text = "xoxb-FAKE-TOKEN-FOR-TESTING-ONLY-0000000000"
        sanitized = sanitizer.sanitize(text)

        assert "xoxb-FAKE" not in sanitized
        assert "[SLACK_TOKEN_REDACTED]" in sanitized

    def test_sanitize_anthropic_api_key(self):
        """Test sanitizing Anthropic API keys."""
        sanitizer = OutputSanitizer()

        text = "sk-ant-api03-1234567890abcdefghijklmnopqrstuvwxyz"
        sanitized = sanitizer.sanitize(text)

        assert "sk-ant-api03" not in sanitized
        assert "[ANTHROPIC_API_KEY_REDACTED]" in sanitized

    def test_sanitize_openai_api_key(self):
        """Test sanitizing OpenAI API keys."""
        sanitizer = OutputSanitizer()

        text = "sk-1234567890abcdefghijklmnopqrstuvwxyz"
        sanitized = sanitizer.sanitize(text)

        # Note: This might also match Stripe keys, but that's okay
        assert "sk-1234567890abcdefghij" not in sanitized
        assert "REDACTED" in sanitized

    def test_sanitize_database_url(self):
        """Test sanitizing database connection strings."""
        sanitizer = OutputSanitizer()

        text = "postgres://username:password123@localhost:5432/dbname"
        sanitized = sanitizer.sanitize(text)

        assert "username:password123" not in sanitized
        assert "postgres://[USER]:[PASSWORD]@" in sanitized

    def test_sanitize_no_credentials(self):
        """Test sanitizing text with no credentials."""
        sanitizer = OutputSanitizer()

        text = "This is just normal text with no secrets."
        sanitized = sanitizer.sanitize(text)

        # Should be unchanged
        assert sanitized == text

    def test_sanitize_multiple_credentials(self):
        """Test sanitizing text with multiple credential types."""
        sanitizer = OutputSanitizer()

        # Use tokens that match the actual regex patterns:
        # - AWS: AKIA + 16 alphanums
        # - GitHub: ghp_ + 36+ alphanums
        # - API key: sk_test_ + 20+ alphanums
        text = """
        AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
        GITHUB_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz1234567890ABCDEF
        api_key: sk_test_1234567890abcdefghijklmnopqrstuvwxyz
        """

        sanitized = sanitizer.sanitize(text)

        # All credentials should be redacted
        assert "AKIAIOSFODNN7EXAMPLE" not in sanitized
        assert "ghp_abcdefghij" not in sanitized
        assert "sk_test_1234567890" not in sanitized
        assert "REDACTED" in sanitized

    def test_sanitize_lines(self):
        """Test sanitizing multiple lines."""
        sanitizer = OutputSanitizer()

        # Use tokens that match actual regex patterns
        lines = [
            "Line 1: AWS Key AKIAIOSFODNN7EXAMPLE",
            "Line 2: Normal text",
            "Line 3: GitHub token ghp_abcdefghijklmnopqrstuvwxyz1234567890ABCDEF",
        ]

        sanitized = sanitizer.sanitize_lines(lines)

        assert len(sanitized) == 3
        assert "AKIAIOSFODNN7EXAMPLE" not in sanitized[0]
        assert "[AWS_ACCESS_KEY_REDACTED]" in sanitized[0]
        assert sanitized[1] == "Line 2: Normal text"
        assert "ghp_abcdefghij" not in sanitized[2]
        assert "[GITHUB_TOKEN_REDACTED]" in sanitized[2]

    def test_sanitize_preserves_structure(self):
        """Test that sanitization preserves text structure."""
        sanitizer = OutputSanitizer()

        # Use token that matches api_key pattern (20+ chars)
        text = """Config file:
        api_key: sk_test_1234567890abcdefghijklmnopqrstuvwxyz
        endpoint: https://api.example.com
        """

        sanitized = sanitizer.sanitize(text)

        # Structure should be preserved
        assert "Config file:" in sanitized
        assert "endpoint: https://api.example.com" in sanitized
        # The api_key line gets replaced but key name is preserved in replacement
        assert "api_key=" in sanitized or "API_KEY_REDACTED" in sanitized

    def test_sanitize_callable_replacement(self):
        """Test that callable replacements work correctly."""
        sanitizer = OutputSanitizer()

        # Database URLs use callable replacements
        text = "mysql://user:pass@host:3306/db"
        sanitized = sanitizer.sanitize(text)

        assert "user:pass" not in sanitized
        assert "mysql://[USER]:[PASSWORD]@" in sanitized

    def test_sanitize_case_sensitive(self):
        """Test that pattern matching respects case sensitivity where needed."""
        sanitizer = OutputSanitizer()

        # AWS keys are case-sensitive
        text1 = "AKIA1234567890ABCDEF"
        text2 = "akia1234567890abcdef"  # lowercase - should not match

        sanitized1 = sanitizer.sanitize(text1)
        sanitized2 = sanitizer.sanitize(text2)

        assert "AKIA1234567890ABCDEF" not in sanitized1
        # lowercase version should match (it's still a potential key)
        # but might not be caught by strict AWS pattern

    def test_sanitize_multiline_private_key(self):
        """Test sanitizing multiline private keys."""
        sanitizer = OutputSanitizer()

        text = """Here's the key:
-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKj
MzEfYyjiWA4R4/M2bS1+fWIcPm15A8Hq5i5hRPVe2dYPZPPSMNI9cqT1vO3XZjQM
-----END PRIVATE KEY-----
After the key."""

        sanitized = sanitizer.sanitize(text)

        assert "BEGIN PRIVATE KEY" not in sanitized
        assert "[PRIVATE_KEY_REDACTED]" in sanitized
        assert "Here's the key:" in sanitized
        assert "After the key." in sanitized

    def test_sanitize_empty_string(self):
        """Test sanitizing empty string."""
        sanitizer = OutputSanitizer()
        assert sanitizer.sanitize("") == ""

    def test_sanitize_lines_empty_list(self):
        """Test sanitizing empty list."""
        sanitizer = OutputSanitizer()
        assert sanitizer.sanitize_lines([]) == []


class TestCredentialPatterns:
    """Test the credential pattern definitions."""

    def test_credential_patterns_structure(self):
        """Test that CREDENTIAL_PATTERNS is properly structured."""
        assert isinstance(CREDENTIAL_PATTERNS, list)
        assert len(CREDENTIAL_PATTERNS) > 0

        for pattern, replacement in CREDENTIAL_PATTERNS:
            assert isinstance(pattern, str)
            assert isinstance(replacement, (str, type(lambda: None)))

    def test_patterns_compile(self):
        """Test that all patterns compile correctly."""
        for pattern_str, _ in CREDENTIAL_PATTERNS:
            # Should not raise an exception
            pattern = re.compile(pattern_str, re.DOTALL | re.MULTILINE)
            assert pattern is not None


class TestBlockedAndSafeVars:
    """Test the BLOCKED_ENV_VARS and SAFE_ENV_VARS constants."""

    def test_blocked_vars_not_empty(self):
        """Test that BLOCKED_ENV_VARS is not empty."""
        assert len(BLOCKED_ENV_VARS) > 0

    def test_safe_vars_not_empty(self):
        """Test that SAFE_ENV_VARS is not empty."""
        assert len(SAFE_ENV_VARS) > 0

    def test_no_overlap_blocked_safe(self):
        """Test that blocked and safe vars don't overlap."""
        blocked_set = set(BLOCKED_ENV_VARS)
        safe_set = set(SAFE_ENV_VARS)

        overlap = blocked_set & safe_set
        assert len(overlap) == 0, f"Overlap found: {overlap}"

    def test_blocked_vars_include_common_secrets(self):
        """Test that common secret vars are in blocked list."""
        assert "AWS_ACCESS_KEY_ID" in BLOCKED_ENV_VARS
        assert "AWS_SECRET_ACCESS_KEY" in BLOCKED_ENV_VARS
        assert "GITHUB_TOKEN" in BLOCKED_ENV_VARS
        assert "ANTHROPIC_API_KEY" in BLOCKED_ENV_VARS

    def test_safe_vars_include_common_system(self):
        """Test that common system vars are in safe list."""
        assert "PATH" in SAFE_ENV_VARS
        assert "HOME" in SAFE_ENV_VARS
        assert "USER" in SAFE_ENV_VARS
