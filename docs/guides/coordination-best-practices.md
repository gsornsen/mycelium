# Multi-Agent Coordination Best Practices

**Purpose:** Design patterns, anti-patterns, and proven strategies for effective multi-agent workflows

**Audience:** Developers building workflows with S1 (Discovery) and S2 (Coordination)

______________________________________________________________________

## Table of Contents

1. [Workflow Design Principles](#workflow-design-principles)
1. [Agent Discovery Strategies](#agent-discovery-strategies)
1. [Context Management](#context-management)
1. [Failure Handling](#failure-handling)
1. [Performance Optimization](#performance-optimization)
1. [Security and Privacy](#security-and-privacy)
1. [Testing and Validation](#testing-and-validation)
1. [Common Anti-Patterns](#common-anti-patterns)

______________________________________________________________________

## Workflow Design Principles

### Principle 1: Single Responsibility

**Each workflow step should have a clear, focused purpose.**

```python
# ✅ GOOD: Clear single purpose per step
workflow = coordinate_workflow(
    steps=[
        {
            "agent": "data-validator",
            "task": "Validate CSV data format and completeness",
            "params": {"file": "data.csv", "schema": "schema.json"}
        },
        {
            "agent": "data-transformer",
            "task": "Transform validated data to JSON format",
            "depends_on": ["step-0"],
            "params": {"input": "data.csv", "output": "data.json"}
        },
        {
            "agent": "data-loader",
            "task": "Load transformed data into PostgreSQL",
            "depends_on": ["step-1"],
            "params": {"file": "data.json", "table": "users"}
        }
    ]
)

# ❌ BAD: Vague, multi-purpose steps
workflow = coordinate_workflow(
    steps=[
        {
            "agent": "data-engineer",
            "task": "Process data",  # Too vague
            "params": {"file": "data.csv"}
        },
        {
            "agent": "backend-developer",
            "task": "Do database stuff",  # Unclear purpose
            "depends_on": ["step-0"]
        }
    ]
)
```

**Why:** Clear, focused steps are easier to debug, monitor, and reuse. Vague tasks lead to inconsistent results and
difficult troubleshooting.

### Principle 2: Explicit Dependencies

**Make step dependencies explicit and meaningful.**

```python
# ✅ GOOD: Explicit dependencies with clear reasons
workflow = coordinate_workflow(
    steps=[
        {
            "agent": "backend-developer",
            "task": "Implement API endpoints",
            "params": {"spec": "api-spec.yaml"}
        },
        {
            "agent": "database-architect",
            "task": "Design database schema for API",
            "params": {"entities": ["User", "Order", "Product"]}
        },
        {
            "agent": "backend-developer",
            "task": "Connect API endpoints to database",
            "depends_on": ["step-0", "step-1"],  # Needs both complete
            "params": {"orm": "SQLAlchemy"}
        },
        {
            "agent": "qa-expert",
            "task": "Integration testing of API with database",
            "depends_on": ["step-2"],  # Only needs implementation done
            "params": {"test_cases": "tests/integration/"}
        }
    ]
)

# ❌ BAD: Implicit or missing dependencies
workflow = coordinate_workflow(
    steps=[
        {"agent": "backend-developer", "task": "Implement API"},
        {"agent": "database-architect", "task": "Design schema"},
        {"agent": "backend-developer", "task": "Connect them"},  # Missing depends_on!
        {"agent": "qa-expert", "task": "Test everything"}  # Missing depends_on!
    ]
)
```

**Why:** Explicit dependencies prevent race conditions, ensure proper ordering, and make workflow logic transparent.

### Principle 3: Appropriate Granularity

**Balance between too many small steps and too few large steps.**

```python
# ✅ GOOD: Balanced granularity
workflow = coordinate_workflow(
    steps=[
        {
            "agent": "code-analyzer",
            "task": "Analyze code complexity and identify refactoring candidates",
            "params": {"threshold": "complexity > 10"}
        },
        {
            "agent": "refactoring-expert",
            "task": "Refactor complex functions",
            "depends_on": ["step-0"],
            "params": {"focus": "reduce_complexity"}
        },
        {
            "agent": "test-generator",
            "task": "Generate tests for refactored code",
            "depends_on": ["step-1"],
            "params": {"coverage_target": 90}
        }
    ]
)

# ❌ BAD: Too fine-grained (micro-steps)
workflow = coordinate_workflow(
    steps=[
        {"agent": "analyzer", "task": "Load code"},
        {"agent": "analyzer", "task": "Parse AST"},
        {"agent": "analyzer", "task": "Calculate metrics"},
        {"agent": "analyzer", "task": "Format report"},
        {"agent": "refactor", "task": "Find function A"},
        {"agent": "refactor", "task": "Simplify function A"},
        # ... 20 more micro-steps
    ]
)

# ❌ BAD: Too coarse-grained (mega-steps)
workflow = coordinate_workflow(
    steps=[
        {
            "agent": "full-stack-developer",
            "task": "Analyze, refactor, test, and deploy entire codebase",
            "params": {"everything": True}
        }
    ]
)
```

**Why:** Too many steps increase coordination overhead; too few steps lose benefits of specialization and make failure
recovery difficult.

**Rule of Thumb:** 3-7 steps per workflow is optimal for most use cases.

______________________________________________________________________

## Agent Discovery Strategies

### Strategy 1: Specific Over Generic

**Use specific queries that match agent specializations.**

```python
# ✅ GOOD: Specific, targeted queries
# For API performance issues
agents = discover_agents("API performance optimization latency reduction")

# For database design
agents = discover_agents("PostgreSQL schema design normalization")

# For security audit
agents = discover_agents("web application security OWASP authentication")

# ❌ BAD: Generic queries
agents = discover_agents("development")  # Too vague
agents = discover_agents("help")  # No useful information
agents = discover_agents("computer stuff")  # Meaningless
```

**Why:** Specific queries leverage NLP matching to find the most relevant specialists, while generic queries return
random results.

### Strategy 2: Multi-Stage Discovery

**Use discovery results to refine subsequent searches.**

```python
# ✅ GOOD: Multi-stage discovery
async def find_optimal_team(task_description):
    # Stage 1: Find primary agent
    primary = discover_agents(task_description, limit=1)

    # Stage 2: Get primary agent's details to understand needs
    details = get_agent_details(primary["agents"][0]["id"])

    # Stage 3: Find complementary agents based on dependencies
    team = [primary["agents"][0]]
    for dependency in details["metadata"]["dependencies"]:
        agent = discover_agents(f"{dependency} specialist", limit=1)
        team.append(agent["agents"][0])

    return team

# ❌ BAD: One-shot discovery without refinement
agents = discover_agents("complex task requiring multiple specialists")
# Hope for the best with top 5 results
```

**Why:** Multi-stage discovery builds better teams by understanding relationships and complementary skills.

### Strategy 3: Confidence-Based Selection

**Use confidence scores to make intelligent agent choices.**

```python
# ✅ GOOD: Confidence-aware selection
agents = discover_agents("machine learning model deployment", limit=10)

# High-confidence agent for critical task
if agents["agents"][0]["confidence"] > 0.9:
    primary_agent = agents["agents"][0]
else:
    # Get human approval if no high-confidence match
    primary_agent = await get_human_selection(agents["agents"])

# Multiple agents for collaborative task
collaborators = [
    agent for agent in agents["agents"]
    if agent["confidence"] > 0.7
]

# ❌ BAD: Ignoring confidence scores
agents = discover_agents("some task")
chosen = agents["agents"][0]  # Blindly use first result
```

**Why:** Confidence scores indicate match quality; high-confidence matches are more likely to succeed.

______________________________________________________________________

## Context Management

### Strategy 1: Minimal Necessary Context

**Pass only what the agent needs to complete their task.**

```python
# ✅ GOOD: Minimal, relevant context
context = {
    "files": ["auth.py", "models/user.py"],  # Only relevant files
    "focus_areas": ["password_hashing", "session_management"],
    "security_standard": "OWASP_ASVS_4.0",
    "current_issues": [
        "Password stored without salt",
        "Session tokens not rotating"
    ]
}

result = handoff_to_agent(
    target_agent="security-expert",
    task="Security audit of authentication system",
    context=context
)

# ❌ BAD: Excessive context
context = {
    "entire_codebase": read_all_files(),  # Unnecessary
    "git_history": get_full_git_log(),  # Too much
    "dependency_tree": get_all_dependencies(),  # Irrelevant
    "random_notes": "check security maybe?",  # Unstructured
    "last_10_conversations": [...],  # Historical clutter
}
```

**Why:** Minimal context reduces token usage, improves processing speed, and helps agents focus on what matters.

### Strategy 2: Structured Context Schemas

**Use consistent, well-defined context structures.**

```python
# ✅ GOOD: Structured context with schema
SECURITY_AUDIT_CONTEXT = {
    "files": List[str],           # Files to audit
    "focus_areas": List[str],     # Security domains
    "standards": str,             # Compliance standard
    "known_issues": List[Dict],   # Previous findings
    "constraints": Dict           # Time, scope, etc.
}

context = {
    "files": ["auth.py", "api/endpoints.py"],
    "focus_areas": ["authentication", "authorization", "input_validation"],
    "standards": "OWASP_ASVS_4.0",
    "known_issues": [
        {
            "type": "SQL_INJECTION",
            "file": "api/search.py",
            "line": 42,
            "severity": "CRITICAL"
        }
    ],
    "constraints": {
        "time_limit_hours": 2,
        "scope": "authentication_only"
    }
}

# ❌ BAD: Unstructured context
context = {
    "stuff": "some files and things",
    "info": ["random", "data", 123, None, True],
    "notes": "check security things I guess",
}
```

**Why:** Structured context is predictable, validatable, and easier for agents to parse and use effectively.

### Strategy 3: Context Compression

**Compress large data using references and summaries.**

```python
# ✅ GOOD: Compressed context with references
context = {
    "database_schema": "file://database/schema.sql",  # Reference
    "slow_queries_log": "file://logs/slow_queries.txt",  # Reference
    "summary": {
        "tables_affected": ["users", "orders", "products"],
        "slowest_query_time_ms": 5000,
        "p95_latency_ms": 1200,
        "daily_query_volume": 1000000
    },
    "sample_queries": [
        "SELECT * FROM users WHERE created_at > ?",  # Example
        "SELECT COUNT(*) FROM orders GROUP BY user_id"  # Example
    ]
}

# ❌ BAD: Embedded large data
context = {
    "schema": read_file("schema.sql"),  # 500KB embedded
    "all_queries": read_file("logs/queries.txt"),  # 50MB embedded
    "every_table": [...]  # Huge array
}
```

**Why:** File references and summaries reduce context size dramatically while preserving necessary information.

______________________________________________________________________

## Failure Handling

### Strategy 1: Appropriate Failure Strategies

**Choose failure strategies based on workflow criticality.**

```python
# ✅ GOOD: Critical deployment - abort on failure
deployment_workflow = coordinate_workflow(
    steps=[
        {"agent": "build-engineer", "task": "Build application"},
        {"agent": "qa-expert", "task": "Run integration tests"},
        {"agent": "devops-engineer", "task": "Deploy to production"}
    ],
    failure_strategy="abort"  # Critical - stop if any step fails
)

# ✅ GOOD: Best-effort analysis - continue on failure
analysis_workflow = coordinate_workflow(
    steps=[
        {"agent": "code-analyzer", "task": "Analyze code quality"},
        {"agent": "security-scanner", "task": "Security scan"},
        {"agent": "dependency-checker", "task": "Check outdated dependencies"}
    ],
    failure_strategy="continue"  # Non-critical - collect all results
)

# ✅ GOOD: Fallback for production service
service_workflow = coordinate_workflow(
    steps=[
        {
            "agent": "ml-engineer",
            "task": "Deploy new ML model",
            "fallback": {
                "agent": "ml-engineer",
                "task": "Rollback to previous model version"
            }
        }
    ],
    failure_strategy="fallback"
)

# ❌ BAD: Wrong strategy for critical workflow
deployment_workflow = coordinate_workflow(
    steps=[...],
    failure_strategy="continue"  # Dangerous! Could deploy broken code
)
```

**Failure Strategy Guide:**

- **abort**: Critical workflows (deployment, data migration)
- **retry**: Transient failures (network issues, rate limits)
- **fallback**: Production services (degraded but functional)
- **continue**: Best-effort collection (analysis, reporting)

### Strategy 2: Defensive Step Design

**Design steps to be idempotent and recoverable.**

```python
# ✅ GOOD: Idempotent steps
workflow = coordinate_workflow(
    steps=[
        {
            "agent": "database-admin",
            "task": "Create users table if not exists",
            "params": {"ddl": "CREATE TABLE IF NOT EXISTS users (...)"}
        },
        {
            "agent": "data-loader",
            "task": "Load data with upsert (insert or update)",
            "params": {"mode": "upsert", "key": "user_id"}
        }
    ]
)

# ❌ BAD: Non-idempotent steps
workflow = coordinate_workflow(
    steps=[
        {
            "agent": "database-admin",
            "task": "Create users table",  # Fails if table exists
            "params": {"ddl": "CREATE TABLE users (...)"}
        },
        {
            "agent": "data-loader",
            "task": "Insert all data",  # Fails if data exists
            "params": {"mode": "insert"}
        }
    ]
)
```

**Why:** Idempotent steps can be safely retried without causing duplicate work or errors.

### Strategy 3: Comprehensive Error Context

**Capture sufficient error context for debugging.**

```python
# ✅ GOOD: Rich error context
try:
    workflow = coordinate_workflow(steps=[...])
except WorkflowExecutionError as e:
    # Get detailed failure information
    events = get_coordination_events(
        workflow_id=e.workflow_id,
        event_type="failure"
    )

    for event in events["events"]:
        print(f"Failed Step: {event['metadata']['step']}")
        print(f"Agent: {event['metadata']['agent']}")
        print(f"Error: {event['metadata']['error']}")
        print(f"Context: {event['metadata']['context']}")
        print(f"Timestamp: {event['timestamp']}")

        # Log to monitoring system
        logger.error(
            "Workflow step failed",
            extra={
                "workflow_id": e.workflow_id,
                "step": event['metadata']['step'],
                "agent": event['metadata']['agent'],
                "error": event['metadata']['error']
            }
        )

# ❌ BAD: Minimal error handling
try:
    workflow = coordinate_workflow(steps=[...])
except Exception as e:
    print(f"Failed: {e}")  # No context, hard to debug
```

**Why:** Detailed error context enables rapid diagnosis and resolution of workflow failures.

______________________________________________________________________

## Performance Optimization

### Strategy 1: Parallel Execution When Possible

**Execute independent steps in parallel to reduce latency.**

```python
# ✅ GOOD: Parallel independent tasks
workflow = coordinate_workflow(
    steps=[
        # These can run in parallel
        {
            "agent": "frontend-developer",
            "task": "Build React components"
        },
        {
            "agent": "backend-developer",
            "task": "Implement API endpoints"
        },
        {
            "agent": "database-architect",
            "task": "Design database schema"
        },
        # This waits for all three
        {
            "agent": "integration-engineer",
            "task": "Connect frontend, backend, and database",
            "depends_on": ["step-0", "step-1", "step-2"]
        }
    ],
    execution_mode="parallel"
)

# ❌ BAD: Unnecessary sequential execution
workflow = coordinate_workflow(
    steps=[
        {"agent": "frontend-developer", "task": "Build components"},
        {
            "agent": "backend-developer",
            "task": "Implement API",
            "depends_on": ["step-0"]  # Not actually dependent!
        },
        {
            "agent": "database-architect",
            "task": "Design schema",
            "depends_on": ["step-1"]  # Not actually dependent!
        }
    ],
    execution_mode="sequential"
)
```

**Performance Impact:** Parallel execution can reduce total workflow time by 50-70% for independent tasks.

### Strategy 2: Agent Caching

**Reuse agents across multiple calls to avoid initialization overhead.**

```python
# ✅ GOOD: Reuse discovered agents
async def code_review_pipeline(files):
    # Discover agents once
    reviewer = discover_agents("code review", limit=1)["agents"][0]
    security = discover_agents("security audit", limit=1)["agents"][0]

    # Reuse for multiple files
    results = []
    for file in files:
        workflow = coordinate_workflow(
            steps=[
                {"agent": reviewer["id"], "task": f"Review {file}"},
                {
                    "agent": security["id"],
                    "task": f"Security scan {file}",
                    "depends_on": ["step-0"]
                }
            ]
        )
        results.append(workflow)

    return results

# ❌ BAD: Rediscover agents for each file
async def code_review_pipeline(files):
    results = []
    for file in files:
        # Wasteful rediscovery
        reviewer = discover_agents("code review")["agents"][0]
        security = discover_agents("security audit")["agents"][0]

        workflow = coordinate_workflow(
            steps=[
                {"agent": reviewer["id"], "task": f"Review {file}"},
                {"agent": security["id"], "task": f"Security scan {file}"}
            ]
        )
        results.append(workflow)
```

**Performance Impact:** Eliminates redundant discovery calls, saving 100-500ms per reuse.

### Strategy 3: Workflow Batching

**Batch similar tasks to reduce coordination overhead.**

```python
# ✅ GOOD: Batch similar tasks
workflow = coordinate_workflow(
    steps=[
        {
            "agent": "test-generator",
            "task": "Generate tests for multiple modules",
            "params": {
                "modules": ["auth.py", "api.py", "models.py"],  # Batch
                "coverage_target": 90
            }
        }
    ]
)

# ❌ BAD: Individual workflows for each task
for module in ["auth.py", "api.py", "models.py"]:
    workflow = coordinate_workflow(
        steps=[
            {
                "agent": "test-generator",
                "task": f"Generate tests for {module}",
                "params": {"module": module}
            }
        ]
    )
```

**Performance Impact:** Reduces coordination overhead from N workflows to 1, saving 200-400ms per task.

______________________________________________________________________

## Security and Privacy

### Strategy 1: Principle of Least Privilege

**Grant agents access only to what they need.**

```python
# ✅ GOOD: Minimal access
context = {
    "files": ["specific/file.py"],  # Only files needed
    "permissions": ["read"],  # Read-only
    "scope": "security_audit_only"  # Limited scope
}

result = handoff_to_agent(
    target_agent="security-expert",
    task="Audit authentication in file.py",
    context=context
)

# ❌ BAD: Excessive access
context = {
    "files": get_all_files(),  # Everything
    "permissions": ["read", "write", "execute"],  # Too much
    "scope": "unlimited"  # No boundaries
}
```

**Why:** Limiting access reduces risk of accidental or malicious modifications.

### Strategy 2: Sensitive Data Handling

**Never pass sensitive data directly in context.**

```python
# ✅ GOOD: Reference sensitive data indirectly
context = {
    "database_config_path": "config/database.yml",  # Reference
    "credentials_source": "vault://prod/db-credentials",  # Secure vault
    "redacted_query_log": "logs/queries_redacted.txt"  # Pre-redacted
}

# ❌ BAD: Sensitive data in context
context = {
    "database_password": "super_secret_123",  # Exposed!
    "api_keys": ["key1", "key2", "key3"],  # Exposed!
    "user_data": [
        {"email": "user@example.com", "ssn": "123-45-6789"}  # PII!
    ]
}
```

**Why:** Context may be logged, cached, or transmitted; sensitive data must be protected.

### Strategy 3: Audit Trail

**Maintain comprehensive audit logs for coordination.**

```python
# ✅ GOOD: Comprehensive audit logging
async def audited_workflow(workflow_spec):
    # Log workflow initiation
    audit_log.record({
        "event": "workflow_started",
        "workflow_spec": workflow_spec,
        "user": get_current_user(),
        "timestamp": datetime.now(UTC)
    })

    try:
        workflow = coordinate_workflow(**workflow_spec)

        # Log completion
        audit_log.record({
            "event": "workflow_completed",
            "workflow_id": workflow["workflow_id"],
            "duration_ms": workflow["total_duration_ms"],
            "timestamp": datetime.now(UTC)
        })

        return workflow

    except Exception as e:
        # Log failure
        audit_log.record({
            "event": "workflow_failed",
            "error": str(e),
            "timestamp": datetime.now(UTC)
        })
        raise

# Get audit trail
events = get_coordination_events(workflow_id="wf-123")
for event in events["events"]:
    audit_log.record(event)
```

**Why:** Audit trails enable compliance, debugging, and security investigations.

______________________________________________________________________

## Testing and Validation

### Strategy 1: Test Workflows Incrementally

**Build and test workflows step by step.**

```python
# ✅ GOOD: Incremental testing
def test_code_review_workflow():
    # Test step 1 alone
    step1 = coordinate_workflow(
        steps=[
            {"agent": "python-pro", "task": "Review code style"}
        ]
    )
    assert step1["status"] == "completed"

    # Test steps 1-2
    step1_2 = coordinate_workflow(
        steps=[
            {"agent": "python-pro", "task": "Review code style"},
            {
                "agent": "security-expert",
                "task": "Security audit",
                "depends_on": ["step-0"]
            }
        ]
    )
    assert step1_2["status"] == "completed"
    assert len(step1_2["results"]) == 2

    # Test full workflow
    full_workflow = coordinate_workflow(
        steps=[...all_steps]
    )
    assert full_workflow["status"] == "completed"

# ❌ BAD: Test everything at once
def test_code_review_workflow():
    workflow = coordinate_workflow(
        steps=[...20_complex_steps]
    )
    assert workflow["status"] == "completed"  # Hard to debug if fails
```

**Why:** Incremental testing isolates failures and makes debugging easier.

### Strategy 2: Mock Agents for Testing

**Use mock agents to test coordination logic without real agents.**

```python
# ✅ GOOD: Mock agents for testing
from unittest.mock import Mock, patch

def test_workflow_coordination_logic():
    # Mock agent discovery
    mock_discover = Mock(return_value={
        "agents": [
            {"id": "mock-agent-1", "confidence": 0.95},
            {"id": "mock-agent-2", "confidence": 0.90}
        ]
    })

    # Mock workflow execution
    mock_coordinate = Mock(return_value={
        "workflow_id": "test-wf-123",
        "status": "completed",
        "results": [...]
    })

    with patch('discover_agents', mock_discover):
        with patch('coordinate_workflow', mock_coordinate):
            # Test your logic
            result = my_workflow_function()
            assert result["status"] == "completed"
            mock_discover.assert_called_once()
            mock_coordinate.assert_called_once()
```

**Why:** Mocks enable fast, reliable testing without dependency on real agents.

### Strategy 3: Validate Workflow Structure

**Validate workflow definitions before execution.**

```python
# ✅ GOOD: Validation before execution
def validate_workflow_spec(steps):
    """Validate workflow structure."""
    if not steps:
        raise ValueError("Workflow must have at least one step")

    step_ids = [f"step-{i}" for i in range(len(steps))]

    for step in steps:
        # Required fields
        if "agent" not in step:
            raise ValueError("Each step must have 'agent'")
        if "task" not in step:
            raise ValueError("Each step must have 'task'")

        # Validate dependencies
        for dep in step.get("depends_on", []):
            if dep not in step_ids:
                raise ValueError(f"Invalid dependency: {dep}")

    # Check for circular dependencies
    if has_circular_dependencies(steps):
        raise ValueError("Circular dependencies detected")

    return True

# Use validation
workflow_spec = {...}
validate_workflow_spec(workflow_spec["steps"])
workflow = coordinate_workflow(**workflow_spec)
```

**Why:** Early validation prevents runtime failures and provides clear error messages.

______________________________________________________________________

## Common Anti-Patterns

### Anti-Pattern 1: Chatty Workflows

**PROBLEM:** Too many small handoffs increase coordination overhead.

```python
# ❌ ANTI-PATTERN: Excessive handoffs
async def process_files(files):
    for file in files:
        # Handoff for each file - wasteful!
        await handoff_to_agent(
            "file-processor",
            f"Process {file}"
        )

# ✅ SOLUTION: Batch processing
async def process_files(files):
    await handoff_to_agent(
        "file-processor",
        "Process files in batch",
        context={"files": files}  # Single handoff
    )
```

**Impact:** Reduces coordination overhead by 90%+

### Anti-Pattern 2: God Workflows

**PROBLEM:** Single workflow trying to do everything.

```python
# ❌ ANTI-PATTERN: Monolithic workflow
workflow = coordinate_workflow(
    steps=[
        # 50 steps covering entire application lifecycle
        {"agent": "...", "task": "..."},
        # ...
        {"agent": "...", "task": "..."}
    ]
)

# ✅ SOLUTION: Compose smaller workflows
frontend_workflow = coordinate_workflow(steps=[...5_frontend_steps])
backend_workflow = coordinate_workflow(steps=[...5_backend_steps])
deployment_workflow = coordinate_workflow(steps=[...3_deployment_steps])

# Compose results
full_result = {
    "frontend": frontend_workflow,
    "backend": backend_workflow,
    "deployment": deployment_workflow
}
```

**Why:** Smaller workflows are easier to test, debug, and maintain.

### Anti-Pattern 3: Implicit State

**PROBLEM:** Relying on side effects instead of explicit state passing.

```python
# ❌ ANTI-PATTERN: Implicit state via files
workflow = coordinate_workflow(
    steps=[
        {
            "agent": "data-processor",
            "task": "Process data and write to /tmp/result.json"  # Side effect
        },
        {
            "agent": "analyzer",
            "task": "Analyze data in /tmp/result.json",  # Implicit dependency
            "depends_on": ["step-0"]
        }
    ]
)

# ✅ SOLUTION: Explicit state passing
workflow = coordinate_workflow(
    steps=[
        {
            "agent": "data-processor",
            "task": "Process data",
            "params": {"output_file": "result.json"}
        },
        {
            "agent": "analyzer",
            "task": "Analyze processed data",
            "depends_on": ["step-0"],
            "params": {
                "input": "{{step-0.output_file}}"  # Explicit reference
            }
        }
    ]
)
```

**Why:** Explicit state is predictable, testable, and easier to debug.

### Anti-Pattern 4: No Failure Planning

**PROBLEM:** Assuming all steps will succeed.

```python
# ❌ ANTI-PATTERN: No error handling
workflow = coordinate_workflow(
    steps=[
        {"agent": "...", "task": "..."},
        {"agent": "...", "task": "..."}
    ]
)
# Hope nothing fails!

# ✅ SOLUTION: Comprehensive failure handling
workflow = coordinate_workflow(
    steps=[
        {"agent": "...", "task": "..."},
        {
            "agent": "...",
            "task": "...",
            "depends_on": ["step-0"],
            "fallback": {
                "agent": "...",
                "task": "Fallback action"
            }
        }
    ],
    failure_strategy="fallback"
)

# Monitor and handle failures
try:
    result = workflow
except WorkflowExecutionError as e:
    handle_failure(e)
```

**Why:** Failure handling prevents cascading failures and enables graceful degradation.

______________________________________________________________________

## Summary Checklist

Use this checklist when designing workflows:

**Workflow Design:**

- [ ] Each step has clear, single purpose
- [ ] Dependencies are explicit and necessary
- [ ] Appropriate granularity (3-7 steps typical)
- [ ] Failure strategy matches criticality

**Agent Discovery:**

- [ ] Specific queries that match specializations
- [ ] Confidence scores considered
- [ ] Multi-stage discovery for complex teams

**Context Management:**

- [ ] Minimal necessary context only
- [ ] Structured, schema-based context
- [ ] Sensitive data handled securely
- [ ] Large data referenced, not embedded

**Performance:**

- [ ] Independent steps run in parallel
- [ ] Agents reused across multiple calls
- [ ] Similar tasks batched when possible

**Security:**

- [ ] Least privilege access
- [ ] No sensitive data in context
- [ ] Comprehensive audit trail

**Testing:**

- [ ] Incremental workflow testing
- [ ] Workflow structure validated
- [ ] Mock agents used for unit tests

**Avoid Anti-Patterns:**

- [ ] No chatty workflows (excessive handoffs)
- [ ] No god workflows (monolithic)
- [ ] No implicit state dependencies
- [ ] Comprehensive failure planning

______________________________________________________________________

**Document Version:** 1.0 **Last Updated:** 2025-10-21 **Related Docs:**

- [S1: Agent Discovery](/home/gerald/git/mycelium/docs/skills/S1-agent-discovery.md)
- [S2: Coordination](/home/gerald/git/mycelium/docs/skills/S2-coordination.md)
- [Quick Start Guide](/home/gerald/git/mycelium/docs/guides/discovery-coordination-quickstart.md)
- [Troubleshooting](/home/gerald/git/mycelium/docs/troubleshooting/discovery-coordination.md)
