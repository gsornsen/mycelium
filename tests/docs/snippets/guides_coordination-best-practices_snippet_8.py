# Source: guides/coordination-best-practices.md
# Line: 299
# Valid syntax: True
# Has imports: False
# Has assignments: True

# ✅ GOOD: Structured context with schema
SECURITY_AUDIT_CONTEXT = {
    "files": List[str],           # Files to audit
    "focus_areas": List[str],     # Security domains
    "standards": str,             # Compliance standard
    "known_issues": List[Dict],   # Previous findings
    "constraints": Dict           # Time, scope, etc.
}

context = {
    "files": ["auth.py", "api/endpoints.py"],
    "focus_areas": ["authentication", "authorization", "input_validation"],
    "standards": "OWASP_ASVS_4.0",
    "known_issues": [
        {
            "type": "SQL_INJECTION",
            "file": "api/search.py",
            "line": 42,
            "severity": "CRITICAL"
        }
    ],
    "constraints": {
        "time_limit_hours": 2,
        "scope": "authentication_only"
    }
}

# ❌ BAD: Unstructured context
context = {
    "stuff": "some files and things",
    "info": ["random", "data", 123, None, True],
    "notes": "check security things I guess",
}