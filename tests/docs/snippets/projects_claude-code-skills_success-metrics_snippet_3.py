# Source: projects/claude-code-skills/success-metrics.md
# Line: 429
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Survey responses (1-5 scale)
responses = [5, 4, 5, 4, 3, 5, 4, 5, 4, 4]  # 10 respondents

average_score = sum(responses) / len(responses)
percentage_satisfied = (average_score / 5) * 100

# Success: percentage_satisfied >= 85
