---
allowed-tools: Bash(cat:*), Bash(redis-cli:*), Bash(pg_isready:*), Bash(nvidia-smi:*), Bash(docker:*), Bash(kubectl:*), Read
description: Generalized infrastructure health check for MCP servers, databases, and system dependencies. Configurable via .infra-check.json in project root.
argument-hint: [--verbose] [--config <path>]
---

# Infrastructure Health Check

Run comprehensive health checks on all configured infrastructure components.

## Context

**Command arguments**: $ARGS

First, check for configuration files and load the appropriate one:
- Project config: `.infra-check.json`
- User config: `~/.infra-check.json`
- If neither exists, use default checks

## Your Task

1. **Load Configuration**:
   - Check for `.infra-check.json` in current directory
   - Fallback to `~/.infra-check.json` if not found
   - Use sensible defaults if no config exists

2. **Parse Configuration Schema**:
   ```json
   {
     "checks": {
       "redis": {
         "enabled": true,
         "url": "redis://localhost:6379",
         "timeout_seconds": 5
       },
       "temporal": {
         "enabled": true,
         "host": "localhost:7233",
         "namespace": "default"
       },
       "taskqueue": {
         "enabled": true,
         "check_npm": true
       },
       "postgresql": {
         "enabled": false,
         "connection_string": "postgresql://localhost:5432/mydb"
       },
       "mongodb": {
         "enabled": false,
         "url": "mongodb://localhost:27017"
       },
       "gpu": {
         "enabled": false,
         "required_model": "RTX 4090",
         "max_temperature": 85
       },
       "custom": [
         {
           "name": "Custom Service",
           "check_command": "curl -f http://localhost:8080/health"
         }
       ]
     },
     "output": {
       "verbose": false,
       "format": "standard"
     }
   }
   ```

3. **Execute Health Checks**:

   **Redis/Valkey Check**:
   ```bash
   redis-cli -u $REDIS_URL ping
   ```

   **Temporal Check**:
   ```bash
   temporal workflow list --namespace $NAMESPACE --limit 1
   ```

   **TaskQueue Check**:
   ```bash
   npx --version && npm list taskqueue-mcp --depth=0
   ```

   **PostgreSQL Check**:
   ```bash
   psql $CONNECTION_STRING -c "SELECT 1;" || pg_isready -d $CONNECTION_STRING
   ```

   **MongoDB Check**:
   ```bash
   mongosh $MONGODB_URL --eval "db.runCommand({ ping: 1 })" --quiet
   ```

   **GPU Check**:
   ```bash
   nvidia-smi --query-gpu=name,temperature.gpu,memory.used,memory.total --format=csv,noheader
   ```

   **Custom Checks**:
   Run each custom check command and capture exit code.

4. **Output Format**:

   **Standard (non-verbose)**:
   ```
   === Infrastructure Health Check ===

   ✅ Redis               HEALTHY    (redis://localhost:6379)
   ✅ Temporal            HEALTHY    (localhost:7233)
   ✅ TaskQueue           HEALTHY    (npx available)
   ⚠️  PostgreSQL         WARNING    (slow response: 2.3s)
   ❌ MongoDB             FAILED     (connection refused)

   ===================================
   Overall Status: DEGRADED ⚠️

   Issues Detected:
   1. PostgreSQL responding slowly (2.3s > 1.0s threshold)
      └─ Action: Check database load

   2. MongoDB connection failed
      └─ Error: Connection refused at localhost:27017
      └─ Fix: Start MongoDB with 'mongod' or 'docker run -d -p 27017:27017 mongo:latest'
   ```

   **Verbose**:
   Include detailed metrics for each service (connection time, memory usage, version, uptime, etc.)

5. **Exit Codes**:
   - 0: All enabled checks passed (HEALTHY)
   - 1: One or more checks failed (UNHEALTHY or DEGRADED)

6. **Integration Notes**:
   - This command can be used in pre-test hooks
   - Can be called from CI/CD pipelines
   - Results can be published to coordination channels if MCP servers available

## Example Configuration Files

Create `.infra-check.json.example` in project root:
```json
{
  "checks": {
    "redis": {"enabled": true, "url": "redis://localhost:6379"},
    "temporal": {"enabled": true, "host": "localhost:7233"},
    "taskqueue": {"enabled": true}
  }
}
```

## Error Handling

- Gracefully handle missing dependencies (e.g., redis-cli not installed)
- Provide helpful error messages with installation instructions
- Continue checking other services even if one fails
- Aggregate all results before reporting overall status

## Coordination Integration (Optional)

If Redis MCP is available, publish health metrics:
```javascript
// Check if mcp__RedisMCPServer tools are available
// If yes, publish metrics:
await mcp__RedisMCPServer__hset({
  name: "health:components",
  key: "redis",
  value: "healthy"
});

await mcp__RedisMCPServer__hset({
  name: "health:last_check",
  key: "timestamp",
  value: new Date().toISOString()
});
```

If not available, simply output to console.
