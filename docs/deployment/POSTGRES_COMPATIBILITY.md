# PostgreSQL Version Compatibility Guide

## Overview

Mycelium automatically validates PostgreSQL compatibility with your Temporal version before deployment to prevent
runtime failures and ensure a smooth deployment experience.

## How It Works

The compatibility checking system performs four steps:

1. **Detect Temporal Version** - Automatically discovers your Temporal SDK version from:

   - `pyproject.toml` (PEP 621, Poetry, PDM)
   - `requirements.txt`
   - `poetry.lock`
   - `setup.py` / `setup.cfg`

1. **Detect PostgreSQL Version** - Identifies your PostgreSQL version from:

   - Docker containers
   - Kubernetes pods
   - Local installations
   - Remote database connections

1. **Validate Compatibility** - Checks versions against the compatibility matrix

1. **Display Warnings** - Shows clear, actionable warnings if versions are incompatible

## Supported Versions

### Temporal Versions

- **Covered:** 1.0.0 through 1.24.0+
- **Tested:** All major and minor releases
- **Unknown versions:** Conservative defaults applied with warning

### PostgreSQL Versions

- **Covered:** 12.0 through 17.0
- **Recommended:** 16.0 (latest stable)
- **EOL Warning:** PostgreSQL 12 reached end-of-life on 2024-11-14

## Compatibility Matrix

| Temporal Version | Min PostgreSQL | Max PostgreSQL | Recommended | Notes         |
| ---------------- | -------------- | -------------- | ----------- | ------------- |
| 1.24.0           | 13.0           | 17.9           | 16.0        | Latest stable |
| 1.23.0           | 13.0           | 17.9           | 16.0        | Current       |
| 1.22.0           | 13.0           | 16.9           | 15.0        | LTS candidate |
| 1.20.0           | 12.0           | 16.9           | 14.0        | Deprecated    |
| 1.15.0           | 12.0           | 15.9           | 13.0        | Deprecated    |
| 1.10.0           | 12.0           | 15.9           | 13.0        | Deprecated    |

**Full matrix:** See `mycelium_onboarding/deployment/postgres/compatibility.yaml`

## Usage

### Automatic Validation (Default)

The simplest way to deploy with compatibility checking:

```bash
mycelium deploy start
```

This will:

- Automatically detect Temporal version from your project
- Automatically detect PostgreSQL version from deployment
- Validate compatibility
- Show warnings if incompatible
- Prompt for confirmation if issues found

### Override Detected Versions

If automatic detection fails or you want to specify versions explicitly:

```bash
# Override PostgreSQL version
mycelium deploy start --postgres-version 16.0

# Override Temporal version
mycelium deploy start --temporal-version 1.24.0

# Override both
mycelium deploy start --postgres-version 16.0 --temporal-version 1.24.0
```

### Skip Validation (Not Recommended)

To bypass compatibility checking entirely:

```bash
mycelium deploy start --force-version
```

**Warning:** Only use `--force-version` in development or when you've manually verified compatibility. Not recommended
for production deployments.

## Compatibility Scenarios

### Scenario 1: Compatible Versions ✅

```
✅ PostgreSQL Compatibility Check Passed

Temporal:   1.24.0
PostgreSQL: 16.0

Status: Compatible ✓

This is a tested, recommended combination.
```

**Action:** Deployment proceeds normally.

### Scenario 2: PostgreSQL Too Old ⚠️

```
⚠️  PostgreSQL Version Incompatibility

Current Setup:
  Temporal:   1.22.0
  PostgreSQL: 12.0

Requirements:
  Minimum PostgreSQL: 13.0
  Maximum PostgreSQL: 16.9
  Recommended:        15.0

Issue: Your PostgreSQL version is too old

Recommended Actions:
  1. Upgrade PostgreSQL to 13.0+ (manual process)
  2. Downgrade Temporal to 1.20.0 or earlier
  3. Continue anyway with --force-version (not recommended)
```

**Action:** You can choose to:

1. Cancel deployment and upgrade PostgreSQL
1. Downgrade Temporal version
1. Continue anyway (expert mode)

### Scenario 3: End-of-Life Warning ⚠️

```
⚠️  PostgreSQL End of Life Warning

Your PostgreSQL version has reached End of Life:
  PostgreSQL: 12.0
  EOL Date:   November 14, 2024

Security Risk: No more security updates

Strongly Recommended:
  Upgrade to PostgreSQL 15+ (current stable)

While technically compatible with Temporal 1.20.0,
using EOL PostgreSQL in production is risky.
```

**Action:** Upgrade to supported PostgreSQL version before production deployment.

### Scenario 4: Unknown Temporal Version ⚠️

```
⚠️  Unknown Temporal Version Detected

Detected:  1.99.0 (unknown version)
Using:     Conservative defaults

PostgreSQL Requirements (estimated):
  Minimum: 12.0
  Maximum: 17.9

Recommendation:
  Verify compatibility manually at:
  https://docs.temporal.io/self-hosted-guide/setup
```

**Action:** Verify compatibility manually or update compatibility matrix.

## Troubleshooting

### Cannot Detect Temporal Version

**Error Message:**

```
✗ Cannot detect Temporal version from project

Please ensure your project has Temporal dependency in:
  - pyproject.toml
  - requirements.txt
  - Or specify manually: --temporal-version 1.24.0
```

**Solutions:**

1. Add `temporalio` to your project dependencies
1. Use `--temporal-version` flag to specify manually
1. Ensure dependency files are in the correct format

### Cannot Detect PostgreSQL Version

**Error Message:**

```
✗ Cannot detect PostgreSQL version

Please specify manually: --postgres-version 15.0
```

**Solutions:**

1. Ensure PostgreSQL is running and accessible
1. Check Docker container or Kubernetes pod status
1. Use `--postgres-version` flag to specify manually

### Validation Fails with --force-version

**Issue:** Even with `--force-version`, deployment seems to check compatibility

**Cause:** `--force-version` only skips the validation check, not the deployment prerequisites

**Solution:** Ensure PostgreSQL is actually running and accessible

## Manual PostgreSQL Upgrade

**IMPORTANT:** Mycelium NEVER automatically upgrades PostgreSQL. All upgrades must be performed manually.

### Upgrade Process

#### 1. Backup Your Database

```bash
# Full database backup
pg_dump -h localhost -U postgres mydb > backup.sql

# Or backup all databases
pg_dumpall -h localhost -U postgres > backup_all.sql
```

#### 2. Install New PostgreSQL Version

**Ubuntu/Debian:**

```bash
# Add PostgreSQL repository
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt-get update

# Install PostgreSQL 16
sudo apt-get install postgresql-16
```

**macOS:**

```bash
# Using Homebrew
brew install postgresql@16

# Start the service
brew services start postgresql@16
```

**Docker:**

```bash
# Pull new image
docker pull postgres:16

# Update docker-compose.yml
services:
  postgres:
    image: postgres:16
```

#### 3. Migrate Data

**Option A: pg_upgrade (Faster)**

```bash
sudo -u postgres pg_upgrade \
  --old-datadir=/var/lib/postgresql/12/main \
  --new-datadir=/var/lib/postgresql/16/main \
  --old-bindir=/usr/lib/postgresql/12/bin \
  --new-bindir=/usr/lib/postgresql/16/bin
```

**Option B: Dump and Restore (Safer)**

```bash
# Restore from backup
psql -h localhost -U postgres -d mydb < backup.sql
```

#### 4. Test Thoroughly

```bash
# Connect to new version
psql -h localhost -U postgres

# Check version
SELECT version();

# Run application tests
pytest tests/

# Test Temporal workflows
mycelium deploy start --dry-run
```

#### 5. Deploy Temporal

```bash
# Deploy with validation
mycelium deploy start
```

### Rollback Plan

If upgrade fails:

1. **Stop new PostgreSQL:**

   ```bash
   sudo systemctl stop postgresql@16
   ```

1. **Restart old version:**

   ```bash
   sudo systemctl start postgresql@12
   ```

1. **Restore from backup if needed:**

   ```bash
   psql -h localhost -U postgres -d mydb < backup.sql
   ```

## Safety

### Never Auto-Upgrade

Mycelium is designed with safety as a priority:

- ✅ Validates compatibility before deployment
- ✅ Shows clear warnings with manual instructions
- ✅ Provides `--force-version` for expert override
- ❌ **NEVER** automatically upgrades PostgreSQL
- ❌ **NEVER** modifies your database
- ❌ **NEVER** runs migrations without confirmation

All PostgreSQL upgrades must be performed manually following official PostgreSQL documentation.

### Production Best Practices

1. **Always test in staging first**

   - Validate compatibility in non-production environment
   - Run full test suite after PostgreSQL upgrade
   - Monitor for issues before promoting to production

1. **Plan maintenance windows**

   - Schedule PostgreSQL upgrades during low-traffic periods
   - Allow sufficient time for testing and rollback
   - Communicate downtime to stakeholders

1. **Monitor after deployment**

   - Watch for PostgreSQL errors in logs
   - Monitor Temporal workflow execution
   - Have rollback plan ready

1. **Keep versions up-to-date**

   - Regularly update to supported PostgreSQL versions
   - Don't wait until EOL to upgrade
   - Follow Temporal release notes for breaking changes

## FAQ

### Q: Can I skip version checking?

**A:** Yes, use `--force-version`, but this is not recommended for production deployments. Only use when you've manually
verified compatibility.

### Q: What if my Temporal version is not in the matrix?

**A:** Conservative defaults will be used with a warning. Verify compatibility manually at
[Temporal Documentation](https://docs.temporal.io/self-hosted-guide/setup).

### Q: How do I update the compatibility matrix?

**A:** Edit `mycelium_onboarding/deployment/postgres/compatibility.yaml` and add your version. Submit a PR to share with
the community.

### Q: Does this work with Temporal Cloud?

**A:** No, this feature is for self-hosted Temporal deployments only. Temporal Cloud manages PostgreSQL versions
automatically.

### Q: Can I use a different database?

**A:** Temporal supports PostgreSQL, MySQL, and Cassandra. This compatibility checker is PostgreSQL-specific. Other
databases are not validated.

### Q: What about minor version updates (16.0 → 16.1)?

**A:** Minor version updates within the same major version (e.g., 16.x) are generally safe and don't require
revalidation. The compatibility matrix uses major.minor format (16.0).

### Q: How often is the compatibility matrix updated?

**A:** The matrix is updated with each Mycelium release and when new Temporal versions are released. Check the
`metadata.last_updated` field in `compatibility.yaml`.

### Q: What if I'm using a PostgreSQL fork (like Amazon RDS)?

**A:** The version checking works with PostgreSQL-compatible databases. Use the equivalent PostgreSQL version number
(e.g., RDS PostgreSQL 16 = PostgreSQL 16.0).

## Additional Resources

- [Temporal Self-Hosted Setup Guide](https://docs.temporal.io/self-hosted-guide/setup)
- [PostgreSQL Upgrade Guide](https://www.postgresql.org/docs/current/upgrading.html)
- [PostgreSQL Version Policy](https://www.postgresql.org/support/versioning/)
- [Mycelium Deployment Documentation](../README.md)

## Support

For issues or questions:

1. Check this documentation
1. Review the [troubleshooting section](#troubleshooting)
1. Check [compatibility matrix](#compatibility-matrix)
1. Open an issue on GitHub with:
   - Temporal version
   - PostgreSQL version
   - Error message
   - Deployment method (Docker, Kubernetes, etc.)
