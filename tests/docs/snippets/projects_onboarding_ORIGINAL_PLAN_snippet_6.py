# Source: projects/onboarding/ORIGINAL_PLAN.md
# Line: 1167
# Valid syntax: True
# Has imports: False
# Has assignments: True

# tests/test_detection.py
def test_detect_redis_running():
    result = detect_services()
    assert result["redis"]["available"] is True

def test_detect_gpu():
    gpus = detect_gpus()
    assert len(gpus) > 0
    assert gpus[0]["model"] == "NVIDIA RTX 4090"