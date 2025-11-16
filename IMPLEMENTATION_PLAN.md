# Service Detection Fix - Implementation Plan

## Quick Reference

**Issue:** Docker container `mycelium-postgres` running but detection marked as STOPPED → ALONGSIDE strategy chosen
incorrectly

**Root Cause:** Docker detection only checks image name, not container name

**Fix:** 3-line change + comprehensive improvements

**Time Estimate:** 4 hours for P0 (critical fix)

______________________________________________________________________

## Phase 1: Critical Fix (P0) - 4 hours

### Change 1: Fix Docker Container Name Matching

**File:** `/home/gerald/git/mycelium/mycelium_onboarding/deployment/strategy/detector.py`

**Line:** 460

**Current Code:**

```python
def _analyze_docker_container(self, container: Dict[str, Any]) -> Optional[DetectedService]:
    """Analyze a Docker container to detect service type."""
    image = container.get("Image", "").lower()
    names = container.get("Names", "").lower()
    ports = container.get("Ports", "")

    # Detect PostgreSQL container
    if "postgres" in image or "postgresql" in image:
        return self._create_docker_service(
            container,
            ServiceType.POSTGRESQL,
            default_port=5432
        )
```

**New Code:**

```python
def _analyze_docker_container(self, container: Dict[str, Any]) -> Optional[DetectedService]:
    """Analyze a Docker container to detect service type."""
    image = container.get("Image", "").lower()
    names = container.get("Names", "").lower()
    ports = container.get("Ports", "")

    # Detect PostgreSQL container (check both image AND name)
    if (
        "postgres" in image or
        "postgresql" in image or
        "pgvector" in image or
        "postgis" in image or
        "postgres" in names  # FIX: Check container name too!
    ):
        return self._create_docker_service(
            container,
            ServiceType.POSTGRESQL,
            default_port=5432
        )
```

**Test:**

```bash
# Before:
mycelium deploy plan
# Output: postgres: ALONGSIDE

# After:
mycelium deploy plan
# Output: postgres: REUSE - Compatible PostgreSQL running in Docker container 'mycelium-postgres'
```

**Time:** 15 minutes

______________________________________________________________________

### Change 2: Improve PostgreSQL Status Determination

**File:** `/home/gerald/git/mycelium/mycelium_onboarding/deployment/strategy/detector.py`

**Lines:** 195-221

**Current Code:**

```python
# Try to check service status
status_result = subprocess.run(
    ["pg_isready"],
    capture_output=True,
    text=True,
    check=False
)

if status_result.returncode == 0:
    status = ServiceStatus.RUNNING
    # Try to get PID
    pid_result = subprocess.run(
        ["pgrep", "-f", "postgres"],
        capture_output=True,
        text=True,
        check=False
    )
    if pid_result.returncode == 0 and pid_result.stdout:
        pid = int(pid_result.stdout.strip().split()[0])
else:
    status = ServiceStatus.STOPPED
```

**New Code:**

```python
# Determine status using multiple checks
status, pid = self._determine_postgresql_status()

# ... (after the _detect_postgresql method, add new helper)

def _determine_postgresql_status(self) -> Tuple[ServiceStatus, Optional[int]]:
    """Determine PostgreSQL status using multiple checks.

    Returns:
        (status, pid) tuple
    """
    # Check 1: Is process running?
    pid_result = subprocess.run(
        ["pgrep", "-f", "postgres"],
        capture_output=True,
        text=True,
        check=False,
        timeout=5
    )

    process_running = pid_result.returncode == 0
    pid = None

    if process_running and pid_result.stdout:
        try:
            pid = int(pid_result.stdout.strip().split()[0])
        except (ValueError, IndexError):
            pass

    # Check 2: Can we connect?
    pg_isready_result = subprocess.run(
        ["pg_isready"],
        capture_output=True,
        text=True,
        check=False,
        timeout=5
    )

    can_connect = pg_isready_result.returncode == 0

    # Determine status from both checks
    if process_running and can_connect:
        return ServiceStatus.RUNNING, pid
    elif process_running and not can_connect:
        # Process exists but we can't connect (auth, SSL, etc.)
        logger.info(
            "PostgreSQL process detected but pg_isready failed. "
            "Marking as RUNNING (may require authentication)."
        )
        return ServiceStatus.RUNNING, pid  # Still consider it RUNNING
    else:
        return ServiceStatus.STOPPED, None
```

**Note:** Using RUNNING instead of DEGRADED to keep it simple. The key is: if process exists, it's running.

**Time:** 30 minutes

______________________________________________________________________

### Change 3: Add Service Ranking

**File:** `/home/gerald/git/mycelium/mycelium_onboarding/deployment/strategy/detector.py`

**Lines:** After line 166 (in `_detect_postgresql` method)

**Current Code:**

```python
def _detect_postgresql(self) -> Optional[DetectedService]:
    """Detect PostgreSQL service."""
    try:
        # Check if PostgreSQL is installed
        result = subprocess.run(
            ["which", "psql"],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0:
            return None

        # ... rest of detection ...
```

**New Code:**

```python
def _detect_postgresql(self) -> Optional[DetectedService]:
    """Detect PostgreSQL service with ranking."""
    # Collect all PostgreSQL instances
    all_instances = []

    # System detection
    if self.scan_system:
        system_pg = self._detect_system_postgresql()
        if system_pg:
            all_instances.append(system_pg)

    # Docker detection
    if self.scan_docker:
        docker_services = self._detect_docker_services()
        pg_containers = [
            s for s in docker_services
            if s.service_type == ServiceType.POSTGRESQL
        ]
        all_instances.extend(pg_containers)

    # No instances found?
    if not all_instances:
        return None

    # Return best instance
    return self._rank_and_select_best(all_instances)


def _detect_system_postgresql(self) -> Optional[DetectedService]:
    """Detect system PostgreSQL (extracted from _detect_postgresql)."""
    try:
        # Check if PostgreSQL is installed
        result = subprocess.run(
            ["which", "psql"],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0:
            return None

        # ... rest of original detection logic ...
        # (same as current _detect_postgresql but returns DetectedService)

    except Exception as e:
        logger.error(f"Error detecting system PostgreSQL: {e}")
        return None


def _rank_and_select_best(
    self,
    services: List[DetectedService]
) -> DetectedService:
    """Rank services and return best match.

    Ranking criteria:
    1. Running > Stopped (100 points)
    2. Docker > System (10 points)
    3. Project name match (5 points)

    Args:
        services: List of detected services

    Returns:
        Best matching service
    """
    def score_service(service: DetectedService) -> int:
        points = 0

        # Prefer running services
        if service.status == ServiceStatus.RUNNING:
            points += 100

        # Prefer Docker containers (more isolated)
        if service.metadata.get("detection_method") == "docker":
            points += 10

        # Prefer services with project name match
        container_name = service.metadata.get("container_name", "")
        if self.project_name and self.project_name in container_name:
            points += 5

        return points

    # Sort by score (highest first)
    ranked = sorted(services, key=score_service, reverse=True)
    best = ranked[0]

    logger.info(
        f"Selected best PostgreSQL: {best.name} "
        f"(status={best.status}, method={best.metadata.get('detection_method')}, "
        f"score={score_service(best)})"
    )

    return best
```

**Constructor Change:**

```python
def __init__(
    self,
    scan_system: bool = True,
    scan_docker: bool = True,
    project_name: Optional[str] = None  # NEW parameter
):
    """Initialize service detector.

    Args:
        scan_system: Whether to scan system services
        scan_docker: Whether to scan Docker containers
        project_name: Project name for container matching (optional)
    """
    self.scan_system = scan_system
    self.scan_docker = scan_docker
    self.project_name = project_name  # NEW
    self._detected_services: List[DetectedService] = []
    self._fingerprint_cache: Dict[str, ServiceFingerprint] = {}
```

**Time:** 1.5 hours

______________________________________________________________________

### Change 4: Simplify Planner Logic

**File:** `/home/gerald/git/mycelium/mycelium_onboarding/deployment/strategy/planner.py`

**Lines:** 179-289 (replace entire `_plan_postgres` method)

**Current Code:**

```python
def _plan_postgres(self) -> ServiceDeploymentPlan:
    """Plan PostgreSQL deployment strategy."""
    detected_pg = self._get_best_service(ServiceType.POSTGRESQL)
    config = self.config.services.postgres

    if detected_pg and detected_pg.status == ServiceStatus.RUNNING:
        # ... 100 lines of complex logic with port checking ...
```

**New Code:**

```python
def _plan_postgres(self) -> ServiceDeploymentPlan:
    """Plan PostgreSQL deployment strategy.

    Simple logic:
    1. No service or not running? CREATE
    2. Running + compatible? REUSE
    3. Running + incompatible? ALONGSIDE
    """
    detected_pg = self._get_best_service(ServiceType.POSTGRESQL)
    config = self.config.services.postgres

    # No service detected or not running? CREATE new
    if not detected_pg or detected_pg.status != ServiceStatus.RUNNING:
        return self._create_postgres_plan(config)

    # Service is running - check version compatibility
    compatibility = self._check_compatibility(
        ServiceType.POSTGRESQL,
        detected_pg.version
    )

    if self.prefer_reuse and compatibility == CompatibilityLevel.COMPATIBLE:
        # REUSE existing service
        return ServiceDeploymentPlan(
            service_name="postgres",
            strategy=ServiceStrategy.REUSE,
            host=detected_pg.host,
            port=detected_pg.port,
            version=detected_pg.version,
            connection_string=self._build_postgres_connection(
                detected_pg.host,
                detected_pg.port,
                config.database
            ),
            reason=self._build_reuse_reason(detected_pg),
            detected_service_id=(
                detected_pg.fingerprint.fingerprint_hash
                if detected_pg.fingerprint
                else None
            ),
            compatibility_level=compatibility,
            requires_configuration=True,
            metadata={
                "requires_database_creation": True,
                "detection_method": detected_pg.metadata.get("detection_method"),
                "container_name": detected_pg.metadata.get("container_name"),
            }
        )
    else:
        # ALONGSIDE for version incompatibility
        new_port = self._calculate_alongside_port(
            ServiceType.POSTGRESQL,
            detected_pg.port
        )
        return ServiceDeploymentPlan(
            service_name="postgres",
            strategy=ServiceStrategy.ALONGSIDE,
            host="localhost",
            port=new_port,
            version=config.version or "15",
            connection_string=self._build_postgres_connection(
                "localhost", new_port, config.database
            ),
            reason=(
                f"Existing PostgreSQL {detected_pg.version} incompatible "
                f"with required version, running alongside on port {new_port}"
            ),
            container_name=f"{self.config.project_name}-postgres",
            compatibility_level=compatibility,
            metadata={
                "existing_service_port": detected_pg.port,
                "existing_service_version": detected_pg.version,
            }
        )


def _create_postgres_plan(self, config) -> ServiceDeploymentPlan:
    """Create plan for new PostgreSQL deployment."""
    return ServiceDeploymentPlan(
        service_name="postgres",
        strategy=ServiceStrategy.CREATE,
        host="localhost",
        port=config.port,
        version=config.version or "15",
        connection_string=self._build_postgres_connection(
            "localhost", config.port, config.database
        ),
        reason="No compatible PostgreSQL instance detected, creating new service",
        container_name=f"{self.config.project_name}-postgres",
    )


def _build_reuse_reason(self, service: DetectedService) -> str:
    """Build human-readable reason for REUSE strategy."""
    method = service.metadata.get("detection_method", "system")
    location = f"{service.host}:{service.port}"

    if method == "docker":
        container = service.metadata.get("container_name", "Docker container")
        return (
            f"Compatible PostgreSQL {service.version} running "
            f"in Docker container '{container}' on {location}"
        )
    else:
        return (
            f"Compatible PostgreSQL {service.version} already running "
            f"on {location}"
        )
```

**Remove:**

- Lines 233-258 (port checking logic - no longer needed)
- Lines 341-366 (`_is_port_in_use` method - no longer needed)

**Time:** 1 hour

______________________________________________________________________

### Change 5: Update Instantiation

**File:** `/home/gerald/git/mycelium/mycelium_onboarding/deployment/commands/deploy.py`

**Find where ServiceDetector is instantiated and add project_name:**

```python
# Before:
detector = ServiceDetector(
    scan_system=True,
    scan_docker=True
)

# After:
detector = ServiceDetector(
    scan_system=True,
    scan_docker=True,
    project_name=config.project_name  # NEW
)
```

**Time:** 15 minutes

______________________________________________________________________

### Testing (P0)

**Manual Test:**

```bash
# 1. Ensure Docker container is running
docker ps | grep postgres
# Should show: mycelium-postgres

# 2. Run detection
mycelium deploy plan

# 3. Verify output
# Should say: "postgres: REUSE - Compatible PostgreSQL running in Docker container 'mycelium-postgres'"
# Should NOT say: "ALONGSIDE"
```

**Time:** 30 minutes

______________________________________________________________________

## Phase 2: Reliability Improvements (P1) - 3 hours

### Change 6: Add Timeouts to All Subprocess Calls

**File:** `/home/gerald/git/mycelium/mycelium_onboarding/deployment/strategy/detector.py`

**Find all `subprocess.run()` calls and add `timeout=5`:**

```python
# Before:
result = subprocess.run(
    ["docker", "ps", "--format", "json"],
    capture_output=True,
    text=True,
    check=False
)

# After:
result = subprocess.run(
    ["docker", "ps", "--format", "json"],
    capture_output=True,
    text=True,
    check=False,
    timeout=5  # NEW
)
```

**Count:** ~15 subprocess calls in detector.py

**Time:** 30 minutes

______________________________________________________________________

### Change 7: Add Comprehensive Logging

**File:** `/home/gerald/git/mycelium/mycelium_onboarding/deployment/strategy/detector.py`

**Add debug logging throughout detection:**

```python
def _detect_docker_postgresql(self) -> List[DetectedService]:
    """Detect PostgreSQL in Docker containers."""
    logger.debug("Starting Docker PostgreSQL detection")

    services = []

    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "json"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5
        )

        if result.returncode != 0:
            logger.debug(f"Docker ps failed: {result.stderr}")
            return services

        logger.debug(f"Found {len(result.stdout.splitlines())} containers")

        for line in result.stdout.strip().split("\n"):
            # ... parsing logic ...
            if is_postgres:
                logger.info(
                    f"Detected PostgreSQL in Docker: {container_name} "
                    f"(image={image}, port={port})"
                )
                services.append(service)

        logger.debug(f"Detected {len(services)} PostgreSQL Docker containers")
        return services

    except subprocess.TimeoutExpired:
        logger.warning("Docker detection timed out after 5 seconds")
        return services
    except Exception as e:
        logger.error(f"Error detecting Docker PostgreSQL: {e}", exc_info=True)
        return services
```

**Time:** 1 hour

______________________________________________________________________

### Change 8: Handle Permission Errors

**File:** `/home/gerald/git/mycelium/mycelium_onboarding/deployment/strategy/detector.py`

**Wrap Docker detection in permission check:**

```python
def _detect_docker_services(self) -> List[DetectedService]:
    """Detect services running in Docker containers."""
    services = []

    try:
        # Check if Docker is available and accessible
        result = subprocess.run(
            ["docker", "ps", "--format", "json"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5
        )

        if result.returncode != 0:
            if "permission denied" in result.stderr.lower():
                logger.warning(
                    "Docker detection skipped: permission denied. "
                    "Add user to 'docker' group or run with appropriate permissions."
                )
            else:
                logger.debug(f"Docker detection failed: {result.stderr}")
            return services

        # ... rest of detection ...

    except FileNotFoundError:
        logger.debug("Docker not installed, skipping Docker detection")
        return services
    except Exception as e:
        logger.error(f"Error detecting Docker services: {e}")
        return services
```

**Time:** 30 minutes

______________________________________________________________________

### Change 9: Support Multiple PostgreSQL Instances

**File:** `/home/gerald/git/mycelium/mycelium_onboarding/deployment/strategy/detector.py`

**Already supported by our new design!** The `_detect_postgresql()` method now:

1. Collects ALL instances (system + Docker)
1. Ranks them
1. Returns the best one

**To expose all instances:**

```python
def detect_all_postgresql_instances(self) -> List[DetectedService]:
    """Detect all PostgreSQL instances (not just the best one).

    Useful for diagnostic purposes or advanced use cases.

    Returns:
        List of all detected PostgreSQL instances
    """
    all_instances = []

    if self.scan_system:
        system_pg = self._detect_system_postgresql()
        if system_pg:
            all_instances.append(system_pg)

    if self.scan_docker:
        docker_services = self._detect_docker_services()
        pg_containers = [
            s for s in docker_services
            if s.service_type == ServiceType.POSTGRESQL
        ]
        all_instances.extend(pg_containers)

    return all_instances
```

**Time:** 30 minutes

______________________________________________________________________

### Testing (P1)

**Test Timeout Handling:**

```python
# Mock slow subprocess
with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("docker", 5)):
    detector = ServiceDetector()
    services = detector._detect_docker_services()
    assert services == []  # Should return empty list, not crash
```

**Test Permission Errors:**

```python
# Mock permission denied
with patch("subprocess.run") as mock_run:
    mock_run.return_value = Mock(
        returncode=1,
        stderr="permission denied while trying to connect to the Docker daemon"
    )
    detector = ServiceDetector()
    services = detector._detect_docker_services()
    assert services == []  # Should handle gracefully
```

**Time:** 30 minutes

______________________________________________________________________

## Phase 3: Polish (P2) - 8 hours

Deferred for future work. See EDGE_CASE_ANALYSIS.md for details.

______________________________________________________________________

## Testing Checklist

### Pre-Implementation

- [ ] Read EDGE_CASE_ANALYSIS.md completely
- [ ] Review current code and understand flow
- [ ] Set up test environment with Docker container running

### During Implementation

- [ ] Change 1: Docker name matching
  - [ ] Code change made
  - [ ] Manual test passed
  - [ ] Unit test added
- [ ] Change 2: Status determination
  - [ ] Helper method added
  - [ ] Manual test passed
  - [ ] Unit test for RUNNING status
  - [ ] Unit test for process-only case
- [ ] Change 3: Service ranking
  - [ ] Refactored \_detect_postgresql
  - [ ] Added \_rank_and_select_best
  - [ ] Unit test for ranking
- [ ] Change 4: Planner simplification
  - [ ] Replaced \_plan_postgres
  - [ ] Removed port checking logic
  - [ ] Added helper methods
  - [ ] Manual test passed
- [ ] Change 5: Updated instantiation
  - [ ] Added project_name parameter
  - [ ] Tested end-to-end

### Post-Implementation

- [ ] All unit tests pass
- [ ] Integration test with real Docker container
- [ ] No regression in Redis detection
- [ ] Documentation updated
- [ ] Performance verified (\< 2 seconds)

______________________________________________________________________

## Rollback Plan

If issues arise, rollback is straightforward:

**Git Revert:**

```bash
# Revert the commit
git revert HEAD

# Or reset to previous commit
git reset --hard <previous-commit-hash>
```

**Feature Flag (Alternative):**

```python
# Add flag to disable new detection
USE_IMPROVED_DETECTION = os.getenv("MYCELIUM_USE_IMPROVED_DETECTION", "true").lower() == "true"

if USE_IMPROVED_DETECTION:
    # New logic
else:
    # Old logic
```

______________________________________________________________________

## Risk Assessment

### Low Risk Changes

- Docker name matching (3 lines) - **LOW**
- Adding timeouts - **LOW**
- Logging improvements - **LOW**

### Medium Risk Changes

- Status determination refactor - **MEDIUM**
  - Risk: Might misclassify stopped services as running
  - Mitigation: Comprehensive unit tests
- Service ranking - **MEDIUM**
  - Risk: Might select wrong service in edge cases
  - Mitigation: Clear scoring algorithm, logging

### High Risk Changes

- Planner simplification - **MEDIUM-HIGH**
  - Risk: Removing port checking might cause issues
  - Mitigation: Detector now handles port ownership

**Overall Risk: LOW-MEDIUM** (well-tested changes, clear requirements)

______________________________________________________________________

## Success Criteria

### Functional

1. Docker container `mycelium-postgres` is detected
1. Status is RUNNING (not STOPPED)
1. Strategy is REUSE (not ALONGSIDE)
1. Connection string points to correct port (5432)

### Non-Functional

1. Detection completes in \< 2 seconds
1. No crashes or exceptions
1. Clear logging of detection process
1. Graceful handling of errors

### User Experience

1. Clear output showing Docker container reuse
1. No confusing ALONGSIDE when not needed
1. Helpful messages about what was detected

______________________________________________________________________

## Deployment Plan

### Step 1: Implement Changes

```bash
# 1. Create feature branch
git checkout -b fix/docker-detection

# 2. Implement P0 changes (4 hours)
# Make changes 1-5 as documented above

# 3. Run tests
pytest tests/deployment/strategy/

# 4. Manual test
mycelium deploy plan
```

### Step 2: Code Review

```bash
# Create PR
gh pr create \
  --title "fix: improve Docker PostgreSQL detection" \
  --body "Fixes detection of Docker containers by checking container name in addition to image name"
```

### Step 3: Merge and Deploy

```bash
# After approval
git checkout feat/smart-onboarding-phase1
git merge fix/docker-detection

# Test again
mycelium deploy plan

# Push
git push origin feat/smart-onboarding-phase1
```

______________________________________________________________________

## Timeline

| Phase             | Duration    | Deliverable                                      |
| ----------------- | ----------- | ------------------------------------------------ |
| P0: Critical Fix  | 4 hours     | Docker detection working, REUSE strategy correct |
| P1: Reliability   | 3 hours     | Timeouts, logging, error handling                |
| P2: Polish        | 8 hours     | Plugin architecture, advanced features           |
| **Total (P0+P1)** | **7 hours** | **Production-ready solution**                    |

______________________________________________________________________

## Next Steps

1. **Read this document completely**
1. **Review EDGE_CASE_ANALYSIS.md for context**
1. **Set up test environment**
1. **Implement P0 changes** (start with Change 1 - 3 lines!)
1. **Test after each change**
1. **Commit frequently**
1. **Create PR when P0 complete**

______________________________________________________________________

**Document Version:** 1.0 **Created:** 2025-11-06 **Author:** Multi-Agent Coordinator **Status:** Ready for
Implementation
