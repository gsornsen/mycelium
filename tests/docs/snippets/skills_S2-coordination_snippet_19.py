# Source: skills/S2-coordination.md
# Line: 709
# Valid syntax: True
# Has imports: False
# Has assignments: True

# ✅ Good: Minimal, structured context
context = {
    "files": ["auth.py", "models/user.py"],
    "focus_areas": ["password_hashing", "session_management"],
    "standards": {"reference": "OWASP_ASVS_4.0"}
}

# ❌ Bad: Massive, unstructured context
context = {
    "entire_codebase": read_all_files(),  # Too large
    "random_notes": "check security stuff",  # Too vague
}