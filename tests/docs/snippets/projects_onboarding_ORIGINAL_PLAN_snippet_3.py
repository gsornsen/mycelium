# Source: projects/onboarding/ORIGINAL_PLAN.md
# Line: 115
# Valid syntax: False
# Has imports: False
# Has assignments: False

# Syntax error: ':' expected after dictionary key (<unknown>, line 18)

# ~/.claude/plugins/mycelium-core/lib/onboarding/detect.py

def detect_services():
    """Detect available services on host system"""
    return {
        "redis": check_redis(),
        "postgres": check_postgres(),
        "temporal": check_temporal(),
        "docker": check_docker(),
        "gpus": detect_gpus(),
        "python": detect_python(),
        "node": detect_node(),
    }

def check_redis():
    """Returns: {"available": bool, "version": str, "port": int}"""
    result = subprocess.run(["redis-cli", "ping"], capture_output=True)
    return {"available": result.returncode == 0, ...}

def detect_gpus():
    """Returns: [{"model": str, "memory_gb": int, "driver": str}]"""
    result = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"], ...)
    # Parse and return GPU list