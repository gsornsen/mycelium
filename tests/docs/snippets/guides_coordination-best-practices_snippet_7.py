# Source: guides/coordination-best-practices.md
# Line: 265
# Valid syntax: True
# Has imports: False
# Has assignments: True

# ✅ GOOD: Minimal, relevant context
context = {
    "files": ["auth.py", "models/user.py"],  # Only relevant files
    "focus_areas": ["password_hashing", "session_management"],
    "security_standard": "OWASP_ASVS_4.0",
    "current_issues": [
        "Password stored without salt",
        "Session tokens not rotating"
    ]
}

result = handoff_to_agent(
    target_agent="security-expert",
    task="Security audit of authentication system",
    context=context
)

# ❌ BAD: Excessive context
context = {
    "entire_codebase": read_all_files(),  # Unnecessary
    "git_history": get_full_git_log(),  # Too much
    "dependency_tree": get_all_dependencies(),  # Irrelevant
    "random_notes": "check security maybe?",  # Unstructured
    "last_10_conversations": [...],  # Historical clutter
}