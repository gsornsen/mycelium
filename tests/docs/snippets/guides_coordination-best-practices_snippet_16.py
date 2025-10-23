# Source: guides/coordination-best-practices.md
# Line: 653
# Valid syntax: True
# Has imports: False
# Has assignments: True

# ✅ GOOD: Minimal access
context = {
    "files": ["specific/file.py"],  # Only files needed
    "permissions": ["read"],  # Read-only
    "scope": "security_audit_only"  # Limited scope
}

result = handoff_to_agent(
    target_agent="security-expert",
    task="Audit authentication in file.py",
    context=context
)

# ❌ BAD: Excessive access
context = {
    "files": get_all_files(),  # Everything
    "permissions": ["read", "write", "execute"],  # Too much
    "scope": "unlimited"  # No boundaries
}