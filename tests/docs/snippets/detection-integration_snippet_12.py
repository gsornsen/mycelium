# Source: detection-integration.md
# Line: 447
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.detection import detect_all

def diagnose_service_issues():
    """Diagnose and report service availability issues."""
    summary = detect_all()

    print("Service Diagnostics:")
    print("=" * 60)

    # Docker
    if not summary.has_docker:
        print("❌ Docker: Not Available")
        if summary.docker.error_message:
            print(f"   Error: {summary.docker.error_message}")
        print("   Solution: Install Docker or start Docker daemon")
    else:
        print(f"✓ Docker: {summary.docker.version}")

    # Redis
    if not summary.has_redis:
        print("❌ Redis: Not Available")
        print("   Solution: Start Redis on port 6379, 6380, or 6381")
    else:
        print(f"✓ Redis: {len(summary.redis)} instance(s)")
        for redis in summary.redis:
            auth = " (auth required)" if redis.password_required else ""
            print(f"   - Port {redis.port}: {redis.version}{auth}")

    # PostgreSQL
    if not summary.has_postgres:
        print("❌ PostgreSQL: Not Available")
        print("   Solution: Start PostgreSQL on port 5432 or 5433")
    else:
        print(f"✓ PostgreSQL: {len(summary.postgres)} instance(s)")
        for pg in summary.postgres:
            print(f"   - Port {pg.port}: {pg.version}")

    # Temporal
    if not summary.has_temporal:
        print("❌ Temporal: Not Available")
        if summary.temporal.error_message:
            print(f"   Error: {summary.temporal.error_message}")
        print("   Solution: Start Temporal server")
    else:
        print(f"✓ Temporal: {summary.temporal.version}")

    # GPU
    if not summary.has_gpu:
        print("ℹ️  GPU: Not Available (optional)")
        if summary.gpu.error_message:
            print(f"   Info: {summary.gpu.error_message}")
    else:
        print(f"✓ GPU: {len(summary.gpu.gpus)} device(s)")

diagnose_service_issues()