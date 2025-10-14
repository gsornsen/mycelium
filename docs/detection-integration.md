# Detection Integration Guide

Comprehensive guide for integrating Mycelium's service detection system into your applications, scripts, and workflows.

## Table of Contents

- [Overview](#overview)
- [Basic Integration](#basic-integration)
- [Async Integration](#async-integration)
- [Config Integration](#config-integration)
- [Error Handling](#error-handling)
- [Performance Optimization](#performance-optimization)
- [Common Patterns](#common-patterns)
- [Framework Integration](#framework-integration)
- [Testing with Detection](#testing-with-detection)
- [Production Considerations](#production-considerations)

## Overview

The Mycelium detection system provides flexible APIs for integrating service discovery into various application contexts, from simple scripts to complex async applications.

**Key Integration Points:**
- Python applications (sync and async)
- CLI scripts and automation
- Web frameworks (FastAPI, Flask, Django)
- Configuration management systems
- CI/CD pipelines
- Container orchestration
- Monitoring and health checks

## Basic Integration

### Simple Detection

The most basic integration runs detection and checks availability:

```python
from mycelium_onboarding.detection import detect_all

def check_services():
    """Check if required services are available."""
    summary = detect_all()

    if not summary.has_docker:
        raise RuntimeError("Docker is required but not available")

    if not summary.has_redis:
        raise RuntimeError("Redis is required but not available")

    print("All required services available")
    return True

# Run check
check_services()
```

### Conditional Service Usage

Adapt behavior based on detected services:

```python
from mycelium_onboarding.detection import detect_all

def initialize_caching():
    """Initialize caching with Redis if available, else use memory cache."""
    summary = detect_all()

    if summary.has_redis:
        # Use Redis for distributed caching
        import redis
        redis_instance = summary.redis[0]
        cache = redis.Redis(
            host=redis_instance.host,
            port=redis_instance.port
        )
        print(f"Using Redis cache on port {redis_instance.port}")
    else:
        # Fallback to in-memory cache
        from cachetools import TTLCache
        cache = TTLCache(maxsize=1000, ttl=300)
        print("Using in-memory cache (Redis not available)")

    return cache

cache = initialize_caching()
```

### Service Version Requirements

Check for minimum service versions:

```python
from mycelium_onboarding.detection import detect_all
from packaging import version

def check_postgres_version(min_version="15.0"):
    """Ensure PostgreSQL meets minimum version requirement."""
    summary = detect_all()

    if not summary.has_postgres:
        raise RuntimeError("PostgreSQL not available")

    pg_instance = summary.postgres[0]
    if pg_instance.version:
        detected_version = version.parse(pg_instance.version)
        required_version = version.parse(min_version)

        if detected_version < required_version:
            raise RuntimeError(
                f"PostgreSQL {min_version}+ required, found {pg_instance.version}"
            )

    print(f"PostgreSQL {pg_instance.version} meets requirements")
    return True

check_postgres_version()
```

### Multi-Instance Selection

Choose from multiple detected instances:

```python
from mycelium_onboarding.detection import detect_all

def select_redis_instance(prefer_authenticated=True):
    """Select appropriate Redis instance based on preferences."""
    summary = detect_all()

    if not summary.has_redis:
        return None

    # Filter instances based on preferences
    if prefer_authenticated:
        auth_instances = [r for r in summary.redis if r.password_required]
        if auth_instances:
            return auth_instances[0]

    # Default to first available
    return summary.redis[0]

redis_instance = select_redis_instance()
if redis_instance:
    print(f"Using Redis on port {redis_instance.port}")
```

## Async Integration

### Basic Async Detection

Use async detection in async applications:

```python
import asyncio
from mycelium_onboarding.detection import detect_all_async

async def async_service_check():
    """Async service availability check."""
    summary = await detect_all_async()

    services = {
        "docker": summary.has_docker,
        "redis": summary.has_redis,
        "postgres": summary.has_postgres,
        "temporal": summary.has_temporal,
        "gpu": summary.has_gpu,
    }

    return services

# Run in async context
services = asyncio.run(async_service_check())
print(f"Available services: {services}")
```

### FastAPI Integration

Integrate detection with FastAPI health checks:

```python
from fastapi import FastAPI, HTTPException
from mycelium_onboarding.detection import detect_all_async

app = FastAPI()

@app.get("/health")
async def health_check():
    """Health check endpoint with service detection."""
    summary = await detect_all_async()

    return {
        "status": "healthy",
        "services": {
            "docker": summary.has_docker,
            "redis": summary.has_redis,
            "postgres": summary.has_postgres,
            "temporal": summary.has_temporal,
            "gpu": summary.has_gpu,
        },
        "detection_time": summary.detection_time,
    }

@app.get("/health/detailed")
async def detailed_health():
    """Detailed health check with version info."""
    summary = await detect_all_async()

    details = {
        "docker": {
            "available": summary.has_docker,
            "version": summary.docker.version if summary.has_docker else None,
        },
        "redis": {
            "available": summary.has_redis,
            "instances": len(summary.redis),
        },
        "postgres": {
            "available": summary.has_postgres,
            "instances": len(summary.postgres),
        },
    }

    return details

@app.on_event("startup")
async def startup_event():
    """Check required services on startup."""
    summary = await detect_all_async()

    if not summary.has_redis:
        raise RuntimeError("Redis is required but not available")

    print(f"Startup checks passed in {summary.detection_time:.2f}s")
```

### Async with Concurrent Operations

Run detection alongside other async operations:

```python
import asyncio
from mycelium_onboarding.detection import detect_all_async

async def load_config():
    """Load application configuration."""
    await asyncio.sleep(1)  # Simulate config loading
    return {"app": "myapp", "version": "1.0"}

async def initialize_database():
    """Initialize database connection."""
    await asyncio.sleep(1)  # Simulate DB init
    return "db_connection"

async def startup_sequence():
    """Run multiple startup tasks concurrently."""
    # Run all tasks in parallel
    config, db, summary = await asyncio.gather(
        load_config(),
        initialize_database(),
        detect_all_async()
    )

    print(f"Config: {config}")
    print(f"Database: {db}")
    print(f"Services: {summary.has_docker}, {summary.has_redis}")

    return config, db, summary

asyncio.run(startup_sequence())
```

## Config Integration

### Automatic Config Update

Update configuration based on detection:

```python
from mycelium_onboarding.detection import detect_all, update_config_from_detection
from mycelium_onboarding.config.manager import ConfigManager

def auto_configure():
    """Automatically configure services based on detection."""
    # Detect services
    print("Detecting services...")
    summary = detect_all()

    # Load existing config or create new
    manager = ConfigManager()
    try:
        base_config = manager.load()
        print("Loaded existing configuration")
    except FileNotFoundError:
        base_config = None
        print("Creating new configuration")

    # Update config with detected values
    config = update_config_from_detection(summary, base_config)

    # Save updated config
    manager.save(config)
    print("Configuration updated successfully")

    # Report changes
    if summary.has_redis:
        print(f"  Redis: enabled on port {config.services.redis.port}")
    if summary.has_postgres:
        print(f"  PostgreSQL: enabled on port {config.services.postgres.port}")
    if summary.has_temporal:
        print(f"  Temporal: enabled on ports {config.services.temporal.ui_port}/{config.services.temporal.frontend_port}")

    return config

config = auto_configure()
```

### Selective Config Updates

Update only specific configuration sections:

```python
from mycelium_onboarding.detection import detect_all
from mycelium_onboarding.config.manager import ConfigManager

def update_redis_config_only():
    """Update only Redis configuration from detection."""
    summary = detect_all()
    manager = ConfigManager()
    config = manager.load()

    if summary.has_redis:
        redis_instance = summary.redis[0]
        config.services.redis.enabled = True
        config.services.redis.port = redis_instance.port

        if redis_instance.version:
            config.services.redis.version = redis_instance.version

        manager.save(config)
        print(f"Updated Redis config: port {redis_instance.port}")
    else:
        print("Redis not detected, config unchanged")

update_redis_config_only()
```

### Config Validation with Detection

Validate config against actual services:

```python
from mycelium_onboarding.detection import detect_all
from mycelium_onboarding.config.manager import ConfigManager

def validate_config_against_detection():
    """Validate that configured services are actually available."""
    manager = ConfigManager()
    config = manager.load()
    summary = detect_all()

    issues = []

    # Check Redis
    if config.services.redis.enabled and not summary.has_redis:
        issues.append("Redis is enabled in config but not detected")

    # Check PostgreSQL
    if config.services.postgres.enabled and not summary.has_postgres:
        issues.append("PostgreSQL is enabled in config but not detected")

    # Check Temporal
    if config.services.temporal.enabled and not summary.has_temporal:
        issues.append("Temporal is enabled in config but not detected")

    # Check port mismatches
    if summary.has_redis:
        configured_port = config.services.redis.port
        detected_ports = [r.port for r in summary.redis]
        if configured_port not in detected_ports:
            issues.append(
                f"Redis configured on port {configured_port} but detected on {detected_ports}"
            )

    if issues:
        print("Configuration validation issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("Configuration validated successfully")
        return True

validate_config_against_detection()
```

## Error Handling

### Graceful Degradation

Handle service unavailability gracefully:

```python
from mycelium_onboarding.detection import detect_all

def initialize_services_with_fallback():
    """Initialize services with fallback strategies."""
    summary = detect_all()
    services = {}

    # Docker - required
    if not summary.has_docker:
        raise RuntimeError(
            "Docker is required for this application. "
            "Please install Docker and try again."
        )
    services["docker"] = summary.docker

    # Redis - optional with fallback
    if summary.has_redis:
        services["cache"] = "redis"
        print("Using Redis for caching")
    else:
        services["cache"] = "memory"
        print("Warning: Redis not available, using in-memory cache")

    # PostgreSQL - optional with fallback
    if summary.has_postgres:
        services["database"] = "postgresql"
        print("Using PostgreSQL database")
    else:
        services["database"] = "sqlite"
        print("Warning: PostgreSQL not available, using SQLite")

    return services

try:
    services = initialize_services_with_fallback()
except RuntimeError as e:
    print(f"Fatal error: {e}")
    exit(1)
```

### Detailed Error Reporting

Provide detailed error information:

```python
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
```

### Retry Logic

Implement retry logic for transient failures:

```python
import time
from mycelium_onboarding.detection import detect_all

def wait_for_services(required_services, max_wait=60, check_interval=5):
    """Wait for required services to become available."""
    start_time = time.time()

    while time.time() - start_time < max_wait:
        summary = detect_all()

        # Check all required services
        all_available = True
        for service in required_services:
            if service == "docker" and not summary.has_docker:
                all_available = False
            elif service == "redis" and not summary.has_redis:
                all_available = False
            elif service == "postgres" and not summary.has_postgres:
                all_available = False
            elif service == "temporal" and not summary.has_temporal:
                all_available = False

        if all_available:
            print(f"All required services available after {time.time() - start_time:.1f}s")
            return True

        print(f"Waiting for services... ({time.time() - start_time:.1f}s)")
        time.sleep(check_interval)

    print(f"Timeout: Services not available after {max_wait}s")
    return False

# Wait for services
required = ["docker", "redis", "postgres"]
if wait_for_services(required):
    print("Starting application...")
else:
    print("Cannot start: Required services unavailable")
    exit(1)
```

## Performance Optimization

### Caching Detection Results

Cache detection results to avoid repeated checks:

```python
import time
from functools import wraps
from mycelium_onboarding.detection import detect_all

# Simple cache with TTL
_detection_cache = None
_cache_timestamp = 0
_cache_ttl = 60  # seconds

def cached_detect_all(ttl=60):
    """Detect all services with caching."""
    global _detection_cache, _cache_timestamp, _cache_ttl

    _cache_ttl = ttl
    current_time = time.time()

    # Return cached result if still valid
    if _detection_cache and (current_time - _cache_timestamp) < _cache_ttl:
        return _detection_cache

    # Run detection and cache result
    _detection_cache = detect_all()
    _cache_timestamp = current_time

    return _detection_cache

# Usage
summary1 = cached_detect_all(ttl=60)  # Runs detection
summary2 = cached_detect_all(ttl=60)  # Returns cached (fast)
```

### Selective Detection

Run only needed detectors:

```python
from mycelium_onboarding.detection.docker_detector import detect_docker
from mycelium_onboarding.detection.redis_detector import detect_redis

def quick_check():
    """Quick check of only critical services."""
    docker = detect_docker()
    redis = detect_redis()

    if not docker.available:
        raise RuntimeError("Docker required")

    print(f"Docker: {docker.version}")
    print(f"Redis: {'available' if redis.available else 'unavailable'}")

quick_check()
```

### Background Detection

Run detection in background thread:

```python
import threading
from mycelium_onboarding.detection import detect_all

class BackgroundDetector:
    """Run detection in background with periodic updates."""

    def __init__(self, interval=60):
        self.interval = interval
        self.summary = None
        self.running = False
        self.thread = None

    def start(self):
        """Start background detection."""
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop background detection."""
        self.running = False
        if self.thread:
            self.thread.join()

    def _run(self):
        """Background detection loop."""
        while self.running:
            self.summary = detect_all()
            time.sleep(self.interval)

    def get_summary(self):
        """Get latest detection summary."""
        if self.summary is None:
            self.summary = detect_all()
        return self.summary

# Usage
detector = BackgroundDetector(interval=30)
detector.start()

# Later...
summary = detector.get_summary()
print(f"Services: {summary.has_docker}, {summary.has_redis}")

# Cleanup
detector.stop()
```

## Common Patterns

### Pre-flight Checks

Run detection before application startup:

```python
from mycelium_onboarding.detection import detect_all

def preflight_checks():
    """Run pre-flight service checks."""
    print("Running pre-flight checks...")

    summary = detect_all()

    # Define requirements
    requirements = {
        "docker": ("required", summary.has_docker),
        "redis": ("required", summary.has_redis),
        "postgres": ("required", summary.has_postgres),
        "temporal": ("optional", summary.has_temporal),
        "gpu": ("optional", summary.has_gpu),
    }

    # Check requirements
    failed_required = []
    missing_optional = []

    for service, (level, available) in requirements.items():
        if level == "required" and not available:
            failed_required.append(service)
        elif level == "optional" and not available:
            missing_optional.append(service)

    # Report
    if failed_required:
        print(f"❌ Missing required services: {', '.join(failed_required)}")
        return False

    if missing_optional:
        print(f"⚠️  Missing optional services: {', '.join(missing_optional)}")

    print(f"✓ Pre-flight checks passed in {summary.detection_time:.2f}s")
    return True

if __name__ == "__main__":
    if preflight_checks():
        # Start application
        print("Starting application...")
    else:
        print("Cannot start application")
        exit(1)
```

### Service Discovery for Connections

Use detection results to establish connections:

```python
from mycelium_onboarding.detection import detect_all
import redis
import psycopg2

def connect_to_services():
    """Connect to detected services."""
    summary = detect_all()
    connections = {}

    # Connect to Redis
    if summary.has_redis:
        redis_instance = summary.redis[0]
        connections["redis"] = redis.Redis(
            host=redis_instance.host,
            port=redis_instance.port,
            decode_responses=True
        )
        print(f"Connected to Redis on port {redis_instance.port}")

    # Connect to PostgreSQL
    if summary.has_postgres:
        pg_instance = summary.postgres[0]
        connections["postgres"] = psycopg2.connect(
            host=pg_instance.host,
            port=pg_instance.port,
            dbname="postgres",
            user="postgres"
        )
        print(f"Connected to PostgreSQL on port {pg_instance.port}")

    return connections

connections = connect_to_services()
```

### Environment-Specific Configuration

Adapt configuration based on detected environment:

```python
from mycelium_onboarding.detection import detect_all

def determine_environment():
    """Determine environment type based on detected services."""
    summary = detect_all()

    # Development environment
    if summary.has_docker and summary.has_redis and summary.has_postgres:
        if len(summary.redis) == 1 and len(summary.postgres) == 1:
            return "development"

    # Production environment
    if summary.has_redis and summary.has_postgres and summary.has_temporal:
        if len(summary.redis) > 1 or len(summary.postgres) > 1:
            return "production"

    # CI environment
    if summary.has_docker and not summary.has_gpu:
        return "ci"

    return "unknown"

env = determine_environment()
print(f"Detected environment: {env}")
```

## Framework Integration

### Flask Integration

```python
from flask import Flask, jsonify
from mycelium_onboarding.detection import detect_all

app = Flask(__name__)

@app.route("/health")
def health():
    """Health check endpoint."""
    summary = detect_all()
    return jsonify({
        "status": "healthy",
        "services": {
            "docker": summary.has_docker,
            "redis": summary.has_redis,
            "postgres": summary.has_postgres,
        }
    })

@app.before_first_request
def check_services():
    """Check services before handling first request."""
    summary = detect_all()
    if not summary.has_redis:
        app.logger.warning("Redis not available")

if __name__ == "__main__":
    app.run()
```

### Django Integration

```python
# myapp/apps.py
from django.apps import AppConfig
from mycelium_onboarding.detection import detect_all

class MyAppConfig(AppConfig):
    name = "myapp"

    def ready(self):
        """Check services on Django startup."""
        summary = detect_all()

        if not summary.has_redis:
            import warnings
            warnings.warn("Redis not available, some features will be disabled")

        # Store in Django cache
        from django.core.cache import cache
        cache.set("service_detection", {
            "docker": summary.has_docker,
            "redis": summary.has_redis,
            "postgres": summary.has_postgres,
        }, 60)
```

### Celery Integration

```python
# celery.py
from celery import Celery
from mycelium_onboarding.detection import detect_all

app = Celery("myapp")

@app.on_after_configure.connect
def check_broker(sender, **kwargs):
    """Check if broker (Redis) is available."""
    summary = detect_all()

    if not summary.has_redis:
        raise RuntimeError("Redis broker not available")

    print(f"Using Redis broker on port {summary.redis[0].port}")
```

## Testing with Detection

### Mocking Detection Results

Mock detection for unit tests:

```python
# test_myapp.py
import pytest
from unittest.mock import patch
from mycelium_onboarding.detection.docker_detector import DockerDetectionResult

def test_with_docker_available():
    """Test behavior when Docker is available."""
    with patch("mycelium_onboarding.detection.detect_docker") as mock:
        mock.return_value = DockerDetectionResult(
            available=True,
            version="24.0.5",
            socket_path="/var/run/docker.sock",
            error_message=None
        )

        # Your test code here
        from myapp import check_docker
        assert check_docker() == True

def test_with_docker_unavailable():
    """Test behavior when Docker is unavailable."""
    with patch("mycelium_onboarding.detection.detect_docker") as mock:
        mock.return_value = DockerDetectionResult(
            available=False,
            version=None,
            socket_path=None,
            error_message="Docker not running"
        )

        # Your test code here
        from myapp import check_docker
        with pytest.raises(RuntimeError):
            check_docker()
```

### Fixture for Tests

Create pytest fixtures:

```python
# conftest.py
import pytest
from mycelium_onboarding.detection import DetectionSummary
from mycelium_onboarding.detection.docker_detector import DockerDetectionResult
# ... import other result types

@pytest.fixture
def all_services_available():
    """Fixture with all services available."""
    return DetectionSummary(
        docker=DockerDetectionResult(available=True, version="24.0.5", socket_path="/var/run/docker.sock", error_message=None),
        redis=[RedisDetectionResult(available=True, host="localhost", port=6379, version="7.2.3", password_required=False, error_message=None)],
        postgres=[PostgresDetectionResult(available=True, host="localhost", port=5432, version="15.4", authentication_method="trust", error_message=None)],
        temporal=TemporalDetectionResult(available=True, frontend_port=7233, ui_port=8233, version="1.22.3", error_message=None),
        gpu=GPUDetectionResult(available=False, gpus=[], total_memory_mb=0, error_message="No GPU"),
        detection_time=2.0
    )

# Use in tests
def test_with_services(all_services_available):
    """Test using the fixture."""
    assert all_services_available.has_docker
    assert all_services_available.has_redis
```

## Production Considerations

### Health Check Endpoints

Implement comprehensive health checks:

```python
from fastapi import FastAPI, status
from mycelium_onboarding.detection import detect_all

app = FastAPI()

@app.get("/health/liveness")
async def liveness():
    """Liveness probe - is the application running?"""
    return {"status": "alive"}

@app.get("/health/readiness")
async def readiness():
    """Readiness probe - can the application serve traffic?"""
    summary = detect_all()

    # Check critical services
    if not summary.has_redis or not summary.has_postgres:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not ready", "reason": "required services unavailable"}
        )

    return {"status": "ready"}

@app.get("/health/startup")
async def startup():
    """Startup probe - has initialization completed?"""
    # Perform full detection
    summary = detect_all()

    if summary.detection_time > 10.0:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "starting", "reason": "detection too slow"}
        )

    return {"status": "started"}
```

### Metrics Collection

Export detection metrics:

```python
from prometheus_client import Gauge, Counter
from mycelium_onboarding.detection import detect_all

# Define metrics
docker_available = Gauge("mycelium_docker_available", "Docker availability")
redis_available = Gauge("mycelium_redis_available", "Redis availability")
detection_time = Gauge("mycelium_detection_time_seconds", "Detection time")
detection_count = Counter("mycelium_detection_total", "Total detections")

def update_metrics():
    """Update Prometheus metrics from detection."""
    summary = detect_all()

    docker_available.set(1 if summary.has_docker else 0)
    redis_available.set(1 if summary.has_redis else 0)
    detection_time.set(summary.detection_time)
    detection_count.inc()

# Run periodically
import schedule
schedule.every(60).seconds.do(update_metrics)
```

### Graceful Shutdown

Handle detection during shutdown:

```python
import signal
import sys
from mycelium_onboarding.detection import detect_all

class Application:
    def __init__(self):
        self.running = True
        self.services = None

    def startup(self):
        """Application startup."""
        print("Detecting services...")
        summary = detect_all()
        self.services = summary

        # Register signal handlers
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

    def shutdown(self, signum, frame):
        """Graceful shutdown."""
        print("Shutting down...")
        self.running = False
        sys.exit(0)

    def run(self):
        """Application main loop."""
        self.startup()
        while self.running:
            # Application logic
            time.sleep(1)

app = Application()
app.run()
```

## See Also

- [Detection Guide](detection-guide.md) - User guide with CLI examples
- [API Reference](detection-reference.md) - Complete API documentation
- [Configuration Guide](configuration-guide.md) - Config system integration
- [Troubleshooting](troubleshooting-environment.md) - Common issues and solutions

---

For issues or contributions, visit: https://github.com/gsornsen/mycelium
