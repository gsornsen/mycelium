# Source: projects/onboarding/ORIGINAL_PLAN.md
# Line: 1206
# Valid syntax: True
# Has imports: False
# Has assignments: True

# tests/test_coordination.py
async def test_full_coordination_flow():
    """Test complete onboarding -> test -> validation flow"""

    # 1. Run onboarding (non-interactive)
    config = await run_onboarding(interactive=False)

    # 2. Start services
    await start_services(config)

    # 3. Run coordination test
    test_result = await run_mycelium_test()

    # 4. Validate results
    assert test_result.success is True
    assert test_result.agents_responded == 5

    # 5. Cleanup
    await stop_services(config)