# Linear Import Instructions for Claude Code Skills Project

**Purpose:** This document provides everything needed to create Linear issues from the Claude Code Skills project plan in a new session with Linear MCP server.

**Last Updated:** 2025-10-20

---

## Quick Start

```
In your new Linear MCP session, say:

"Create Linear issues for the Claude Code Skills project using the plan in /home/gerald/git/mycelium/docs/projects/claude-code-skills/. Follow the instructions in LINEAR_IMPORT_INSTRUCTIONS.md."
```

---

## Project Overview

### Project Details

**Project Name:** Claude Code Skills
**Team:** Mycelium Engineering
**Owner:** Gerald Sornsen
**Priority:** High
**Target Start:** Q1 2025
**Duration:** 24 weeks (596 hours)

### Project Description

Implement Claude Code Skills framework for Mycelium, enabling:
- Agent discovery and coordination
- Dynamic skill loading with hot-reload
- Token budget optimization with warnings
- Web-based workflow orchestration
- Privacy-first analytics and telemetry

**Key Technologies:**
- PostgreSQL 15+ with pgvector and TimescaleDB extensions
- TanStack (React Query, Router, Table, Virtual)
- Radix UI + Tailwind CSS + Storybook
- Textual (TUI framework)
- Filesystem-based skill repository

**Expected Impact:**
- 40-60% token reduction
- 80% workflow overhead reduction
- Modern web UI and TUI interfaces
- Privacy-first telemetry (opt-in)

---

## Linear Structure

### Create These Milestones (in Linear)

Create 5 Linear milestones matching these project phases:

1. **MLP - Agent Discovery & Coordination**
   - Target: Weeks 1-7
   - Description: Foundation for multi-agent workflows with PostgreSQL + pgvector + telemetry
   - Issues: 11 tasks from M01

2. **Dogfooding - Skill Infrastructure**
   - Target: Weeks 5-10
   - Description: Filesystem-based skills with dynamic loading, web UI, and design system
   - Issues: 8+ tasks from M02

3. **Beta - Token Optimization**
   - Target: Weeks 9-14
   - Description: Budget warnings, TimescaleDB analytics, and compression
   - Issues: 11 tasks from M03

4. **Beta Feedback - Orchestration**
   - Target: Weeks 13-18
   - Description: Web workflow builder with visual DAG editor
   - Issues: 10 tasks from M04

5. **GA - Analytics & Self-Optimization**
   - Target: Weeks 17-24
   - Description: Privacy-first analytics dashboards and self-optimization
   - Issues: 10 tasks from M05

---

## Issue Creation Instructions

### For Each Milestone

Read the corresponding milestone file:
- M01: `/home/gerald/git/mycelium/docs/projects/claude-code-skills/milestones/M01_AGENT_DISCOVERY_SKILLS.md`
- M02: `/home/gerald/git/mycelium/docs/projects/claude-code-skills/milestones/M02_SKILL_INFRASTRUCTURE.md`
- M03: `/home/gerald/git/mycelium/docs/projects/claude-code-skills/milestones/M03_TOKEN_OPTIMIZATION.md`
- M04: `/home/gerald/git/mycelium/docs/projects/claude-code-skills/milestones/M04_ORCHESTRATION.md`
- M05: `/home/gerald/git/mycelium/docs/projects/claude-code-skills/milestones/M05_ANALYTICS_COMPRESSION.md`

### Issue Template

For each task in the milestone (e.g., Task 1.1, Task 1.2, etc.), create a Linear issue with:

**Title Format:** `[M0X] Task X.Y: Task Name`
- Example: `[M01] Task 1.1: Agent Registry Infrastructure`

**Description Format:**
```markdown
## Overview
[Copy the "Description" section from the task]

## Owner
[Copy the "Agent" field - this becomes the assignee or label]

## Effort
[Copy the "Effort" field - use for time tracking estimate]

## Dependencies
[Copy the "Dependencies" field]
- List any task dependencies
- These should be converted to Linear blocking relationships

## Acceptance Criteria
[Copy all the checkbox items from "Acceptance Criteria"]
- [ ] Criterion 1
- [ ] Criterion 2
...

## Deliverables
[Copy the "Deliverables" list]
- File path 1
- File path 2
...

## Technical Notes
[Include any code examples or technical approach details from the task]

## Related Milestone
Milestone: [MLP | Dogfooding | Beta | Beta Feedback | GA]
Phase: [M01 | M02 | M03 | M04 | M05]
```

**Labels to Add:**
- Milestone label: `M01`, `M02`, `M03`, `M04`, or `M05`
- Phase label: `MLP`, `Dogfooding`, `Beta`, `Beta Feedback`, or `GA`
- Priority from task: `P0` (Critical), `P1` (High), `P2` (Medium)
- Agent label: e.g., `backend-developer`, `ai-engineer`, `platform-engineer`

**Effort Estimate:**
Use the "Effort" hours from the task (e.g., 16 hours, 20 hours)

**Milestone Assignment:**
Assign to the corresponding Linear milestone

**Dependencies (Blocking Relationships):**
- If Task 1.2 depends on Task 1.1, mark the M01-Task-1.2 issue as "blocked by" M01-Task-1.1 issue
- Cross-milestone dependencies:
  - M02 tasks can depend on M01 tasks
  - M03 tasks can depend on M02 tasks
  - M04 tasks can depend on M01, M02, M03
  - M05 tasks can depend on M03

---

## Example Issue Creation

### Example 1: M01 Task 1.1

**Create Linear Issue:**

```
Title: [M01] Task 1.1: Agent Registry Infrastructure

Description:
## Overview
Implement the centralized agent registry system that serves as the source of truth for all agent metadata, capabilities, and discovery operations. This includes designing the metadata schema, implementing storage with PostgreSQL 15+, and creating CRUD operations for registry management.

## Owner
backend-developer

## Effort
16 hours

## Dependencies
None (project start task)

## Acceptance Criteria
- [ ] Agent metadata schema defined with fields for name, capabilities, constraints, dependencies, examples, performance metrics
- [ ] Database tables created with proper indexing on searchable fields (capabilities, tags, domains)
- [ ] CRUD API implemented for registry management (create, read, update, delete agents)
- [ ] Registry populated with metadata for all 130+ existing Mycelium agents
- [ ] Query performance validated <100ms for discovery operations on full registry
- [ ] Migration scripts created for schema updates and backward compatibility
- [ ] Unit tests achieving >90% coverage for registry operations

## Deliverables
- `/plugins/mycelium-core/registry/schema.sql` - Database schema definition
- `/plugins/mycelium-core/registry/registry.py` - Registry implementation
- `/plugins/mycelium-core/registry/migrations/` - Migration scripts
- `/tests/unit/test_registry.py` - Unit test suite
- `/docs/api/registry-api.md` - Registry API documentation

## Technical Notes
Uses PostgreSQL 15+ with pgvector extension for embeddings storage. Schema includes vector columns for semantic search capabilities.

## Related Milestone
Milestone: MLP
Phase: M01

Labels: M01, MLP, P0-Critical, backend-developer
Estimate: 16 hours
Milestone: MLP - Agent Discovery & Coordination
```

### Example 2: M01 Task 1.3 (with Dependency)

**Create Linear Issue:**

```
Title: [M01] Task 1.3: NLP Capability Matching Engine

Description:
## Overview
Implement semantic matching engine that maps natural language task descriptions to agent capabilities using NLP techniques. Evaluate and integrate sentence transformers or similar models for embedding-based similarity matching with confidence scoring.

## Owner
ai-engineer

## Effort
20 hours

## Dependencies
- Task 1.1: Agent Registry Infrastructure (must be completed first for pgvector storage)

## Acceptance Criteria
- [ ] Embedding model selected and integrated (sentence-transformers recommended)
- [ ] Agent capability embeddings pre-computed and cached for all 130+ agents
- [ ] Matching algorithm implemented with cosine similarity or equivalent
- [ ] Confidence scoring system implemented (0.0-1.0 scale)
- [ ] Fallback recommendations provided when no high-confidence matches exist
- [ ] Matching accuracy validated >85% on test dataset of 100+ queries
- [ ] Performance optimized for <200ms matching latency
- [ ] Unit tests covering edge cases (ambiguous queries, no matches, multiple matches)

## Deliverables
- `/plugins/mycelium-core/matching/matcher.py` - Matching engine implementation
- `/plugins/mycelium-core/matching/embeddings/` - Pre-computed embeddings cache
- `/tests/unit/test_matcher.py` - Unit test suite
- `/tests/fixtures/matching_test_queries.json` - Test dataset
- `/docs/technical/matching-algorithm.md` - Algorithm documentation

## Technical Notes
Uses pgvector extension in PostgreSQL for vector similarity search with HNSW indexing. Pre-computes embeddings and stores in database for <50ms query performance.

## Related Milestone
Milestone: MLP
Phase: M01

Labels: M01, MLP, P0-Critical, ai-engineer
Estimate: 20 hours
Milestone: MLP - Agent Discovery & Coordination
Blocked by: [M01] Task 1.1: Agent Registry Infrastructure
```

---

## Complete Task List

### M01: Agent Discovery & Coordination (11 tasks, 135 hours)

1. Task 1.1: Agent Registry Infrastructure (16h) - backend-developer, P0
2. Task 1.2: Discovery API Endpoints (12h) - backend-developer, P0, depends on 1.1
3. Task 1.3: NLP Capability Matching Engine (20h) - ai-engineer, P0, depends on 1.1
4. Task 1.4: Agent Discovery MCP Tool (12h) - python-pro, P1, depends on 1.2, 1.3
5. Task 1.5: Handoff Protocol Implementation (16h) - ai-engineer, P0, depends on 1.1
6. Task 1.6: Workflow Orchestration Engine (20h) - backend-developer, P1, depends on 1.5
7. Task 1.7: Coordination Tracking System (12h) - backend-developer, P2, depends on 1.6
8. Task 1.8: Coordination MCP Tool (12h) - python-pro, P1, depends on 1.6, 1.7
9. Task 1.9: Integration Testing Framework (12h) - qa-expert, P1, depends on 1.4, 1.8
10. Task 1.10: Documentation & Examples (8h) - multi-agent-coordinator, P2, depends on 1.4, 1.8
11. Task 1.11: Telemetry Infrastructure (12h) - backend-developer, P2

### M02: Skill Infrastructure (8 tasks, 120 hours)

1. Task 2.1: Skill Module Format Specification (15h) - backend-developer, P0, depends on M01-1.1
2. Task 2.2: Dynamic Skill Loader Implementation (25h) - backend-developer, P0, depends on 2.1
3. Task 2.3: Skill Repository and Version Control (20h) - platform-engineer, P1, depends on 2.1, 2.2
4. Task 2.4: Dependency Resolution System (20h) - python-pro, P0, depends on 2.3
5. Task 2.5: Initial Skill Library (20+ Skills) (20h) - backend-developer, P1, depends on 2.1, 2.2
6. Task 2.6: Web UI Components (20h) - frontend-developer, P1, depends on 2.2
7. Task 2.7: TUI Implementation (12h) - cli-developer, P2, depends on 2.2
8. Task 2.8: CLI Integration (8h) - cli-developer, P2, depends on 2.2

### M03: Token Optimization (11 tasks, 140 hours)

1. Task 3.1: Compression Engine Architecture (15h) - performance-engineer, P0, depends on M02-2.2
2. Task 3.2: Token Budget Optimizer (20h) - ai-engineer, P0, depends on M01-1.6
3. Task 3.3: Context Diff Generator (15h) - backend-developer, P0, depends on M01-1.5
4. Task 3.4: Lazy Loading Enhancement (15h) - python-pro, P1, depends on M02-2.2
5. Task 3.5: Compression Validation Framework (12h) - qa-expert, P1, depends on 3.1
6. Task 3.6: Budget Optimization Integration (15h) - backend-developer, P1, depends on 3.2, M01-1.6
7. Task 3.7: Context Diff Integration (12h) - python-pro, P1, depends on 3.3, M01-1.8
8. Task 3.8: Compression MCP Tools (10h) - python-pro, P2, depends on 3.1
9. Task 3.9: Performance Optimization (10h) - performance-engineer, P1, depends on 3.1-3.4
10. Task 3.10: Documentation & Examples (6h) - multi-agent-coordinator, P2, depends on 3.1-3.8
11. Task 3.11: Budget UI Components (16h) - frontend-developer, P1, depends on 3.2

### M04: Orchestration Meta-Skill (10 tasks, 100 hours)

1. Task 4.1: Task Decomposition Engine (15h) - ai-engineer, P0, depends on M01-1.3
2. Task 4.2: Intelligent Agent Selector (15h) - multi-agent-coordinator, P0, depends on M01-1.4, 4.1
3. Task 4.3: Workflow DAG Executor (15h) - backend-developer, P0, depends on 4.2, M01-1.6
4. Task 4.4: Failure Recovery System (12h) - workflow-orchestrator, P1, depends on 4.3
5. Task 4.5: Resource Allocation Manager (10h) - backend-developer, P1, depends on 4.3, M03-3.2
6. Task 4.6: Orchestration MCP Tool (8h) - python-pro, P1, depends on 4.1-4.5
7. Task 4.7: Workflow Visualization (Web UI) (12h) - frontend-developer, P0, depends on 4.3
8. Task 4.8: Integration Testing (10h) - qa-expert, P1, depends on 4.6
9. Task 4.9: Performance Optimization (5h) - performance-engineer, P2, depends on 4.8
10. Task 4.10: Documentation (2h) - multi-agent-coordinator, P2, depends on 4.6

### M05: Analytics & Self-Optimization (10 tasks, 100 hours)

1. Task 5.1: Telemetry Infrastructure (15h) - backend-developer, P0, depends on M03-3.1
2. Task 5.2: Analytics Data Store (TimescaleDB) (12h) - data-analyst, P0, depends on 5.1
3. Task 5.3: S7 - Analytics Query Skills (18h) - data-analyst, P1, depends on 5.2
4. Task 5.4: S3 - Compression Pipeline Skill (15h) - performance-engineer, P1, depends on M03-3.1, 5.2
5. Task 5.5: S8 - Self-Optimization Skill (20h) - ai-engineer, P1, depends on 5.3, M03-3.2
6. Task 5.6: Analytics MCP Tools (10h) - python-pro, P2, depends on 5.3
7. Task 5.7: Dashboard Implementation (Web UI) (12h) - frontend-developer, P0, depends on 5.3
8. Task 5.8: Integration Testing (8h) - qa-expert, P1, depends on 5.3-5.7
9. Task 5.9: Performance Tuning (6h) - performance-engineer, P2, depends on 5.8
10. Task 5.10: Documentation (4h) - data-analyst, P2, depends on 5.6

---

## Issue Fields Mapping

### Title
Format: `[M0X] Task X.Y: Task Name`

### Description
Copy from milestone document with this structure:
```markdown
## Overview
[Task description]

## Owner
[Agent name]

## Effort
[X hours]

## Dependencies
[List of dependency tasks]

## Acceptance Criteria
[All checkbox items]

## Deliverables
[All file paths and deliverables]

## Technical Notes
[Any code examples or implementation details]
```

### Priority
- P0 → High priority in Linear
- P1 → Medium priority in Linear
- P2 → Low priority in Linear

### Estimate
Use the effort hours (e.g., 16 hours = 2 points if using 8-hour point system, or just use hours)

### Labels
Add these labels to each issue:
- Milestone: `M01`, `M02`, `M03`, `M04`, or `M05`
- Phase: `MLP`, `Dogfooding`, `Beta`, `Beta Feedback`, or `GA`
- Priority: `P0`, `P1`, or `P2`
- Agent: `backend-developer`, `ai-engineer`, `frontend-developer`, etc.
- Technology tags: `postgresql`, `pgvector`, `react`, `tanstack`, `telemetry`, etc.

### Assignee
Map the "Agent" field to actual team members or leave as label for later assignment

### Milestone
Assign to the appropriate Linear milestone (MLP, Dogfooding, Beta, Beta Feedback, GA)

### Project
Assign to "Claude Code Skills" or "mycelium" project

---

## Dependency Mapping

### How to Create Blocking Relationships

When creating issues, note the dependencies and create Linear blocking relationships:

**Example:**
- Task 1.2 says "Dependencies: Task 1.1"
- After creating both issues, mark [M01] Task 1.2 as "blocked by" [M01] Task 1.1

**Cross-Milestone Dependencies:**
- M02 Task 2.1 depends on M01 Task 1.1
  - Mark [M02] Task 2.1 as "blocked by" [M01] Task 1.1
- M03 Task 3.2 depends on M01 Task 1.6
  - Mark [M03] Task 3.2 as "blocked by" [M01] Task 1.6

**Priority Order for Dependencies:**
1. Create all M01 issues first
2. Create all M02 issues and link M01 dependencies
3. Create all M03 issues and link M01/M02 dependencies
4. Create all M04 issues and link M01/M02/M03 dependencies
5. Create all M05 issues and link M03 dependencies

---

## Automation Tips

### Bulk Creation Script

If Linear MCP supports batch operations, create issues in batches:

```typescript
// Pseudo-code for batch creation
const m01Tasks = [
  { title: '[M01] Task 1.1: Agent Registry Infrastructure', ... },
  { title: '[M01] Task 1.2: Discovery API Endpoints', ... },
  // ... all 11 M01 tasks
];

const m01Issues = await linear.createIssues(m01Tasks);

// Then create dependencies
await linear.createBlockingRelationship(
  m01Issues[1], // Task 1.2
  m01Issues[0]  // Task 1.1 (blocker)
);
```

### Validation Checklist

After creating all issues, verify:
- [ ] Total issue count matches: 50+ issues created
- [ ] All blocking relationships created
- [ ] All milestones assigned correctly
- [ ] All labels applied
- [ ] All effort estimates entered
- [ ] No orphaned tasks (all have proper milestone)
- [ ] Critical path visible (M01-1.1 → ... → M05-5.10)

---

## Quick Reference Tables

### M01 Task Summary

| Task | Title | Hours | Agent | Priority | Depends On |
|------|-------|-------|-------|----------|------------|
| 1.1 | Agent Registry Infrastructure | 16 | backend-developer | P0 | None |
| 1.2 | Discovery API Endpoints | 12 | backend-developer | P0 | 1.1 |
| 1.3 | NLP Capability Matching Engine | 20 | ai-engineer | P0 | 1.1 |
| 1.4 | Agent Discovery MCP Tool | 12 | python-pro | P1 | 1.2, 1.3 |
| 1.5 | Handoff Protocol Implementation | 16 | ai-engineer | P0 | 1.1 |
| 1.6 | Workflow Orchestration Engine | 20 | backend-developer | P1 | 1.5 |
| 1.7 | Coordination Tracking System | 12 | backend-developer | P2 | 1.6 |
| 1.8 | Coordination MCP Tool | 12 | python-pro | P1 | 1.6, 1.7 |
| 1.9 | Integration Testing Framework | 12 | qa-expert | P1 | 1.4, 1.8 |
| 1.10 | Documentation & Examples | 8 | multi-agent-coordinator | P2 | 1.4, 1.8 |
| 1.11 | Telemetry Infrastructure | 12 | backend-developer | P2 | None |

### M02 Task Summary

| Task | Title | Hours | Agent | Priority | Depends On |
|------|-------|-------|-------|----------|------------|
| 2.1 | Skill Module Format Specification | 15 | backend-developer | P0 | M01-1.1 |
| 2.2 | Dynamic Skill Loader Implementation | 25 | backend-developer | P0 | 2.1 |
| 2.3 | Skill Repository and Version Control | 20 | platform-engineer | P1 | 2.1, 2.2 |
| 2.4 | Dependency Resolution System | 20 | python-pro | P0 | 2.3 |
| 2.5 | Initial Skill Library (20+ Skills) | 20 | backend-developer | P1 | 2.1, 2.2 |
| 2.6 | Web UI Components (Storybook) | 20 | frontend-developer | P1 | 2.2 |
| 2.7 | TUI Implementation (Textual) | 12 | cli-developer | P2 | 2.2 |
| 2.8 | CLI Integration | 8 | cli-developer | P2 | 2.2 |

### M03 Task Summary

| Task | Title | Hours | Agent | Priority | Depends On |
|------|-------|-------|-------|----------|------------|
| 3.1 | Compression Engine Architecture | 15 | performance-engineer | P0 | M02-2.2 |
| 3.2 | Token Budget Optimizer | 20 | ai-engineer | P0 | M01-1.6 |
| 3.3 | Context Diff Generator | 15 | backend-developer | P0 | M01-1.5 |
| 3.4 | Lazy Loading Enhancement | 15 | python-pro | P1 | M02-2.2 |
| 3.5 | Compression Validation Framework | 12 | qa-expert | P1 | 3.1 |
| 3.6 | Budget Optimization Integration | 15 | backend-developer | P1 | 3.2, M01-1.6 |
| 3.7 | Context Diff Integration | 12 | python-pro | P1 | 3.3, M01-1.8 |
| 3.8 | Compression MCP Tools | 10 | python-pro | P2 | 3.1 |
| 3.9 | Performance Optimization | 10 | performance-engineer | P1 | 3.1-3.4 |
| 3.10 | Documentation & Examples | 6 | multi-agent-coordinator | P2 | 3.1-3.8 |
| 3.11 | Budget UI Components | 16 | frontend-developer | P1 | 3.2 |

### M04 Task Summary

| Task | Title | Hours | Agent | Priority | Depends On |
|------|-------|-------|-------|----------|------------|
| 4.1 | Task Decomposition Engine | 15 | ai-engineer | P0 | M01-1.3 |
| 4.2 | Intelligent Agent Selector | 15 | multi-agent-coordinator | P0 | M01-1.4, 4.1 |
| 4.3 | Workflow DAG Executor | 15 | backend-developer | P0 | 4.2, M01-1.6 |
| 4.4 | Failure Recovery System | 12 | workflow-orchestrator | P1 | 4.3 |
| 4.5 | Resource Allocation Manager | 10 | backend-developer | P1 | 4.3, M03-3.2 |
| 4.6 | Orchestration MCP Tool | 8 | python-pro | P1 | 4.1-4.5 |
| 4.7 | Workflow Visualization (Web UI) | 12 | frontend-developer | P0 | 4.3, M02-2.6 |
| 4.8 | Integration Testing | 10 | qa-expert | P1 | 4.6 |
| 4.9 | Performance Optimization | 5 | performance-engineer | P2 | 4.8 |
| 4.10 | Documentation | 2 | multi-agent-coordinator | P2 | 4.6 |

### M05 Task Summary

| Task | Title | Hours | Agent | Priority | Depends On |
|------|-------|-------|-------|----------|------------|
| 5.1 | Telemetry Infrastructure | 15 | backend-developer | P0 | M03-3.1 |
| 5.2 | Analytics Data Store (TimescaleDB) | 12 | data-analyst | P0 | 5.1 |
| 5.3 | S7 - Analytics Query Skills | 18 | data-analyst | P1 | 5.2 |
| 5.4 | S3 - Compression Pipeline Skill | 15 | performance-engineer | P1 | M03-3.1, 5.2 |
| 5.5 | S8 - Self-Optimization Skill | 20 | ai-engineer | P1 | 5.3, M03-3.2 |
| 5.6 | Analytics MCP Tools | 10 | python-pro | P2 | 5.3 |
| 5.7 | Dashboard Implementation (Web UI) | 12 | frontend-developer | P0 | 5.3, M02-2.6, M04-4.7 |
| 5.8 | Integration Testing | 8 | qa-expert | P1 | 5.3-5.7 |
| 5.9 | Performance Tuning | 6 | performance-engineer | P2 | 5.8 |
| 5.10 | Documentation | 4 | data-analyst | P2 | 5.6 |

---

## Special Notes for Linear Import

### Epic Structure (Optional)

Consider creating epics for major features:
- Epic 1: "Agent Discovery System" (M01 Tasks 1.1-1.4)
- Epic 2: "Coordination Infrastructure" (M01 Tasks 1.5-1.8, 1.11)
- Epic 3: "Skill Loading Framework" (M02 Tasks 2.1-2.5)
- Epic 4: "UI Component Library" (M02 Tasks 2.6-2.8, shared across M03-M05)
- Epic 5: "Token Budget System" (M03 Tasks 3.1-3.3, 3.6-3.8, 3.11)
- Epic 6: "Workflow Orchestration" (M04 all tasks)
- Epic 7: "Analytics & Telemetry" (M05 all tasks)

### Views to Create

**Critical Path View:**
- Filter: Priority = P0
- Sort: By dependencies (blockers first)
- Purpose: Focus on must-have tasks

**By Agent View:**
- Group by: Agent label
- Purpose: Workload distribution

**Timeline View:**
- Sort by: Milestone → Dependencies
- Purpose: Gantt chart visualization

**UI Components View:**
- Filter: Labels contain "frontend" or "ui"
- Purpose: Track UI development progress

---

## Import Process

### Step-by-Step

1. **Create Project** (if doesn't exist):
   - Name: "Claude Code Skills" or add to existing "mycelium" project
   - Description: Copy from README.md

2. **Create Milestones**:
   - Create 5 milestones (MLP, Dogfooding, Beta, Beta Feedback, GA)
   - Set target dates if known

3. **Create Labels**:
   - Milestone labels: M01, M02, M03, M04, M05
   - Phase labels: MLP, Dogfooding, Beta, Beta Feedback, GA
   - Priority labels: P0, P1, P2
   - Agent labels: backend-developer, ai-engineer, frontend-developer, etc.
   - Tech labels: postgresql, pgvector, timescaledb, react, tanstack, etc.

4. **Create M01 Issues** (11 tasks):
   - Use M01 task summary table above
   - Copy description format from milestone file
   - Apply labels and estimates

5. **Create M02 Issues** (8 tasks):
   - Link dependencies to M01 issues as needed
   - Apply labels and estimates

6. **Create M03 Issues** (11 tasks):
   - Link dependencies to M01/M02 issues
   - Apply labels and estimates

7. **Create M04 Issues** (10 tasks):
   - Link dependencies to M01/M02/M03 issues
   - Apply labels and estimates

8. **Create M05 Issues** (10 tasks):
   - Link dependencies to M03 issues
   - Apply labels and estimates

9. **Verify Dependencies**:
   - Check critical path is visible
   - Ensure no circular dependencies
   - Validate all cross-milestone links

10. **Create Views**:
    - Critical Path view
    - By Agent view
    - Timeline view
    - Current Sprint view

---

## Verification Checklist

After import, verify in Linear:

**Project Structure:**
- [ ] Project created with correct name
- [ ] 5 milestones exist with target dates
- [ ] All labels created and ready to use

**Issue Count:**
- [ ] M01: 11 issues
- [ ] M02: 8 issues
- [ ] M03: 11 issues
- [ ] M04: 10 issues
- [ ] M05: 10 issues
- [ ] Total: 50 issues

**Dependencies:**
- [ ] All task dependencies converted to blocking relationships
- [ ] Critical path visible (no orphaned tasks)
- [ ] Cross-milestone dependencies linked
- [ ] No circular dependencies

**Metadata:**
- [ ] All issues have estimates
- [ ] All issues have priority
- [ ] All issues have labels
- [ ] All issues assigned to milestones
- [ ] Acceptance criteria as checklists

**Views:**
- [ ] Can filter by milestone (M01-M05)
- [ ] Can filter by priority (P0, P1, P2)
- [ ] Can group by agent
- [ ] Timeline shows proper sequence

---

## Key Technology Tags to Add

Use these technology tags for filtering and tracking:

**Infrastructure:**
- `postgresql` - Database work
- `pgvector` - Vector similarity search
- `timescaledb` - Time-series analytics
- `redis` - Caching layer

**Frontend:**
- `react` - React components
- `tanstack` - TanStack ecosystem
- `radix-ui` - Design primitives
- `tailwind` - Styling
- `storybook` - Component development

**Backend:**
- `python` - Python backend work
- `typescript` - TypeScript backend
- `api` - REST API development
- `mcp` - MCP tool integration

**Features:**
- `agent-discovery` - Discovery features
- `orchestration` - Workflow features
- `token-optimization` - Budget/compression
- `analytics` - Analytics features
- `telemetry` - Telemetry system
- `ui-components` - UI work
- `tui` - Terminal UI
- `cli` - Command-line tools

**Quality:**
- `testing` - Test tasks
- `documentation` - Docs tasks
- `performance` - Performance work
- `security` - Security reviews

---

## Demo Scenario References

Each milestone has a demo scenario. Reference these for validation criteria:

- **M01 Demo:** Multi-Agent Code Review Workflow (15 min)
  - Located in M01_AGENT_DISCOVERY_SKILLS.md, "Demo Scenario" section

- **M02 Demo:** Live Skill Development Cycle (15 min)
  - Located in M02_SKILL_INFRASTRUCTURE.md, "Demo Scenario" section

- **M03 Demo:** Multi-Turn Conversation with Dynamic Optimization (12 min)
  - Located in M03_TOKEN_OPTIMIZATION.md, "Demo Scenario" section

- **M04 Demo:** Autonomous Multi-Agent Code Review (10 min)
  - Located in M04_ORCHESTRATION.md, "Demo Scenario" section

- **M05 Demo:** Data-Driven System Optimization (12 min)
  - Located in M05_ANALYTICS_COMPRESSION.md, "Demo Scenario" section

---

## Additional Context Files

If you need more context while creating issues:

**Technical Details:**
- `/home/gerald/git/mycelium/docs/TECHNICAL_ARCHITECTURE_SKILLS.md` (79KB)
- `/home/gerald/git/mycelium/docs/SKILLS_TECHNICAL_ROADMAP.md` (23KB)
- `/home/gerald/git/mycelium/docs/SKILLS_IMPLEMENTATION_QUICKSTART.md` (32KB)

**Analysis:**
- `/home/gerald/git/mycelium/docs/CLAUDE_CODE_SKILLS_SYNTHESIS.md` (75KB)
- `/home/gerald/git/mycelium/docs/SKILLS_EXECUTIVE_SUMMARY.md` (9.5KB)

---

## Final Notes

### Important Reminders

1. **Dependencies are Critical**: Proper blocking relationships ensure correct task sequencing
2. **Effort Estimates**: Use for capacity planning (596 hours ÷ team size = weeks needed)
3. **Labels Enable Filtering**: Comprehensive labels make project management easier
4. **Acceptance Criteria**: These become sub-tasks/checklists in Linear
5. **Demo Scenarios**: Use for sprint review planning

### Success Criteria

You'll know the import was successful when:
- All 50+ issues created
- Dependencies visualize critical path
- Can filter by milestone and see logical progression
- Effort totals match (M01: 135h, M02: 120h, M03: 140h, M04: 100h, M05: 100h)
- Each issue has complete description with acceptance criteria

---

## Questions?

If anything is unclear during import:
- Refer to milestone documents for complete task details
- Check FEEDBACK_INCORPORATION_PLAN.md for technology decisions
- Review PROJECT_SUMMARY.md for high-level context

---

**Ready to import!** This document contains everything needed to create a complete Linear project from the Claude Code Skills plan.
