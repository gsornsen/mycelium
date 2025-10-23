# Source: projects/claude-code-skills/success-metrics.md
# Line: 401
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Session token consumption
baseline_tokens = 21150  # Phase 1 with lazy loading
current_tokens = measure_session_tokens()

reduction_percentage = ((baseline_tokens - current_tokens) / baseline_tokens) * 100

# Success: reduction_percentage >= 40 for M03