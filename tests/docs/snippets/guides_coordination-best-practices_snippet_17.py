# Source: guides/coordination-best-practices.md
# Line: 681
# Valid syntax: True
# Has imports: False
# Has assignments: True

# ✅ GOOD: Reference sensitive data indirectly
context = {
    "database_config_path": "config/database.yml",  # Reference
    "credentials_source": "vault://prod/db-credentials",  # Secure vault
    "redacted_query_log": "logs/queries_redacted.txt"  # Pre-redacted
}

# ❌ BAD: Sensitive data in context
context = {
    "database_password": "super_secret_123",  # Exposed!
    "api_keys": ["key1", "key2", "key3"],  # Exposed!
    "user_data": [
        {"email": "user@example.com", "ssn": "123-45-6789"}  # PII!
    ]
}
