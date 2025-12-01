# M5: MCP Server Execution - Coordination Master

## Mission

Coordinate implementation of M5: MCP Server Execution with three parallel teams.

## Timeline

- Start: 2025-11-30
- Target: Single coordination session
- Teams: 3 parallel workstreams

## Team Assignments

### Team 1: MCP Execution Tools

- **Agent**: `mycelium-core:mcp-developer`
- **Status**: Pending
- **Deliverables**:
  - `invoke_agent` tool
  - `get_workflow_status` tool
  - Integration with ProcessManager
  - Unit tests
- **Brief**: `/home/gerald/git/mycelium/docs/m5/TEAM1_MCP_EXECUTION_TOOLS.md`
- **Redis Key**: `mycelium:m5:team1:status`

### Team 2: Consent System

- **Agent**: `mycelium-core:security-engineer`
- **Status**: Pending
- **Deliverables**:
  - ConsentManager class
  - CLI consent prompts
  - Persistence layer
  - Re-consent logic
  - Unit tests
- **Brief**: `/home/gerald/git/mycelium/docs/m5/TEAM2_CONSENT_SYSTEM.md`
- **Redis Key**: `mycelium:m5:team2:status`

### Team 3: Environment Isolation

- **Agent**: `mycelium-core:security-engineer`
- **Status**: Pending
- **Deliverables**:
  - EnvironmentIsolation class
  - OutputSanitizer class
  - Credential patterns
  - Unit tests
- **Brief**: `/home/gerald/git/mycelium/docs/m5/TEAM3_ENVIRONMENT_ISOLATION.md`
- **Redis Key**: `mycelium:m5:team3:status`

## Integration Phase

- **Coordinator**: Multi-agent coordinator
- **Plan**: `/home/gerald/git/mycelium/docs/m5/INTEGRATION_PLAN.md`
- **Tests**: Integration tests + full suite

## Redis Coordination Schema

```
mycelium:m5:coordination
  - status: "initializing" | "in_progress" | "integrating" | "completed"
  - started_at: ISO timestamp
  - completed_at: ISO timestamp

mycelium:m5:team1
  - name: "MCP Execution Tools"
  - status: "pending" | "in_progress" | "completed" | "failed"
  - task: Description
  - deliverables: List of files
  - started_at: ISO timestamp
  - completed_at: ISO timestamp
  - result: Success/failure info

mycelium:m5:team2
  - name: "Consent System"
  - status: "pending" | "in_progress" | "completed" | "failed"
  - task: Description
  - deliverables: List of files
  - started_at: ISO timestamp
  - completed_at: ISO timestamp
  - result: Success/failure info

mycelium:m5:team3
  - name: "Environment Isolation"
  - status: "pending" | "in_progress" | "completed" | "failed"
  - task: Description
  - deliverables: List of files
  - started_at: ISO timestamp
  - completed_at: ISO timestamp
  - result: Success/failure info
```

## Event Stream

```
Channel: mycelium:m5:events

Events:
  - team1:started
  - team1:completed
  - team2:started
  - team2:completed
  - team3:started
  - team3:completed
  - integration:started
  - integration:completed
  - m5:completed
```

## Exit Criteria

### Team 1

- [ ] `invoke_agent` tool works via MCP
- [ ] `get_workflow_status` tool works via MCP
- [ ] ProcessManager integration complete
- [ ] Workflow state in Redis
- [ ] Tests passing

### Team 2

- [ ] ConsentManager implemented
- [ ] CLI prompts working
- [ ] Consent persistence working
- [ ] Re-consent on checksum change working
- [ ] Tests passing

### Team 3

- [ ] EnvironmentIsolation implemented
- [ ] OutputSanitizer implemented
- [ ] Sensitive vars blocked
- [ ] Output sanitization working
- [ ] Tests passing

### Integration

- [ ] Consent wired into invoke_agent
- [ ] Isolation wired into ProcessManager
- [ ] All integration tests passing
- [ ] Full test suite passing
- [ ] Documentation complete

## Risk Mitigation

### Parallel Work Conflicts

- Each team works on separate files
- Clear interfaces defined upfront
- Integration team handles wiring

### Security Requirements

- Team 2 and Team 3 both security-focused
- Comprehensive threat model
- Security audit before merge

### Testing Strategy

- Unit tests per team
- Integration tests after merge
- End-to-end tests for complete flow

## Communication Protocol

### Status Updates

Teams update Redis hash:

```bash
mcp__RedisMCPServer__hset("mycelium:m5:team1", "status", "in_progress")
```

### Event Broadcasting

Teams publish completion:

```bash
mcp__RedisMCPServer__publish("mycelium:m5:events", "team1:completed")
```

### Progress Tracking

Coordinator monitors all team hashes:

```bash
mcp__RedisMCPServer__hgetall("mycelium:m5:team1")
mcp__RedisMCPServer__hgetall("mycelium:m5:team2")
mcp__RedisMCPServer__hgetall("mycelium:m5:team3")
```

## Rollback Plan

If any team fails:

1. Review failure reason
1. Provide guidance/fixes
1. Re-run failed team
1. Proceed when all teams complete

If integration fails:

1. Review integration issues
1. Fix wiring problems
1. Re-run integration tests
1. Verify full suite

## Success Metrics

- **Coordination Efficiency**: \<5% overhead
- **Parallel Execution**: All teams start simultaneously
- **Integration Success**: First-time integration success
- **Test Coverage**: >90% for new code
- **Security**: 100% of requirements met
- **Timeline**: Complete in single session

## Current Status

**Overall**: Coordination infrastructure ready **Team 1**: Pending - brief ready **Team 2**: Pending - brief ready
**Team 3**: Pending - brief ready **Integration**: Pending - plan ready

## Next Steps

1. Execute all three teams in parallel
1. Monitor progress via Redis
1. Handle any blockers
1. Run integration phase
1. Validate all exit criteria
1. Report completion
