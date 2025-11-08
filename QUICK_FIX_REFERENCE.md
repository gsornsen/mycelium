# Quick Fix Reference - Smart Deployment Issues

## TL;DR - What Was Fixed

### Issue 1: Permission Denied Crashes Detection

**Problem**: `PermissionError` on `/etc/redis/redis.conf` caused entire Redis detection to fail **Fix**: Config paths
are now optional metadata, permission errors logged at DEBUG level **Files**: `deployment/strategy/detector.py` lines
343-416

### Issue 2 & 3: Smart Reuse Doesn't Work + Port Conflicts

**Problem**: ServiceDeploymentPlanner existed but was never used, causing all services to deploy on default ports
**Fix**: Wired up planner in deployment flow, smart plan now propagates to docker-compose generation **Files**:
`deployment/commands/deploy.py` lines 51-52, 137, 592-606, 734-738

______________________________________________________________________

## Quick Validation

### Test if Fixes Work

```bash
# 1. Start Redis
redis-server --daemonize yes
redis-cli ping  # Should return PONG

# 2. Run deployment
cd /home/gerald/git/mycelium
mycelium deploy start --dry-run

# 3. Expected output should show:
# ✅ Smart Deployment Strategy:
#    • redis: REUSE - Compatible Redis X.X already running on localhost:6379
#
# ✅ Reusable Services: redis
# ✅ New Services: None (or just postgres)

# 4. Check generated docker-compose.yml
cat ~/.local/share/mycelium/deployments/[project-name]/docker-compose.yml
# ✅ Should NOT include redis service
# ✅ Should only include services marked for CREATE
```

### Test Permission Handling

```bash
# 1. Make Redis config unreadable
sudo chmod 000 /etc/redis/redis.conf

# 2. Run detection
mycelium deploy start --dry-run --verbose

# 3. Expected behavior:
# ✅ Redis still detected (not crashing)
# ✅ Verbose logs show: "Cannot access Redis config at /etc/redis/redis.conf: Permission denied"
# ✅ metadata.config_accessible = False
# ✅ Detection continues successfully
```

______________________________________________________________________

## Key Code Changes

### detector.py - Defensive Permission Handling

```python
# OLD (BROKEN):
for path_str in config_locations:
    path = Path(path_str)
    if path.exists():
        config_path = path  # Could raise PermissionError
        break

# NEW (FIXED):
for path_str in config_locations:
    try:
        path = Path(path_str)
        if path.exists():
            try:
                path.stat()  # Test access
                config_path = path
                break
            except PermissionError:
                logger.debug(f"Cannot access: {path}")
                continue  # Try next location
    except Exception as e:
        logger.debug(f"Error: {e}")
        continue

# Always return DetectedService even if config_path is None
```

### deploy.py - Planner Integration

```python
# OLD (BROKEN):
plan = DeploymentPlan(...)
# Manual logic:
for service in detected_services:
    if service.status == ServiceStatus.RUNNING:
        plan.reusable_services.append(service.name)
# ServiceDeploymentPlanner never used!

# NEW (FIXED):
plan = DeploymentPlan(...)
# Use smart planner:
smart_planner = ServiceDeploymentPlanner(
    config=config,
    detected_services=detected_services,
    prefer_reuse=True
)
smart_plan = smart_planner.create_deployment_plan()
plan.smart_plan = smart_plan
plan.reusable_services = smart_plan.services_to_reuse
plan.new_services = smart_plan.services_to_create

# Pass to generator:
generator = DeploymentGenerator(
    config,
    output_dir=deployment_dir,
    deployment_plan=plan.smart_plan  # ← KEY FIX
)
```

______________________________________________________________________

## Verification Commands

### Check Service Detection

```bash
# Enable verbose logging
export MYCELIUM_LOG_LEVEL=DEBUG

# Run detection
mycelium deploy start --dry-run --verbose 2>&1 | grep -A5 "Detecting services"

# Should see:
# Detected Redis: status=running, version=7.2, port=6379, config_found=true
```

### Check Smart Plan

```bash
mycelium deploy start --dry-run 2>&1 | grep -A10 "Smart Deployment Strategy"

# Should see service-by-service strategies:
# • redis: REUSE - Compatible Redis already running...
# • postgres: CREATE - No compatible PostgreSQL detected...
```

### Check Docker Compose Generation

```bash
# After dry-run, check generated file
cat ~/.local/share/mycelium/deployments/*/docker-compose.yml

# Services marked REUSE should NOT appear
# Services marked CREATE should appear with correct ports
```

______________________________________________________________________

## Rollback Instructions

If fixes cause issues:

```bash
# 1. Checkout previous version
git checkout HEAD~1 -- mycelium_onboarding/deployment/strategy/detector.py
git checkout HEAD~1 -- mycelium_onboarding/deployment/commands/deploy.py

# 2. Reinstall
pip install -e .

# 3. Test
mycelium deploy start --dry-run
```

______________________________________________________________________

## Common Issues After Fix

### Issue: "ServiceDeploymentPlanner not found"

```bash
# Solution: Reinstall package
pip install -e . --force-reinstall --no-deps
```

### Issue: "deployment_plan is None" warnings

```bash
# Check: Is ServiceDeploymentPlanner imported?
grep "ServiceDeploymentPlanner" mycelium_onboarding/deployment/commands/deploy.py

# Should see:
# from mycelium_onboarding.deployment.strategy.planner import ServiceDeploymentPlanner
```

### Issue: Still getting port conflicts

```bash
# Debug: Check what planner decided
mycelium deploy start --dry-run --verbose 2>&1 | grep "strategy"

# Should show:
# redis: REUSE - Compatible Redis already running
# NOT: redis: CREATE - No compatible Redis detected
```

______________________________________________________________________

## Files Modified

| File                              | Lines Changed | Purpose                        |
| --------------------------------- | ------------- | ------------------------------ |
| `deployment/strategy/detector.py` | 284-416       | Defensive Redis detection      |
| `deployment/strategy/detector.py` | 222-251       | Defensive PostgreSQL detection |
| `deployment/commands/deploy.py`   | 51-52         | Import planner                 |
| `deployment/commands/deploy.py`   | 137           | Add smart_plan field           |
| `deployment/commands/deploy.py`   | 592-606       | Integrate planner              |
| `deployment/commands/deploy.py`   | 734-738       | Pass plan to generator         |
| `deployment/commands/deploy.py`   | 1116-1129     | Display strategies             |

______________________________________________________________________

## Testing Checklist

Before merging:

- [ ] Run existing test suite: `pytest tests/`
- [ ] Test with Redis running: Service detected and reused
- [ ] Test with Redis stopped: Service created
- [ ] Test with restricted permissions: No crashes
- [ ] Test with custom ports: ALONGSIDE strategy works
- [ ] Verify docker-compose.yml excludes reused services
- [ ] Verify CONNECTIONS.md shows correct strategies
- [ ] Check logs for permission errors (should be DEBUG)

______________________________________________________________________

## Need Help?

- **Full Analysis**: See `DEPLOYMENT_FIXES_5WHYS_ANALYSIS.md`
- **Test Cases**: See `DEPLOYMENT_FIXES_5WHYS_ANALYSIS.md` sections
- **Architecture**: See data flow diagrams in main analysis
- **Logs**: Check `~/.local/share/mycelium/logs/deployment.log`

______________________________________________________________________

**Last Updated**: 2025-11-06 **Status**: ✅ All Fixes Applied **Next**: Run test suite and validate
