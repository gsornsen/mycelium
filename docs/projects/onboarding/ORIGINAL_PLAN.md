# Mycelium Onboarding & Configuration System

## Comprehensive Implementation Plan

______________________________________________________________________

## 🎯 Executive Summary

Transform Mycelium from passive infrastructure into an interactive, self-configuring system that guides users through
setup, manages isolated environments, and validates coordination through agent-based testing.

### Key Deliverables

1. **Interactive Onboarding System** - TUI-based configuration wizard
1. **Infrastructure Management** - Docker Compose OR Justfile-based orchestration
1. **Isolated Environments** - Language-specific isolation (Python via uv, Node.js, etc.)
1. **Agent Testing Framework** - Orchestrator-driven coordination validation
1. **Configuration Management** - View, edit, and reconfigure at any time

______________________________________________________________________

## 📋 Part 1: Interactive Configuration System

### `/mycelium-onboarding` Command

**Purpose**: First-time setup wizard that detects, configures, and deploys infrastructure

**Flow**:

```
1. Welcome & System Detection
   ├─ Detect available services (Redis, Postgres, Temporal, Docker, GPUs)
   ├─ Show detected vs. required services
   └─ Recommend configuration based on detection

2. Service Selection (TUI or Q&A)
   ├─ [✓] Redis (detected: running on :6379)
   ├─ [✓] Temporal (detected: CLI installed, server needed)
   ├─ [ ] PostgreSQL (not detected - install?)
   ├─ [ ] MongoDB (not detected - skip?)
   ├─ [✓] GPU: NVIDIA RTX 4090 (detected)
   └─ Custom services...

3. Deployment Method Selection
   ├─ Option A: Docker Compose (recommended)
   │  ├─ All services in containers
   │  ├─ Easy teardown/rebuild
   │  └─ Consistent across environments
   │
   └─ Option B: Baremetal via Justfile
      ├─ Services run as system processes
      ├─ Better performance
      ├─ More complex dependency management
      └─ Options: Justfile (parallel), Procfile, or supervisord

4. Environment Isolation Configuration
   ├─ Python: uv virtual environment
   │  └─ Enforce "uv run python" pattern
   ├─ Node.js: npm/pnpm project-local
   │  └─ Use npx for global tools
   ├─ Ruby: bundler exec
   └─ Go: module-scoped builds

5. Generate Configuration
   ├─ Write ~/.config/mycelium/config.json
   ├─ Generate docker-compose.yaml OR Justfile
   ├─ Create .envrc for environment isolation
   └─ Set up coordination directories

6. Deploy & Validate
   ├─ Start services
   ├─ Run /infra-check
   ├─ Initialize coordination (Redis keys, TaskQueue projects)
   └─ Success report with next steps
```

**Technical Approach**:

**Option 1: TUI with Python `textual`**

```python
# ~/.claude/plugins/mycelium-core/lib/onboarding/tui.py
from textual.app import App
from textual.widgets import Checkbox, Button, SelectionList

class MyceliumOnboarding(App):
    def compose(self):
        yield Header()
        yield ServiceSelector(detected_services)
        yield DeploymentMethodSelector()
        yield EnvironmentIsolationSelector()
        yield ProgressView()
        yield Footer()
```

**Option 2: CLI Q&A with `click`**

```python
# ~/.claude/plugins/mycelium-core/lib/onboarding/cli.py
import click
from InquirerPy import inquirer

@click.command()
def onboard():
    services = detect_services()
    selected = inquirer.checkbox(
        message="Select services to enable:",
        choices=[...detected_services]
    ).execute()

    deployment = inquirer.select(
        message="Choose deployment method:",
        choices=["Docker Compose", "Baremetal (Justfile)", "Baremetal (Procfile)"]
    ).execute()

    # Continue configuration...
```

**Detection Scripts**:

```python
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
```

______________________________________________________________________

## 📋 Part 2: Configuration Storage & Management

### Configuration Schema

**Location**: `~/.config/mycelium/config.json`

```json
{
  "version": "1.0.0",
  "onboarding_completed": true,
  "onboarding_date": "2025-10-13T11:30:00Z",

  "deployment": {
    "method": "docker-compose",
    "compose_file": "~/.config/mycelium/docker-compose.yaml",
    "justfile": null
  },

  "services": {
    "redis": {
      "enabled": true,
      "mode": "docker",
      "port": 6379,
      "password": null,
      "persistence": true
    },
    "temporal": {
      "enabled": true,
      "mode": "docker",
      "ui_port": 8233,
      "grpc_port": 7233,
      "namespace": "default"
    },
    "postgresql": {
      "enabled": true,
      "mode": "docker",
      "port": 5432,
      "database": "mycelium",
      "username": "mycelium",
      "password_env": "MYCELIUM_POSTGRES_PASSWORD"
    },
    "mongodb": {
      "enabled": false
    },
    "gpu": {
      "enabled": true,
      "devices": [
        {
          "id": 0,
          "model": "NVIDIA RTX 4090",
          "memory_gb": 24
        }
      ],
      "docker_runtime": "nvidia"
    }
  },

  "environments": {
    "python": {
      "manager": "uv",
      "venv_path": "~/.config/mycelium/venvs/mycelium",
      "enforce_isolation": true,
      "blocked_commands": ["python", "python3", "pip", "pip3"]
    },
    "node": {
      "manager": "npm",
      "project_local": true,
      "use_npx": true
    },
    "ruby": {
      "manager": "bundler",
      "use_bundle_exec": true
    }
  },

  "coordination": {
    "primary_method": "redis",
    "redis_keys": {
      "agents_workload": "agents:workload",
      "agents_tasks": "agents:active_tasks",
      "agents_heartbeat": "agents:heartbeat",
      "circuit_breaker": "agents:circuit-breaker"
    },
    "taskqueue_project": "mycelium-coordination",
    "markdown_fallback": true,
    "markdown_dir": ".claude/coordination"
  },

  "testing": {
    "enabled": true,
    "orchestrator_agent": "multi-agent-coordinator",
    "test_agents": [
      "task-distributor",
      "knowledge-synthesizer",
      "performance-monitor"
    ]
  }
}
```

### `/mycelium-configuration` Command

**Purpose**: View current configuration and modify settings

**Features**:

- Show current configuration (formatted, colored output)
- Edit specific services (enable/disable, change ports)
- Switch deployment methods
- Re-run onboarding from scratch
- Export/import configurations

**Flow**:

```
$ /mycelium-configuration

=== Mycelium Configuration ===

Services:
  ✅ Redis (docker, :6379)
  ✅ Temporal (docker, :7233)
  ✅ PostgreSQL (docker, :5432)
  ❌ MongoDB (disabled)
  ✅ GPU: NVIDIA RTX 4090

Deployment: Docker Compose
Environment Isolation: uv (Python), npm (Node.js)
Coordination: Redis MCP (primary)

Actions:
  [v] View full configuration
  [e] Edit service
  [d] Change deployment method
  [r] Re-run onboarding
  [t] Test infrastructure
  [x] Exit
```

______________________________________________________________________

## 📋 Part 3: Deployment Methods

### Option A: Docker Compose

**Generated File**: `~/.config/mycelium/docker-compose.yaml`

```yaml
version: '3.9'

services:
  redis:
    image: redis:7-alpine
    container_name: mycelium-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  temporal:
    image: temporalio/auto-setup:latest
    container_name: mycelium-temporal
    ports:
      - "7233:7233"
      - "8233:8233"
    environment:
      - DB=postgresql
      - DB_PORT=5432
      - POSTGRES_USER=temporal
      - POSTGRES_PWD=temporal
      - POSTGRES_SEEDS=postgres
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    container_name: mycelium-postgres
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=mycelium
      - POSTGRES_PASSWORD=${MYCELIUM_POSTGRES_PASSWORD:-mycelium}
      - POSTGRES_DB=mycelium
    volumes:
      - postgres-data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mycelium"]
      interval: 5s
      timeout: 3s
      retries: 5

  # GPU-accelerated services can be added here with:
  # deploy:
  #   resources:
  #     reservations:
  #       devices:
  #         - driver: nvidia
  #           count: 1
  #           capabilities: [gpu]

volumes:
  redis-data:
  postgres-data:

networks:
  default:
    name: mycelium-network
```

**Management Commands**:

```bash
# Start all services
docker compose -f ~/.config/mycelium/docker-compose.yaml up -d

# Stop all services
docker compose -f ~/.config/mycelium/docker-compose.yaml down

# View logs
docker compose -f ~/.config/mycelium/docker-compose.yaml logs -f

# Restart single service
docker compose -f ~/.config/mycelium/docker-compose.yaml restart redis
```

### Option B: Baremetal with Justfile

**Generated File**: `~/.config/mycelium/Justfile`

```makefile
# Mycelium Infrastructure Management
# Generated: 2025-10-13

# Start all services in parallel
[group('lifecycle')]
[parallel]
start: start-redis start-temporal start-postgres

# Stop all services
[group('lifecycle')]
[parallel]
stop: stop-redis stop-temporal stop-postgres

# Individual service management

[group('redis')]
start-redis:
    @echo "Starting Redis..."
    redis-server --daemonize yes --port 6379 --logfile ~/.config/mycelium/logs/redis.log

[group('redis')]
stop-redis:
    @echo "Stopping Redis..."
    redis-cli shutdown

[group('temporal')]
start-temporal: start-postgres
    @echo "Starting Temporal server..."
    temporal server start-dev --db-filename ~/.config/mycelium/data/temporal.db --log-level info &
    @echo $! > ~/.config/mycelium/pids/temporal.pid

[group('temporal')]
stop-temporal:
    @echo "Stopping Temporal..."
    kill $(cat ~/.config/mycelium/pids/temporal.pid) 2>/dev/null || true

[group('postgres')]
start-postgres:
    @echo "Starting PostgreSQL..."
    pg_ctl -D ~/.config/mycelium/data/postgres -l ~/.config/mycelium/logs/postgres.log start

[group('postgres')]
stop-postgres:
    @echo "Stopping PostgreSQL..."
    pg_ctl -D ~/.config/mycelium/data/postgres stop

# Health checks
[group('health')]
check-redis:
    redis-cli ping

[group('health')]
check-postgres:
    pg_isready

[group('health')]
check-temporal:
    temporal workflow list --limit 1

[group('health')]
[parallel]
health: check-redis check-postgres check-temporal

# Logs
[group('logs')]
logs-redis:
    tail -f ~/.config/mycelium/logs/redis.log

[group('logs')]
logs-postgres:
    tail -f ~/.config/mycelium/logs/postgres.log

[group('logs')]
logs-temporal:
    tail -f ~/.config/mycelium/logs/temporal.log
```

**Alternatives Considered**:

1. **Procfile** (requires foreman/hivemind):

```procfile
redis: redis-server --port 6379
temporal: temporal server start-dev
postgres: pg_ctl -D ~/.config/mycelium/data/postgres start
```

2. **Supervisord** (better for production):

```ini
[supervisord]
logfile=~/.config/mycelium/logs/supervisord.log

[program:redis]
command=redis-server --port 6379
autostart=true
autorestart=true

[program:temporal]
command=temporal server start-dev
autostart=true
autorestart=true
depends_on=postgres

[program:postgres]
command=pg_ctl -D ~/.config/mycelium/data/postgres start
autostart=true
autorestart=true
```

**Recommendation**: Use Justfile for simplicity and built-in parallel support.

______________________________________________________________________

## 📋 Part 4: Environment Isolation

### Python Isolation via `uv`

**Setup**:

```bash
# Create isolated venv for Mycelium
uv venv ~/.config/mycelium/venvs/mycelium

# Install dependencies
uv pip install -r ~/.config/mycelium/requirements.txt
```

**Enforcement**:

1. **Wrapper Script**: `~/.config/mycelium/bin/python`

```bash
#!/bin/bash
# Mycelium Python wrapper - enforces uv isolation

if [[ "$0" == *"/python"* ]] || [[ "$0" == *"/python3"* ]]; then
    echo "❌ Direct python execution blocked by Mycelium"
    echo "Use: uv run python <script>"
    exit 1
fi

exec uv run python "$@"
```

2. **Shell Hook**: Add to `.envrc` (direnv) or `.bashrc`

```bash
# Mycelium environment isolation
export PATH="~/.config/mycelium/bin:$PATH"
alias python='echo "Use: uv run python" && false'
alias python3='echo "Use: uv run python" && false'
alias pip='echo "Use: uv pip" && false'
alias pip3='echo "Use: uv pip" && false'
```

3. **Command Validation in Slash Commands**:

```python
# In command execution context
def validate_python_command(cmd: str) -> bool:
    """Ensure python commands use uv"""
    blocked_patterns = [
        r'\bpython\s',
        r'\bpython3\s',
        r'\bpip\s',
        r'\bpip3\s',
    ]

    for pattern in blocked_patterns:
        if re.search(pattern, cmd):
            raise ValueError(
                f"Direct python execution blocked. Use: uv run python ..."
            )

    return True
```

### Node.js Isolation

**Enforcement**:

```bash
# Use npx for global tools
alias node-global='echo "Use: npx <tool>" && false'

# Project-local node_modules
export PATH="./node_modules/.bin:$PATH"
```

### Ruby Isolation

**Enforcement**:

```bash
# Require bundle exec
alias gem='echo "Use: bundle install" && false'
alias ruby='echo "Use: bundle exec ruby" && false'
```

______________________________________________________________________

## 📋 Part 5: Agent Testing Framework

### `/mycelium-test` Command

**Purpose**: Validate agent coordination through orchestrated tasks

**Flow**:

```
1. Orchestrator Setup
   ├─ multi-agent-coordinator initializes test
   ├─ Creates test project in TaskQueue
   └─ Publishes initial state to Redis

2. Task Generation (Mycelium-themed)
   ├─ "Spread spores to 5 new locations" (task-distributor)
   ├─ "Establish hyphal network connection" (context-manager)
   ├─ "Synthesize nutrient report" (knowledge-synthesizer)
   ├─ "Monitor mycelial growth rate" (performance-monitor)
   └─ "Detect fungal anomalies" (error-coordinator)

3. Task Distribution
   ├─ multi-agent-coordinator assigns tasks
   ├─ Agents pick up tasks via TaskQueue
   ├─ Agents report status to Redis
   └─ Agents publish messages via pub/sub

4. Coordination Validation
   ├─ Monitor Redis keys for updates
   ├─ Check TaskQueue task progression
   ├─ Verify pub/sub message flow
   └─ Track agent heartbeats

5. Results & Report
   ├─ Success: All agents responded
   ├─ Latency: Task pickup time
   ├─ Coordination: Message flow analysis
   └─ Health: Circuit breaker status

6. Cleanup
   ├─ Archive test project
   ├─ Clear test Redis keys
   └─ Generate test report
```

**Implementation**:

**Test Orchestrator**:

```python
# ~/.claude/plugins/mycelium-core/lib/testing/orchestrator.py

class MyceliumTest:
    def __init__(self, redis_client, taskqueue_client):
        self.redis = redis_client
        self.taskqueue = taskqueue_client
        self.test_id = str(uuid.uuid4())

    async def run_test(self):
        """Execute full coordination test"""
        print("🍄 Initializing Mycelium coordination test...")

        # 1. Create test project
        project = await self.create_test_project()

        # 2. Generate quirky tasks
        tasks = self.generate_spore_tasks()

        # 3. Publish tasks to TaskQueue
        for task in tasks:
            await self.taskqueue.create_task(
                project_id=project.id,
                **task
            )

        # 4. Monitor coordination
        results = await self.monitor_execution(
            duration_seconds=60
        )

        # 5. Generate report
        report = self.generate_report(results)

        print(report)
        return report

    def generate_spore_tasks(self):
        """Generate mycelium-themed test tasks"""
        return [
            {
                "title": "Spread spores to 5 new locations",
                "description": "Disperse fungal propagules across the network",
                "agent": "task-distributor",
                "priority": "high"
            },
            {
                "title": "Establish hyphal network connection",
                "description": "Create interconnected mycelial threads",
                "agent": "context-manager",
                "priority": "medium"
            },
            {
                "title": "Synthesize nutrient report from decomposition",
                "description": "Extract insights from organic matter breakdown",
                "agent": "knowledge-synthesizer",
                "priority": "medium"
            },
            {
                "title": "Monitor mycelial growth rate",
                "description": "Track expansion metrics across hyphae",
                "agent": "performance-monitor",
                "priority": "low"
            },
            {
                "title": "Detect and isolate fungal anomalies",
                "description": "Identify contamination or network disruptions",
                "agent": "error-coordinator",
                "priority": "high"
            }
        ]

    async def monitor_execution(self, duration_seconds):
        """Monitor Redis/TaskQueue during test"""
        start_time = time.time()
        metrics = {
            "agent_responses": [],
            "task_completions": [],
            "messages_published": 0,
            "heartbeat_count": 0
        }

        while time.time() - start_time < duration_seconds:
            # Check Redis for agent activity
            workload = await self.redis.hgetall("agents:workload")
            heartbeats = await self.redis.hgetall("agents:heartbeat")

            # Check TaskQueue for task progress
            tasks = await self.taskqueue.list_tasks(
                project_id=self.project_id
            )

            # Update metrics
            metrics["heartbeat_count"] = len(heartbeats)
            metrics["task_completions"] = sum(
                1 for t in tasks if t.status == "done"
            )

            await asyncio.sleep(5)

        return metrics
```

**Command Integration**:

````yaml
---
# ~/.claude/plugins/mycelium-core/commands/mycelium-test.md
allowed-tools:
  - mcp__RedisMCPServer__*
  - mcp__taskqueue__*
  - Bash(uv:*)
  - Read
  - Write
description: Test agent coordination system with orchestrated tasks. Validates TaskQueue, Redis pub/sub, and agent response times.
argument-hint: [--duration <seconds>] [--agents <comma-separated>] [--verbose]
---

# Mycelium Coordination Test

Validate the multi-agent coordination infrastructure through orchestrated testing.

## Your Task

1. **Initialize Test Environment**:
   - Check Redis and TaskQueue availability
   - Verify test agents are configured
   - Create isolated test project

2. **Execute Test**:
   ```bash
   uv run python ~/.config/mycelium/lib/testing/orchestrator.py \
     --duration 60 \
     --agents task-distributor,context-manager,performance-monitor
````

3. **Monitor Coordination**:

   - Track agent heartbeats in Redis
   - Monitor task progression in TaskQueue
   - Measure response latency
   - Validate pub/sub message flow

1. **Generate Report**:

   ```
   === Mycelium Coordination Test ===
   Duration: 60 seconds

   Agents Tested:
     ✅ task-distributor      (responded in 2.3s)
     ✅ context-manager       (responded in 1.8s)
     ✅ performance-monitor   (responded in 3.1s)

   Task Execution:
     Total Tasks: 5
     Completed: 5
     Failed: 0
     Success Rate: 100%

   Coordination Metrics:
     Heartbeat Frequency: 5.2s avg
     Message Latency: 0.8s avg
     Queue Depth: 0

   Redis Health:
     Keys Created: 15
     Pub/Sub Messages: 23
     Connected Clients: 3

   TaskQueue Health:
     Projects: 1 (test)
     Tasks Created: 5
     Tasks Completed: 5

   ===================================
   Overall Result: ✅ PASS

   All coordination systems operational!
   ```

1. **Cleanup**:

   - Archive test project
   - Clear Redis test keys
   - Generate detailed log for debugging

## Integration

This test validates:

- `/team-status` - Agents reporting via Redis
- `/infra-check` - Service availability
- TaskQueue MCP - Task distribution
- Redis MCP - State coordination

````

---

## 📋 Part 6: Slash Command Specifications

### Command 1: `/mycelium-onboarding`

**File**: `~/.claude/plugins/mycelium-core/commands/mycelium-onboarding.md`

```yaml
---
allowed-tools:
  - Bash(uv:*)
  - Bash(docker:*)
  - Bash(nvidia-smi:*)
  - Bash(redis-cli:*)
  - Bash(psql:*)
  - Bash(temporal:*)
  - Write
  - Read
  - Glob
description: Interactive onboarding wizard for Mycelium infrastructure setup. Detects services, guides configuration, and deploys coordination infrastructure.
argument-hint: [--skip-detection] [--non-interactive] [--config <path>]
---

# Mycelium Onboarding

First-time setup wizard for Mycelium multi-agent coordination system.

## Your Task

**Step 1: Detection**
- Detect available services (Redis, Postgres, Temporal, Docker, GPUs)
- Check for existing configuration
- Recommend setup based on environment

**Step 2: Interactive Configuration**
- Launch TUI or CLI wizard
- Guide user through service selection
- Choose deployment method (docker-compose vs baremetal)
- Configure environment isolation

**Step 3: Generation**
- Write `~/.config/mycelium/config.json`
- Generate `docker-compose.yaml` OR `Justfile`
- Create environment isolation scripts
- Set up coordination directories

**Step 4: Deployment**
- Start selected services
- Initialize Redis keys for coordination
- Create TaskQueue project
- Validate with `/infra-check`

**Step 5: Success Report**
- Show service status
- Provide next steps
- Link to documentation
````

### Command 2: `/mycelium-configuration`

**File**: `~/.claude/plugins/mycelium-core/commands/mycelium-configuration.md`

```yaml
---
allowed-tools:
  - Read
  - Write
  - Bash(uv:*)
  - mcp__RedisMCPServer__*
description: View and modify Mycelium configuration. Shows current setup, enables editing services, and can trigger re-onboarding.
argument-hint: [--show] [--edit <service>] [--reset]
---

# Mycelium Configuration Management

View current configuration and modify infrastructure settings.

## Your Task

**Actions**:
1. **View** - Display formatted configuration
2. **Edit** - Modify specific services
3. **Reset** - Clear configuration and re-run onboarding
4. **Export** - Save configuration to file
5. **Import** - Load configuration from file

**Interactive Menu**:
- Show current services and status
- Enable/disable services
- Change deployment method
- Modify environment isolation settings
- Test current configuration
```

### Command 3: `/mycelium-test`

**File**: `~/.claude/plugins/mycelium-core/commands/mycelium-test.md`

```yaml
---
allowed-tools:
  - Bash(uv:*)
  - mcp__RedisMCPServer__*
  - mcp__taskqueue__*
  - Read
  - Write
description: Test agent coordination system with orchestrated tasks. Validates TaskQueue, Redis pub/sub, and multi-agent communication.
argument-hint: [--duration <seconds>] [--agents <list>] [--verbose]
---

# Mycelium Coordination Test

Validate multi-agent infrastructure through orchestrated testing.

## Your Task

**Test Flow**:
1. Initialize test environment
2. Generate mycelium-themed tasks
3. Distribute tasks via TaskQueue
4. Monitor agent coordination via Redis
5. Measure response times and success rates
6. Generate comprehensive report
7. Cleanup test artifacts

**Validation**:
- Agent heartbeats
- Task distribution
- Pub/sub messaging
- Circuit breaker health
- Response latencies
```

______________________________________________________________________

## 📋 Part 7: Implementation Roadmap

### Phase 1: Core Infrastructure (Week 1)

**Deliverables**:

- [ ] Configuration schema and storage
- [ ] Service detection scripts
- [ ] Docker Compose generator
- [ ] Justfile generator
- [ ] Basic CLI onboarding (non-interactive)

**Agents**: devops-engineer, platform-engineer, python-pro

### Phase 2: Interactive UI (Week 2)

**Deliverables**:

- [ ] TUI with `textual` OR CLI wizard with `InquirerPy`
- [ ] Interactive service selection
- [ ] Deployment method chooser
- [ ] Configuration preview and confirmation

**Agents**: cli-developer, ux-researcher, python-pro

### Phase 3: Environment Isolation (Week 2)

**Deliverables**:

- [ ] Python isolation via uv
- [ ] Node.js isolation patterns
- [ ] Ruby isolation patterns
- [ ] Wrapper scripts and enforcement
- [ ] `.envrc` generation for direnv

**Agents**: python-pro, devops-engineer, dependency-manager

### Phase 4: Testing Framework (Week 3)

**Deliverables**:

- [ ] Test orchestrator implementation
- [ ] Mycelium-themed task generator
- [ ] Coordination monitoring
- [ ] Report generation
- [ ] Cleanup automation

**Agents**: multi-agent-coordinator, task-distributor, performance-monitor

### Phase 5: Commands Integration (Week 3)

**Deliverables**:

- [ ] `/mycelium-onboarding` command
- [ ] `/mycelium-configuration` command
- [ ] `/mycelium-test` command
- [ ] Update existing commands to use new config

**Agents**: claude-code-developer, technical-writer

### Phase 6: Documentation & Polish (Week 4)

**Deliverables**:

- [ ] User documentation
- [ ] Developer documentation
- [ ] Video tutorials
- [ ] Migration guide from existing setups
- [ ] Troubleshooting guide

**Agents**: technical-writer, documentation-engineer

______________________________________________________________________

## 📋 Part 8: File Structure

```
~/.config/mycelium/
├── config.json                    # Main configuration
├── docker-compose.yaml            # Docker deployment (if chosen)
├── Justfile                       # Baremetal deployment (if chosen)
├── .envrc                         # Environment isolation
├── logs/                          # Service logs (baremetal)
│   ├── redis.log
│   ├── postgres.log
│   └── temporal.log
├── data/                          # Service data (baremetal)
│   ├── postgres/
│   └── temporal.db
├── pids/                          # Process IDs (baremetal)
├── venvs/                         # Isolated environments
│   └── mycelium/                  # Python venv via uv
└── bin/                           # Wrapper scripts
    ├── python                     # Blocks direct python
    └── node                       # Blocks direct node

~/.claude/plugins/mycelium-core/
├── commands/
│   ├── mycelium-onboarding.md     # NEW
│   ├── mycelium-configuration.md  # NEW
│   ├── mycelium-test.md           # NEW
│   ├── infra-check.md             # UPDATED to use new config
│   └── team-status.md             # UPDATED to use new config
├── lib/
│   ├── onboarding/
│   │   ├── __init__.py
│   │   ├── detect.py              # Service detection
│   │   ├── tui.py                 # Textual TUI
│   │   ├── cli.py                 # Click CLI wizard
│   │   ├── generator.py           # Docker/Justfile generator
│   │   └── config.py              # Config management
│   ├── testing/
│   │   ├── __init__.py
│   │   ├── orchestrator.py        # Test orchestration
│   │   ├── tasks.py               # Task generation
│   │   └── monitor.py             # Coordination monitoring
│   └── isolation/
│       ├── __init__.py
│       ├── python.py              # UV enforcement
│       ├── node.py                # NPM/NPX enforcement
│       └── ruby.py                # Bundler enforcement
└── requirements.txt               # Python dependencies
    ├── textual>=0.40.0
    ├── InquirerPy>=0.3.4
    ├── rich>=13.0.0
    ├── pyyaml>=6.0
    └── redis>=5.0.0
```

______________________________________________________________________

## 📋 Part 9: Dependencies & Requirements

### Python Dependencies

```toml
# ~/.claude/plugins/mycelium-core/pyproject.toml
[project]
name = "mycelium-core"
version = "1.0.0"
requires-python = ">=3.10"

dependencies = [
    "textual>=0.40.0",
    "InquirerPy>=0.3.4",
    "rich>=13.0.0",
    "pyyaml>=6.0",
    "redis>=5.0.0",
    "click>=8.1.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=7.4.0",
    "ruff>=0.1.0",
    "mypy>=1.7.0",
]
```

### System Dependencies

**Docker Compose Deployment**:

- Docker 24.0+
- Docker Compose v2
- nvidia-docker2 (for GPU support)

**Baremetal Deployment**:

- Redis 7.0+
- PostgreSQL 14+
- Temporal CLI 1.4+
- Just 1.14+ (for Justfile)
- OR Foreman/Hivemind (for Procfile)
- OR Supervisord (alternative)

**Common**:

- Python 3.10+
- uv 0.1.0+
- Node.js 18+ (optional)
- Git 2.30+

______________________________________________________________________

## 📋 Part 10: Security & Best Practices

### Security Considerations

1. **Secrets Management**:

   - Store passwords in environment variables
   - Use `.env` files (add to `.gitignore`)
   - Never commit secrets to config files

1. **Network Security**:

   - Bind services to localhost by default
   - Use Docker networks for isolation
   - Enable authentication for Redis/Postgres

1. **Process Isolation**:

   - Run services as non-root users
   - Use systemd user services for baremetal
   - Limit resource usage (cgroups/Docker)

### Best Practices

1. **Configuration Validation**:

   - Schema validation on load
   - Compatibility checks between services
   - Version migration scripts

1. **Graceful Degradation**:

   - Fall back to markdown if Redis unavailable
   - Continue onboarding if optional services fail
   - Clear error messages with remediation steps

1. **Monitoring & Observability**:

   - Log all service starts/stops
   - Publish metrics to Redis
   - Generate health check reports

______________________________________________________________________

## 📋 Part 11: Testing Strategy

### Unit Tests

```python
# tests/test_detection.py
def test_detect_redis_running():
    result = detect_services()
    assert result["redis"]["available"] is True

def test_detect_gpu():
    gpus = detect_gpus()
    assert len(gpus) > 0
    assert gpus[0]["model"] == "NVIDIA RTX 4090"
```

### Integration Tests

```python
# tests/test_onboarding.py
def test_docker_compose_generation():
    config = {
        "services": {"redis": {"enabled": True}},
        "deployment": {"method": "docker-compose"}
    }

    compose_file = generate_docker_compose(config)
    assert "redis:" in compose_file
    assert "6379:6379" in compose_file

def test_justfile_generation():
    config = {
        "services": {"redis": {"enabled": True}},
        "deployment": {"method": "baremetal"}
    }

    justfile = generate_justfile(config)
    assert "start-redis:" in justfile
    assert "[parallel]" in justfile
```

### End-to-End Tests

```python
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
```

______________________________________________________________________

## 📋 Part 12: Migration Path

For users with existing setups:

1. **Detect Existing Configuration**:

   - Check for running services
   - Import existing Redis/Postgres credentials
   - Preserve existing data

1. **Migration Wizard**:

   - Show detected configuration
   - Offer to adopt existing services
   - Create config from current state

1. **Backwards Compatibility**:

   - Support legacy `.infra-check.json` format
   - Auto-upgrade to new config schema
   - Maintain old slash commands

______________________________________________________________________

## 🎯 Success Criteria

**Onboarding**:

- [ ] Complete setup in \<5 minutes
- [ ] Support both Docker and baremetal
- [ ] Detect 90%+ of existing services
- [ ] Zero manual config file editing required

**Configuration**:

- [ ] View config in \<1 second
- [ ] Edit services without restart
- [ ] Export/import configurations
- [ ] Validate config before applying

**Testing**:

- [ ] Complete test in \<60 seconds
- [ ] 100% agent response rate
- [ ] Clear pass/fail results
- [ ] Actionable error messages

**Isolation**:

- [ ] Block direct python/pip execution
- [ ] Enforce uv for all Python commands
- [ ] Isolate Node.js with npx
- [ ] No system pollution

______________________________________________________________________

## 📞 Questions for Review Agents

### For @agent-devops-engineer:

1. **Docker Compose vs Justfile**: Which would you recommend as default? Should we support both?

1. **Supervisord Alternative**: Is supervisord overkill, or would it provide better process management than Justfile?

1. **Service Dependencies**: How should we handle startup ordering in Justfile? (e.g., Temporal needs Postgres first)

1. **Health Checks**: Should we implement retries and backoff for service startup validation?

1. **GPU Access**: How should we expose GPU in Docker Compose? Host network mode or device mapping?

### For @agent-platform-engineer:

1. **Environment Isolation**: Is the uv wrapper script approach sufficient, or should we use more aggressive
   enforcement?

1. **Directory Structure**: Is `~/.config/mycelium/` the right location, or should we use XDG_CONFIG_HOME?

1. **Multiple Projects**: How should we handle users working on multiple projects with different Mycelium configs?

1. **Performance**: Will Python wrapper scripts add noticeable latency?

### For @agent-python-pro:

1. **TUI vs CLI**: Should we implement both, or pick one? Which provides better UX?

1. **Async Coordination**: Should the test orchestrator use asyncio for monitoring, or is polling sufficient?

1. **Type Safety**: Should we use Pydantic for config validation?

1. **Error Handling**: What's the best pattern for graceful degradation in onboarding?

### For @agent-claude-code-developer:

1. **Slash Command Integration**: How should these commands invoke the Python TUI/CLI? Via subprocess or direct Python
   execution?

1. **Permission Model**: Are the tool permissions specified correctly for the new commands?

1. **Command Dependencies**: Should `/mycelium-test` automatically run `/infra-check` first?

1. **Plugin Updates**: How should we handle config schema changes in plugin updates?

### For @agent-multi-agent-coordinator:

1. **Test Design**: Are the mycelium-themed tasks appropriate for testing coordination?

1. **Agent Selection**: Which agents should be included in the default test suite?

1. **Failure Scenarios**: How should the test handle partial failures (e.g., 3/5 agents respond)?

1. **Metrics**: What coordination metrics are most important to track?

______________________________________________________________________

## 🔚 End of Plan

This plan is now ready for review by specialized agents. After incorporating their feedback, we'll proceed with
implementation.

**Generated**: 2025-10-13 **Version**: 1.0.0-draft **Status**: Awaiting agent review
