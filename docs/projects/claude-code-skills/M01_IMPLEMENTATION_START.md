# M01: Agent Discovery & Coordination Skills - Implementation Start

**Purpose:** Use this document to kickstart M01 implementation in a fresh Claude Code session **Status:** Ready to Begin
**Linear Issues:** Created and ready for tracking **Last Updated:** 2025-10-20

______________________________________________________________________

## Quick Start Command

```
In your new session, say:

"Start implementing M01 Agent Discovery & Coordination Skills following the plan in /home/gerald/git/mycelium/docs/projects/claude-code-skills/M01_IMPLEMENTATION_START.md"
```

______________________________________________________________________

## Project Context

### What is M01?

M01 is the **foundation milestone** for the Claude Code Skills project. It delivers:

**Core Deliverables:**

- **S1: Agent Discovery Skill** - NLP-based agent matching with 90% accuracy
- **S2: Coordination Skill** - Multi-agent workflow orchestration
- **Agent Registry** - PostgreSQL 15+ with pgvector for embeddings
- **Discovery API** - RESTful endpoints for agent discovery
- **Coordination Protocol** - Agent-to-agent communication system
- **Telemetry Infrastructure** - Opt-in analytics (default: OFF)

**Duration:** 6-7 weeks **Effort:** 135 hours **Phase:** MLP (Minimum Lovable Product)

### Why M01 Matters

M01 establishes the foundational infrastructure that **all future milestones depend on**:

- M02 needs the agent registry for skill-agent mapping
- M03 needs the orchestration engine for budget integration
- M04 needs the coordination protocol for workflow execution
- M05 needs the telemetry infrastructure for analytics

**Success = Foundation is solid, performant, and extensible**

______________________________________________________________________

## Team Assembly

### Required Agents

Assemble these Mycelium agents for M01 implementation:

**Lead:**

- **multi-agent-coordinator** - Overall M01 coordination and Task 1.10 (Documentation)

**Core Implementation:**

- **backend-developer** - Tasks 1.1, 1.2, 1.6, 1.7, 1.11
- **ai-engineer** - Tasks 1.3, 1.5
- **python-pro** - Tasks 1.4, 1.8
- **qa-expert** - Task 1.9

**Support:**

- **postgres-pro** - PostgreSQL + pgvector setup and optimization
- **devops-engineer** - Infrastructure setup, deployment
- **security-auditor** - Security review for telemetry and APIs

### Agent Responsibilities

| Agent                   | Tasks                    | Hours | Focus Area                         |
| ----------------------- | ------------------------ | ----- | ---------------------------------- |
| backend-developer       | 1.1, 1.2, 1.6, 1.7, 1.11 | 68h   | Infrastructure, APIs, coordination |
| ai-engineer             | 1.3, 1.5                 | 36h   | NLP matching, protocols            |
| python-pro              | 1.4, 1.8                 | 24h   | MCP tool integration               |
| qa-expert               | 1.9                      | 12h   | Testing framework                  |
| multi-agent-coordinator | 1.10                     | 8h    | Documentation                      |
| postgres-pro            | Support                  | 8h    | Database optimization              |
| devops-engineer         | Support                  | 4h    | Infrastructure                     |
| security-auditor        | Support                  | 4h    | Security review                    |

______________________________________________________________________

## Implementation Plan

### Week 1: Database Foundation

**Goals:**

- PostgreSQL 15+ with pgvector installed and configured
- Agent registry schema created
- Basic CRUD operations working

**Tasks to Complete:**

- **Task 1.1:** Agent Registry Infrastructure (16h)
- **Task 1.11:** Telemetry Infrastructure (12h)

**Team Focus:**

- **backend-developer**: Lead Task 1.1
- **postgres-pro**: Support pgvector setup
- **backend-developer**: Lead Task 1.11

**Validation:**

- [ ] PostgreSQL 15+ running with pgvector extension
- [ ] Registry schema created with vector columns
- [ ] Can insert/query agents with metadata
- [ ] Telemetry config system operational (default: OFF)
- [ ] Unit tests passing for registry operations

**Deliverables:**

```
plugins/mycelium-core/registry/
├── schema.sql              # PostgreSQL schema with pgvector
├── registry.py             # Registry implementation
├── migrations/             # Migration scripts
└── telemetry/
    ├── client.py           # Telemetry client
    ├── config.py           # Configuration management
    └── anonymization.py    # Privacy layer

tests/unit/
├── test_registry.py
└── test_telemetry.py

docs/api/
└── registry-api.md
```

### Week 2: Discovery & APIs

**Goals:**

- Agent discovery API operational
- NLP matching engine integrated
- pgvector similarity search working

**Tasks to Complete:**

- **Task 1.2:** Discovery API Endpoints (12h)
- **Task 1.3:** NLP Capability Matching Engine (20h)

**Team Focus:**

- **backend-developer**: Lead Task 1.2
- **ai-engineer**: Lead Task 1.3
- **postgres-pro**: Optimize pgvector indexes

**Validation:**

- [ ] Discovery API endpoints responding (\<100ms)
- [ ] NLP embeddings generated for all agents
- [ ] Similarity search working with pgvector HNSW
- [ ] Matching accuracy >85% on test queries
- [ ] OpenAPI spec generated

**Deliverables:**

```
plugins/mycelium-core/api/
└── discovery.py            # Discovery API

plugins/mycelium-core/matching/
├── matcher.py              # NLP matching engine
├── embeddings/             # Cached embeddings
└── config.py               # HNSW configuration

tests/
├── integration/test_discovery_api.py
└── unit/test_matcher.py
├── fixtures/matching_test_queries.json

docs/api/
├── discovery-api.yaml      # OpenAPI spec
└── discovery-quickstart.md
```

### Week 3: MCP Integration

**Goals:**

- Agent discovery accessible via MCP tools
- Claude Code can discover agents
- Integration testing framework ready

**Tasks to Complete:**

- **Task 1.4:** Agent Discovery MCP Tool (12h)
- **Task 1.9:** Integration Testing Framework (start - 6h)

**Team Focus:**

- **python-pro**: Lead Task 1.4
- **qa-expert**: Start Task 1.9

**Validation:**

- [ ] `discover_agents` MCP tool working
- [ ] `get_agent_details` MCP tool working
- [ ] Claude Code can invoke tools successfully
- [ ] Integration test framework scaffolded

**Deliverables:**

```
plugins/mycelium-core/mcp/tools/
├── discovery_tools.py      # MCP tool implementation
└── config/discovery.json   # Tool configuration

tests/integration/
├── test_discovery_mcp.py
└── fixtures/coordination_scenarios.json

docs/skills/
└── S1-agent-discovery.md   # Skill documentation
```

### Week 4: Coordination Infrastructure

**Goals:**

- Handoff protocol implemented
- Workflow orchestration engine operational
- Agent-to-agent coordination working

**Tasks to Complete:**

- **Task 1.5:** Handoff Protocol Implementation (16h)
- **Task 1.6:** Workflow Orchestration Engine (20h)

**Team Focus:**

- **ai-engineer**: Lead Task 1.5
- **backend-developer**: Lead Task 1.6

**Validation:**

- [ ] Handoff message schema validated
- [ ] Context preservation working
- [ ] Orchestration engine handles dependencies
- [ ] State management with rollback support
- [ ] Multi-agent workflows executable

**Deliverables:**

```
plugins/mycelium-core/coordination/
├── protocol.py             # Handoff protocol
├── schemas/handoff.json    # JSON schema
├── orchestrator.py         # Orchestration engine
└── state_manager.py        # State management

tests/unit/
├── test_handoff_protocol.py
└── test_orchestrator.py

tests/integration/
└── test_orchestration.py

docs/technical/
├── handoff-protocol.md
└── orchestration-engine.md
```

### Week 5: Coordination Completion

**Goals:**

- Coordination tracking operational
- Coordination MCP tool working
- Integration testing complete

**Tasks to Complete:**

- **Task 1.7:** Coordination Tracking System (12h)
- **Task 1.8:** Coordination MCP Tool (12h)
- **Task 1.9:** Integration Testing Framework (complete - 6h)

**Team Focus:**

- **backend-developer**: Lead Task 1.7
- **python-pro**: Lead Task 1.8
- **qa-expert**: Complete Task 1.9

**Validation:**

- [ ] All coordination events logged
- [ ] `coordinate_workflow` MCP tool working
- [ ] `handoff_to_agent` MCP tool working
- [ ] Integration tests covering 2, 3, 5-agent workflows
- [ ] Test coverage >85%

**Deliverables:**

```
plugins/mycelium-core/coordination/
├── tracker.py              # Event tracking
└── schemas/events.json     # Event schema

plugins/mycelium-core/mcp/tools/
├── coordination_tools.py   # MCP tools
└── config/coordination.json

tests/integration/
├── test_coordination_mcp.py
├── test_discovery_coordination.py
└── fixtures/coordination_scenarios.json

tests/performance/
└── benchmark_coordination.py

docs/
├── skills/S2-coordination.md
└── operations/coordination-tracking.md
```

### Week 6: Documentation & Polish

**Goals:**

- All documentation complete
- Demo scenario validated
- Performance benchmarks passing
- Code review complete

**Tasks to Complete:**

- **Task 1.10:** Documentation & Examples (8h)
- Final integration testing and bug fixes
- Performance optimization
- Security review

**Team Focus:**

- **multi-agent-coordinator**: Lead Task 1.10
- **qa-expert**: Final validation
- **security-auditor**: Security review
- **All team**: Bug fixes and polish

**Validation:**

- [ ] All documentation complete and reviewed
- [ ] Demo scenario executes successfully
- [ ] Performance benchmarks meet targets
- [ ] Security review passed
- [ ] All acceptance criteria met

**Deliverables:**

```
docs/skills/
├── S1-agent-discovery.md
└── S2-coordination.md

docs/guides/
├── discovery-coordination-quickstart.md
└── coordination-best-practices.md

docs/troubleshooting/
└── discovery-coordination.md
```

### Week 7: Demo & MLP Review

**Goals:**

- Executive demo prepared
- MLP review with stakeholders
- M01 signed off
- M02 kickoff ready

**Activities:**

- Execute full demo scenario (15 minutes)
- Stakeholder review and feedback
- Address any critical feedback
- Sign off on M01 completion
- Prepare M02 environment

______________________________________________________________________

## Technical Setup

### Prerequisites

**Infrastructure:**

```bash
# PostgreSQL 15+ with extensions
docker-compose up -d postgres

# Verify extensions
psql -c "CREATE EXTENSION IF NOT EXISTS vector;"
psql -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# Create database
psql -c "CREATE DATABASE mycelium_registry;"

# Apply schema
psql -d mycelium_registry -f plugins/mycelium-core/registry/schema.sql
```

**Development Environment:**

```bash
# Install dependencies
uv sync

# Install NLP dependencies
uv pip install sentence-transformers scikit-learn

# Install testing dependencies
uv pip install pytest pytest-asyncio pytest-benchmark pytest-postgresql

# Set up pre-commit hooks
pre-commit install
```

**Environment Variables:**

```bash
# .env
DATABASE_URL=postgresql://localhost:5432/mycelium_registry
POSTGRES_USER=mycelium
POSTGRES_PASSWORD=<secure-password>
TELEMETRY_ENABLED=false
TELEMETRY_ENDPOINT=https://mycelium-telemetry.sornsen.io
```

### Repository Structure

```
/home/gerald/git/mycelium/
├── plugins/mycelium-core/
│   ├── registry/           # Task 1.1
│   ├── api/                # Task 1.2
│   ├── matching/           # Task 1.3
│   ├── coordination/       # Tasks 1.5, 1.6, 1.7
│   ├── mcp/tools/          # Tasks 1.4, 1.8
│   └── telemetry/          # Task 1.11
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── performance/
│   └── fixtures/
└── docs/
    ├── api/
    ├── skills/
    ├── guides/
    ├── technical/
    └── operations/
```

______________________________________________________________________

## Task Execution Guide

### For Each Task

**1. Read the Task Details**

- Location: Milestone document, find "Task X.Y" section
- Understand: Description, acceptance criteria, deliverables

**2. Check Dependencies**

- Verify: All dependent tasks are complete
- If blocked: Wait for dependencies or request help

**3. Create Feature Branch**

```bash
git checkout -b feat/m01-task-X.Y-description
# Example: git checkout -b feat/m01-task-1.1-agent-registry
```

**4. Implement**

- Follow acceptance criteria as checklist
- Write tests alongside implementation
- Document as you go

**5. Test**

```bash
# Unit tests
pytest tests/unit/test_<feature>.py -v

# Integration tests (if applicable)
pytest tests/integration/test_<feature>.py -v

# Performance benchmarks (if applicable)
pytest tests/performance/benchmark_<feature>.py --benchmark-only
```

**6. Code Review**

- Ensure >85% test coverage
- Run linting: `ruff check .`
- Type check: `mypy plugins/mycelium-core/`
- Format: `ruff format .`

**7. Update Linear**

- Check off acceptance criteria in Linear issue
- Add comment with implementation notes
- Move to "Ready for Review" status

**8. Request Validation**

- Tag Gerald in Linear issue
- Provide demo/test instructions
- Wait for validation before marking complete

**9. Mark Complete (After Gerald's Validation)**

- Gerald marks Linear issue as complete
- Merge feature branch
- Move to next task

______________________________________________________________________

## Critical Path (Priority Order)

Execute tasks in this order to minimize blocking:

### Phase 1 (Parallel - Week 1)

Start simultaneously:

- **Task 1.1**: Agent Registry (blocks 1.2, 1.3, 1.5)
- **Task 1.11**: Telemetry (independent, can run in parallel)

### Phase 2 (Parallel - Week 2)

After Task 1.1 completes, start:

- **Task 1.2**: Discovery API (depends 1.1, blocks 1.4)
- **Task 1.3**: NLP Matching (depends 1.1, blocks 1.4)
- **Task 1.5**: Handoff Protocol (depends 1.1, blocks 1.6)

### Phase 3 (Sequential - Week 3)

- **Task 1.4**: Discovery MCP Tool (depends 1.2, 1.3)
- **Task 1.6**: Orchestration Engine (depends 1.5, blocks 1.7, 1.8)

### Phase 4 (Sequential - Week 4)

- **Task 1.7**: Coordination Tracking (depends 1.6, blocks 1.8)
- **Task 1.8**: Coordination MCP Tool (depends 1.6, 1.7, blocks 1.9)

### Phase 5 (Week 5)

- **Task 1.9**: Integration Testing (depends 1.4, 1.8)
- **Task 1.10**: Documentation (depends 1.4, 1.8)

### Phase 6 (Week 6-7)

- Final integration testing
- Demo preparation
- Bug fixes and polish

______________________________________________________________________

## Task Details Reference

### Task 1.1: Agent Registry Infrastructure (16h)

**Owner:** backend-developer **Priority:** P0 (Critical) **Dependencies:** None

**What to Build:** PostgreSQL-based agent registry with pgvector for semantic search.

**Key Acceptance Criteria:**

- PostgreSQL 15+ with pgvector extension installed
- Schema with vector columns for embeddings
- CRUD operations for agent metadata
- Registry populated with 130+ Mycelium agents
- Query performance \<100ms
- Unit tests >90% coverage

**Files to Create:**

- `plugins/mycelium-core/registry/schema.sql`
- `plugins/mycelium-core/registry/registry.py`
- `plugins/mycelium-core/registry/migrations/`
- `tests/unit/test_registry.py`
- `docs/api/registry-api.md`

**Technical Notes:**

- Use existing `plugins/mycelium-core/agents/index.json` as data source
- pgvector for 384-dim embeddings (sentence-transformers)
- HNSW index for fast similarity search

**Linear Issue:** `[M01] Task 1.1: Agent Registry Infrastructure`

______________________________________________________________________

### Task 1.2: Discovery API Endpoints (12h)

**Owner:** backend-developer **Priority:** P0 (Critical) **Dependencies:** Task 1.1

**What to Build:** RESTful API for agent discovery, search, and metadata retrieval.

**Key Acceptance Criteria:**

- `/api/v1/agents/discover` endpoint (query parameter)
- `/api/v1/agents/{agent_id}` endpoint (get details)
- `/api/v1/agents/search` endpoint (full-text)
- Input validation with error messages
- OpenAPI 3.0 spec generated
- Rate limiting (100 req/min)
- Response time \<100ms

**Files to Create:**

- `plugins/mycelium-core/api/discovery.py`
- `docs/api/discovery-api.yaml`
- `tests/integration/test_discovery_api.py`
- `docs/api/discovery-quickstart.md`

**Technical Notes:**

- Use FastAPI or Flask
- Integrate with registry.py from Task 1.1
- OpenAPI spec auto-generated from code

**Linear Issue:** `[M01] Task 1.2: Discovery API Endpoints`

______________________________________________________________________

### Task 1.3: NLP Capability Matching Engine (20h)

**Owner:** ai-engineer **Priority:** P0 (Critical) **Dependencies:** Task 1.1

**What to Build:** Semantic matching using embeddings and pgvector similarity search.

**Key Acceptance Criteria:**

- Embedding model integrated (sentence-transformers/all-MiniLM-L6-v2)
- Agent embeddings pre-computed and stored in pgvector
- Cosine similarity matching algorithm
- Confidence scoring (0.0-1.0)
- Matching accuracy >85% on test dataset (100+ queries)
- Performance \<200ms latency
- Fallback for low-confidence matches

**Files to Create:**

- `plugins/mycelium-core/matching/matcher.py`
- `plugins/mycelium-core/matching/embeddings/`
- `tests/unit/test_matcher.py`
- `tests/fixtures/matching_test_queries.json`
- `docs/technical/matching-algorithm.md`

**Technical Notes:**

- sentence-transformers/all-MiniLM-L6-v2 recommended (384-dim)
- Store embeddings in registry with pgvector
- HNSW index for fast similarity search
- Test dataset: 100+ queries with ground truth

**Linear Issue:** `[M01] Task 1.3: NLP Capability Matching Engine`

______________________________________________________________________

### Task 1.4: Agent Discovery MCP Tool (12h)

**Owner:** python-pro **Priority:** P1 (High) **Dependencies:** Task 1.2, Task 1.3

**What to Build:** MCP tool wrapper exposing discovery to Claude Code.

**Key Acceptance Criteria:**

- `discover_agents` MCP tool (natural language query)
- `get_agent_details` MCP tool (agent metadata)
- Formatted responses with confidence scores
- Error handling with actionable messages
- Registered in MCP server config
- End-to-end \<500ms

**Files to Create:**

- `plugins/mycelium-core/mcp/tools/discovery_tools.py`
- `plugins/mycelium-core/mcp/config/discovery.json`
- `tests/integration/test_discovery_mcp.py`
- `docs/skills/S1-agent-discovery.md`

**Technical Notes:**

- Follow MCP protocol specification
- Return ranked results with scores
- Handle timeout gracefully

**Linear Issue:** `[M01] Task 1.4: Agent Discovery MCP Tool`

______________________________________________________________________

### Task 1.5: Handoff Protocol Implementation (16h)

**Owner:** ai-engineer **Priority:** P0 (Critical) **Dependencies:** Task 1.1

**What to Build:** JSON-based protocol for agent-to-agent state transfer.

**Key Acceptance Criteria:**

- JSON schema for handoff messages
- Serialization/deserialization utilities
- Schema validation with error messages
- Context preservation for nested data
- Backward compatibility layer
- Performance \<100ms for message processing

**Files to Create:**

- `plugins/mycelium-core/coordination/protocol.py`
- `plugins/mycelium-core/coordination/schemas/handoff.json`
- `tests/unit/test_handoff_protocol.py`
- `docs/technical/handoff-protocol.md`

**Technical Notes:**

- JSON schema with source, target, context, state, metadata
- Support for nested coordination
- Version field for protocol evolution

**Linear Issue:** `[M01] Task 1.5: Handoff Protocol Implementation`

______________________________________________________________________

### Task 1.6: Workflow Orchestration Engine (20h)

**Owner:** backend-developer **Priority:** P1 (High) **Dependencies:** Task 1.5

**What to Build:** Workflow execution engine with dependency resolution and failure recovery.

**Key Acceptance Criteria:**

- Sequential workflow support
- Dependency resolution (prerequisites, ordering)
- State persistence with rollback
- Failure recovery (retry, fallback, abort)
- Parallel coordination for independent tasks
- Real-time progress tracking
- Multi-agent workflows (3+ agents) validated

**Files to Create:**

- `plugins/mycelium-core/coordination/orchestrator.py`
- `plugins/mycelium-core/coordination/state_manager.py`
- `tests/integration/test_orchestration.py`
- `docs/technical/orchestration-engine.md`

**Technical Notes:**

- DAG-based execution
- State machine per task
- Memory overhead \<50MB per workflow

**Linear Issue:** `[M01] Task 1.6: Workflow Orchestration Engine`

______________________________________________________________________

### Task 1.7: Coordination Tracking System (12h)

**Owner:** backend-developer **Priority:** P2 (Medium) **Dependencies:** Task 1.6

**What to Build:** Event logging for all inter-agent communications and coordination.

**Key Acceptance Criteria:**

- Event schema for coordination events
- Structured logging with timestamps
- Query API for history retrieval
- Performance impact \<5%
- Integration with existing logging
- Storage \<10MB per 1000 events

**Files to Create:**

- `plugins/mycelium-core/coordination/tracker.py`
- `plugins/mycelium-core/coordination/schemas/events.json`
- `tests/integration/test_tracking.py`
- `docs/operations/coordination-tracking.md`

**Technical Notes:**

- PostgreSQL for persistence
- Indexed by workflow_id, agent_id, timestamp

**Linear Issue:** `[M01] Task 1.7: Coordination Tracking System`

______________________________________________________________________

### Task 1.8: Coordination MCP Tool (12h)

**Owner:** python-pro **Priority:** P1 (High) **Dependencies:** Task 1.6, Task 1.7

**What to Build:** MCP tools for workflow orchestration from Claude Code.

**Key Acceptance Criteria:**

- `coordinate_workflow` MCP tool
- `handoff_to_agent` MCP tool
- `get_workflow_status` MCP tool
- Workflow execution status in responses
- Error handling with context
- Multi-agent scenarios tested

**Files to Create:**

- `plugins/mycelium-core/mcp/tools/coordination_tools.py`
- `plugins/mycelium-core/mcp/config/coordination.json`
- `tests/integration/test_coordination_mcp.py`
- `docs/skills/S2-coordination.md`

**Technical Notes:**

- Tools expose orchestrator capabilities
- WebSocket for real-time updates (optional)

**Linear Issue:** `[M01] Task 1.8: Coordination MCP Tool`

______________________________________________________________________

### Task 1.9: Integration Testing Framework (12h)

**Owner:** qa-expert **Priority:** P1 (High) **Dependencies:** Task 1.4, Task 1.8

**What to Build:** Comprehensive testing for discovery and coordination workflows.

**Key Acceptance Criteria:**

- Test scenarios: single agent, 2-agent, 3-agent, 5-agent workflows
- Edge case tests (no matches, failures, timeouts)
- Performance tests validating SLAs
- Test coverage >85%
- CI/CD integration
- Test documentation

**Files to Create:**

- `tests/integration/test_discovery_coordination.py`
- `tests/fixtures/coordination_scenarios.json`
- `tests/performance/benchmark_coordination.py`
- `docs/testing/integration-testing-guide.md`

**Technical Notes:**

- Use pytest-asyncio for async tests
- pytest-benchmark for performance
- Fixtures for common scenarios

**Linear Issue:** `[M01] Task 1.9: Integration Testing Framework`

______________________________________________________________________

### Task 1.10: Documentation & Examples (8h)

**Owner:** multi-agent-coordinator **Priority:** P2 (Medium) **Dependencies:** Task 1.4, Task 1.8

**What to Build:** Complete documentation for S1 and S2 skills.

**Key Acceptance Criteria:**

- S1 and S2 skill documentation
- Usage examples for common patterns
- Best practices for workflow design
- Troubleshooting guide
- API reference complete
- Quick start guide (\<15 min to proficiency)

**Files to Create:**

- `docs/skills/S1-agent-discovery.md`
- `docs/skills/S2-coordination.md`
- `docs/guides/discovery-coordination-quickstart.md`
- `docs/guides/coordination-best-practices.md`
- `docs/troubleshooting/discovery-coordination.md`

**Technical Notes:**

- Include code examples
- Reference demo scenario
- Link to API docs

**Linear Issue:** `[M01] Task 1.10: Documentation & Examples`

______________________________________________________________________

### Task 1.11: Telemetry Infrastructure (12h)

**Owner:** backend-developer **Priority:** P2 (Medium) **Dependencies:** None (can run in parallel)

**What to Build:** Opt-in telemetry with privacy-preserving design.

**Key Acceptance Criteria:**

- Telemetry disabled by default
- Explicit opt-in configuration
- Default endpoint: mycelium-telemetry.sornsen.io
- Configurable endpoint (self-hosting)
- Privacy-preserving anonymization (hashed IDs)
- Zero impact if disabled
- Graceful degradation on endpoint failure

**Files to Create:**

- `plugins/mycelium-core/telemetry/client.py`
- `plugins/mycelium-core/telemetry/anonymization.py`
- `plugins/mycelium-core/telemetry/config.py`
- `tests/telemetry/test_privacy.py`
- `docs/telemetry-configuration.md`

**Technical Notes:**

- Never collect: prompts, responses, code, PII
- Collect only: agent usage, performance metrics, errors (anonymized)
- Rate limiting and batching
- Async sending (non-blocking)

**Linear Issue:** `[M01] Task 1.11: Telemetry Infrastructure`

______________________________________________________________________

## Demo Scenario (Final Validation)

### Multi-Agent Code Review Workflow

**Purpose:** Validate that M01 deliverables work end-to-end

**Duration:** 15 minutes

**Prerequisite:**

- All tasks 1.1-1.11 complete
- PostgreSQL + pgvector operational
- MCP server running
- Test data prepared

**Execution:**

```bash
# 1. Environment Setup (2 min)
cd /home/gerald/git/mycelium
./bin/mycelium-switch development
pytest tests/integration/test_discovery_coordination.py -v

# Verify all tests pass
# Verify registry has 130+ agents
# Verify MCP tools registered

# 2. Create Test File (1 min)
cat > /tmp/demo/sample_module.py << 'EOF'
def process_data(data):
    result = []
    for item in data:
        if item > 0:
            if item < 100:
                result.append(item * 2)
            else:
                result.append(item)
    return result
EOF

# 3. Agent Discovery Demo (3 min)
# In Claude Code conversation:
User: "I need comprehensive code review on /tmp/demo/sample_module.py including style, security, and performance"

# Expected: Claude Code uses discover_agents tool
# Returns: python-pro (0.95), security-expert (0.89), performance-optimizer (0.87)
# Verify: Discovery <500ms, confidence scores correct

# 4. Multi-Agent Coordination Demo (4 min)
User: "Coordinate python-pro, security-expert, and performance-optimizer to review this file in sequence"

# Expected: Claude Code uses coordinate_workflow tool
# Orchestrates: python-pro → security-expert → performance-optimizer
# Verify: Context preserved, 3 handoffs logged, final output aggregates findings

# 5. Coordination Tracking Demo (2 min)
User: "Show me the coordination events for this workflow"

# Expected: Detailed event log with timestamps
# Verify: 3 handoffs logged, state preservation visible

# 6. Failure Recovery Demo (3 min)
# Disable security-expert temporarily
mv plugins/mycelium-core/agents/03-security-expert.md \
   plugins/mycelium-core/agents/03-security-expert.md.disabled

User: "Run the same review again"

# Expected: Workflow detects failure, retries once, falls back gracefully
# Verify: Failure logged, retry attempted, user notified clearly

# 7. Cleanup
./bin/mycelium-switch usage
rm -rf /tmp/demo/
mv plugins/mycelium-core/agents/03-security-expert.md.disabled \
   plugins/mycelium-core/agents/03-security-expert.md
```

**Success Criteria:**

- [ ] Agent discovery works with natural language
- [ ] Multi-agent coordination maintains context
- [ ] Coordination tracking logs complete history
- [ ] Failure recovery operates correctly
- [ ] Performance \<500ms discovery, \<5s total workflow
- [ ] Demo reproducible without assistance

**After Demo:**

- Record demo for documentation
- Collect stakeholder feedback
- Document any issues found
- Create follow-up tasks if needed

______________________________________________________________________

## Success Metrics

### Must Achieve Before M01 Sign-Off

**Functional:**

- [ ] All 11 tasks complete with acceptance criteria met
- [ ] Demo scenario executes flawlessly
- [ ] Integration tests passing (>85% coverage)
- [ ] All deliverables created and documented

**Performance:**

- [ ] Agent discovery \<100ms (P95)
- [ ] Coordination handoff \<500ms (P95)
- [ ] Query performance validated under load
- [ ] Memory usage reasonable (\<500MB baseline)

**Quality:**

- [ ] Code review approved by technical lead
- [ ] Security review passed (especially telemetry)
- [ ] Documentation >90% complete
- [ ] No critical bugs

**Stakeholder:**

- [ ] Gerald validates all demos
- [ ] Team satisfied with foundation
- [ ] Ready to build M02 on this base

______________________________________________________________________

## Communication Protocol

### Daily Standups

**When:** Every morning, 10am **Duration:** 15 minutes **Format:** Async Slack or quick video

**Template:**

```
Agent: [Your agent name]
Yesterday: [What you completed]
Today: [What you're working on]
Blockers: [Any issues or dependencies waiting]
```

### Progress Updates

**When:** End of each task completion **Where:** Linear issue comments **What:** Brief summary of implementation, any
deviations, next steps

### Blocker Escalation

**If blocked >4 hours:**

1. Comment on Linear issue
1. Tag Gerald and relevant agent
1. Propose workaround or ask for help
1. Update in daily standup

### Code Reviews

**When:** Before marking task complete **Who:** 2+ team members (technical lead for critical tasks) **Checklist:**

- [ ] Code quality (ruff, mypy pass)
- [ ] Tests pass (>85% coverage)
- [ ] Documentation updated
- [ ] Performance benchmarks met
- [ ] Security reviewed (if applicable)

______________________________________________________________________

## Validation Process

### For Each Task

**1. Self-Validation:**

- Run all acceptance criteria checks
- Execute relevant tests
- Verify deliverables created
- Check performance benchmarks

**2. Peer Review:**

- Request code review from 1-2 agents
- Address feedback
- Re-test after changes

**3. Gerald's Validation:**

- Demo the feature
- Walk through acceptance criteria
- Answer questions
- **Wait for Gerald to mark Linear issue complete**

**4. Only After Gerald Approves:**

- Merge feature branch
- Update documentation
- Move to next task

______________________________________________________________________

## Risk Mitigation

### Common Risks in M01

**Risk 1: NLP Matching Accuracy \<85%**

- **If occurs:** Try different embedding model, create better test dataset
- **Contingency:** Implement hybrid matching (embeddings + keywords)
- **Escalate if:** Can't achieve >80% after 8 hours of tuning

**Risk 2: PostgreSQL Performance Issues**

- **If occurs:** Optimize pgvector HNSW index parameters
- **Contingency:** Add query result caching (Redis)
- **Escalate if:** Can't achieve \<100ms after optimization

**Risk 3: State Management Complexity**

- **If occurs:** Simplify to forward-only state transitions
- **Contingency:** Defer rollback to M02
- **Escalate if:** Implementation taking >25 hours

**Risk 4: Integration Breaking Changes**

- **If occurs:** Feature flags to toggle new functionality
- **Contingency:** Parallel operation (old + new systems)
- **Escalate if:** Existing workflows breaking

______________________________________________________________________

## Reference Documents

### Essential Reading

**Before Starting:**

1. `M01_AGENT_DISCOVERY_SKILLS.md` - Complete milestone specification
1. `architecture.md` - Overall technical architecture
1. `TECHNICAL_ARCHITECTURE_SKILLS.md` - Detailed design

**During Implementation:**

1. Milestone document - For acceptance criteria
1. API documentation - For interface specs
1. Test scenarios - For validation

**For Decisions:**

1. `FEEDBACK_INCORPORATION_PLAN.md` - Technology choices rationale
1. Technical lead's M01 review - Implementation guidance

### File Locations

All documents in: `/home/gerald/git/mycelium/docs/projects/claude-code-skills/`

**Key Files:**

- Milestone spec: `milestones/M01_AGENT_DISCOVERY_SKILLS.md`
- Architecture: `architecture.md`
- Metrics: `success-metrics.md`
- Tech details: `../TECHNICAL_ARCHITECTURE_SKILLS.md`
- Roadmap: `../SKILLS_TECHNICAL_ROADMAP.md`
- Quick start: `../SKILLS_IMPLEMENTATION_QUICKSTART.md`

______________________________________________________________________

## Getting Help

### Technical Questions

- Reference: `TECHNICAL_ARCHITECTURE_SKILLS.md`
- Ask: technical lead (claude-code-developer agent)
- Escalate: Gerald if blocking

### Scope Questions

- Reference: Milestone acceptance criteria
- Ask: project-manager agent
- Escalate: Gerald for scope changes

### Architecture Decisions

- Reference: `architecture.md`
- Ask: architect-reviewer agent
- Escalate: Gerald for major changes

______________________________________________________________________

## Completion Checklist

### M01 Done When:

**All Tasks Complete:**

- [ ] Task 1.1 ✓ (Gerald validated)
- [ ] Task 1.2 ✓ (Gerald validated)
- [ ] Task 1.3 ✓ (Gerald validated)
- [ ] Task 1.4 ✓ (Gerald validated)
- [ ] Task 1.5 ✓ (Gerald validated)
- [ ] Task 1.6 ✓ (Gerald validated)
- [ ] Task 1.7 ✓ (Gerald validated)
- [ ] Task 1.8 ✓ (Gerald validated)
- [ ] Task 1.9 ✓ (Gerald validated)
- [ ] Task 1.10 ✓ (Gerald validated)
- [ ] Task 1.11 ✓ (Gerald validated)

**Success Metrics:**

- [ ] Discovery accuracy >85%
- [ ] Coordination latency \<500ms
- [ ] Test coverage >85%
- [ ] Performance benchmarks passing
- [ ] Security review passed
- [ ] Demo executes successfully

**Stakeholder Approval:**

- [ ] Gerald signs off on M01
- [ ] Team ready for M02
- [ ] No critical blockers

### Then Move to M02

Read: `M02_SKILL_INFRASTRUCTURE.md` Follow: Similar implementation process Focus: Filesystem-based skills + Web UI
components

______________________________________________________________________

**M01 Implementation Start Guide Complete**

Point to this document in your next session to begin M01 implementation with the full team assembled and ready to
execute!
