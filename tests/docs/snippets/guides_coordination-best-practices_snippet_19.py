# Source: guides/coordination-best-practices.md
# Line: 754
# Valid syntax: False
# Has imports: False
# Has assignments: False

# Syntax error: invalid decimal literal (<unknown>, line 34)

# ✅ GOOD: Incremental testing
def test_code_review_workflow():
    # Test step 1 alone
    step1 = coordinate_workflow(
        steps=[
            {"agent": "python-pro", "task": "Review code style"}
        ]
    )
    assert step1["status"] == "completed"

    # Test steps 1-2
    step1_2 = coordinate_workflow(
        steps=[
            {"agent": "python-pro", "task": "Review code style"},
            {
                "agent": "security-expert",
                "task": "Security audit",
                "depends_on": ["step-0"]
            }
        ]
    )
    assert step1_2["status"] == "completed"
    assert len(step1_2["results"]) == 2

    # Test full workflow
    full_workflow = coordinate_workflow(
        steps=[...all_steps]
    )
    assert full_workflow["status"] == "completed"

# ❌ BAD: Test everything at once
def test_code_review_workflow():
    workflow = coordinate_workflow(
        steps=[...20_complex_steps]
    )
    assert workflow["status"] == "completed"  # Hard to debug if fails