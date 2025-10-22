# Claude Code Skills - Feedback Incorporation Plan

**Version:** 1.0
**Date:** 2025-10-20
**Lead:** Technical Lead (claude-code-developer)
**Purpose:** Systematic incorporation of Gerald's technical feedback across all project documentation

---

## Executive Summary

This document provides a comprehensive plan for incorporating Gerald's architectural and technical feedback into the Claude Code Skills project documentation. The feedback fundamentally shifts several technical decisions while maintaining the project's core objectives and timeline.

**Key Changes:**
- Database: PostgreSQL only (no SQLite)
- Embeddings: pgvector for caching
- Time-series: TimescaleDB for analytics
- Token budgets: Alert/warn, don't limit (configurable)
- Telemetry: Opt-in centralized (default OFF, endpoint configurable)
- Web UI: TanStack + design system + Storybook
- CLI: Text commands + Textual TUI
- Skill repository: Filesystem-based

**Impact:** These changes increase architectural complexity moderately but provide production-grade scalability, better developer experience, and align with Gerald's operational requirements.

---

## Documents Requiring Updates

### Core Documents (9 total)
1. `/home/gerald/git/mycelium/docs/projects/claude-code-skills/architecture.md`
2. `/home/gerald/git/mycelium/docs/projects/claude-code-skills/README.md`
3. `/home/gerald/git/mycelium/docs/projects/claude-code-skills/success-metrics.md`
4. `/home/gerald/git/mycelium/docs/TECHNICAL_ARCHITECTURE_SKILLS.md`
5. `/home/gerald/git/mycelium/docs/SKILLS_TECHNICAL_ROADMAP.md`
6. `/home/gerald/git/mycelium/docs/SKILLS_IMPLEMENTATION_QUICKSTART.md`
7. `/home/gerald/git/mycelium/docs/projects/claude-code-skills/milestones/M01_AGENT_DISCOVERY_SKILLS.md`
8. `/home/gerald/git/mycelium/docs/projects/claude-code-skills/milestones/M02_SKILL_INFRASTRUCTURE.md`
9. `/home/gerald/git/mycelium/docs/projects/claude-code-skills/milestones/M03_TOKEN_OPTIMIZATION.md`

---

## Detailed Change Specifications

### 1. Architecture Document (`architecture.md`)

**File:** `/home/gerald/git/mycelium/docs/projects/claude-code-skills/architecture.md`

#### Section 2.1: Data Architecture - Data Stores

**Current:**
```markdown
**Agent Registry** (M01)
- Technology: PostgreSQL or SQLite
- Schema: agents, capabilities, metadata, mappings
```

**Change To:**
```markdown
**Agent Registry** (M01)
- Technology: PostgreSQL 15+ (production requirement)
- Schema: agents, capabilities, metadata, mappings
- Extensions: pgvector for embeddings cache
- Rationale: Production scalability, pgvector for semantic search, no SQLite option
```

**New Addition After Agent Registry:**
```markdown
**Embeddings Cache** (M01)
- Technology: pgvector extension in PostgreSQL
- Storage: Agent capability embeddings (384-dim vectors)
- Indexing: HNSW for approximate nearest neighbor search
- Performance: <10ms similarity search across 500+ agents
- Size: ~50KB per agent embedding
```

#### Section 2.1: Data Architecture - Analytics Store

**Current:**
```markdown
**Analytics Store** (M05)
- Technology: TimescaleDB or partitioned SQLite
```

**Change To:**
```markdown
**Analytics Store** (M05)
- Technology: TimescaleDB (hypertables on PostgreSQL)
- Rationale: Time-series optimization, continuous aggregates, compression
- No SQLite option: Production analytics require TimescaleDB performance
```

#### Section 3.1: Integration Points - External Integrations

**Add New Subsection:**
```markdown
### Web UI Integration

**Technology Stack:**
- Frontend Framework: TanStack (React Query + Router + Table + Virtual)
- Design System: Custom component library with Storybook
- State Management: TanStack Query for server state
- Styling: Tailwind CSS + design tokens
- Development: Storybook for component development

**Components:**
- Skills Dashboard (browse, install, configure skills)
- Analytics Visualization (token usage, performance metrics)
- Workflow Builder (visual orchestration design)
- Agent Directory (search, filter, inspect agents)

**Integration:**
- REST API endpoints for all data access
- WebSocket for real-time updates
- Authentication via existing Mycelium auth
```

#### Section 3.1: Integration Points - CLI Integration

**Add New Subsection:**
```markdown
### CLI Integration

**Dual Interface Approach:**

**1. Text Commands:**
- Traditional CLI commands for scripting and automation
- Example: `mycelium skill install agent-discovery`
- Use case: CI/CD pipelines, shell scripts

**2. Textual TUI:**
- Interactive terminal UI using Textual framework
- Rich formatting, live updates, interactive widgets
- Example: `mycelium tui` launches dashboard
- Use case: Interactive exploration, development workflow

**Implementation:**
```python
# Text command example
@click.command()
@click.argument('skill_name')
def install(skill_name: str):
    """Install a skill from the repository."""
    loader = SkillLoader()
    loader.install(skill_name)
```

```python
# Textual TUI example
from textual.app import App
from textual.widgets import Header, Footer, DataTable

class MyceliumTUI(App):
    """Interactive TUI for Mycelium Skills."""
    def compose(self):
        yield Header()
        yield DataTable()  # Skills list
        yield Footer()
```

#### Section 4: Performance Architecture - New Subsection

**Add After Performance Budgets:**
```markdown
### Token Budget Policy

**Approach:** Alert/Warn, Don't Limit (Configurable)

**Default Behavior:**
- Budget calculations provide warnings, not hard limits
- Users informed of potential cost implications
- Suggestions for optimization provided
- No automatic truncation or rejection

**Configuration:**
```json
{
  "token_budget": {
    "mode": "warn",  // "warn" | "limit" | "off"
    "warn_threshold": 0.8,  // Warn at 80% of calculated budget
    "hard_limit_enabled": false,  // User can enable strict limits
    "per_agent_budgets": {
      "default": "warn",
      "overrides": {
        "security-expert": "limit"  // Per-agent policy
      }
    }
  }
}
```

**Use Cases:**
- **Warn mode (default):** Development and exploration
- **Limit mode (opt-in):** Production cost control
- **Off mode:** No budget tracking

**Implementation:**
- Budget calculator runs as advisory service
- Warnings displayed in UI/CLI
- Analytics track actual vs predicted consumption
- Self-optimization in M05 improves predictions
```

#### Section 5: Security Architecture - Add Telemetry Privacy

**Add New Subsection After Privacy Architecture:**
```markdown
### Telemetry Privacy

**Opt-In Centralized Telemetry:**

**Default Configuration:**
```json
{
  "telemetry": {
    "enabled": false,  // Default: OFF
    "endpoint": null,  // No default endpoint
    "anonymous_id": null,  // Generated on opt-in
    "data_collection": {
      "usage_metrics": false,
      "performance_metrics": false,
      "error_reports": false
    }
  }
}
```

**Opt-In Process:**
```bash
# User explicitly enables telemetry
mycelium config telemetry enable --endpoint=https://telemetry.mycelium.local

# Configure endpoint (required)
mycelium config telemetry endpoint https://custom.telemetry.server

# Selective data collection
mycelium config telemetry enable-usage-metrics
mycelium config telemetry enable-performance-metrics
```

**Privacy Guarantees:**
- No data sent without explicit opt-in
- Configurable endpoint (private deployment supported)
- Data minimization: only specified metrics collected
- Anonymization: hashed IDs, no PII
- Local-only mode always available
- User can revoke consent at any time

**Transparency:**
- Telemetry dashboard shows what data is being sent
- Export capability for audit
- Open-source telemetry SDK
```

---

### 2. Project README (`README.md`)

**File:** `/home/gerald/git/mycelium/docs/projects/claude-code-skills/README.md`

#### Section: Overview - Add Technical Stack Summary

**Add After "Key Outcomes":**
```markdown
### Technical Architecture Highlights

**Database Layer:**
- PostgreSQL 15+ for all persistent data
- pgvector extension for embeddings cache
- TimescaleDB for time-series analytics

**Skills Repository:**
- Filesystem-based with Git integration
- No centralized database for skill storage
- Fast local access, version control friendly

**User Interfaces:**
- **Web UI:** TanStack ecosystem (React Query, Router, Table, Virtual)
- **CLI:** Dual mode - text commands for automation, Textual TUI for interaction
- **Design System:** Storybook component library

**Operational Policies:**
- Token budgets: Alert/warn by default, optional limits
- Telemetry: Opt-in only, configurable endpoint
- Privacy-first: Local-only mode always available
```

#### Section: Milestones & Deliverables - Update M02

**Current M02 Description:** (mentions multiple storage options)

**Change To:**
```markdown
### M02: Skill Infrastructure
**Phase:** Dogfooding
**Timeline:** Weeks 5-10
**Effort:** 120 hours (+20h for UI foundation)

**Deliverables:**
- Dynamic skill loading from filesystem
- PostgreSQL-based skill metadata registry with pgvector
- Hot-reload capability without restarts
- Filesystem skill repository (Git-friendly)
- Version control and dependency management
- 20+ initial reusable skills across categories
- **NEW:** Web UI foundation (TanStack setup, design system)
- **NEW:** CLI foundation (text commands + Textual TUI)

**Phase Gates:**
- <200ms skill loading overhead
- Zero memory leaks over 24h operation
- 100% backward compatibility maintained
- **NEW:** Web UI prototype functional
- **NEW:** TUI demonstrates interactive workflows
```

---

### 3. Success Metrics (`success-metrics.md`)

**File:** `/home/gerald/git/mycelium/docs/projects/claude-code-skills/success-metrics.md`

#### Section 1.2: Add Token Budget Effectiveness Metrics

**Add New Subsection:**
```markdown
### 1.4 Token Budget Effectiveness

**M03 Specific**

| Metric | Target | Measurement |
|--------|--------|-------------|
| Budget Prediction Accuracy | >85% | Actual within 15% of predicted |
| Warning Usefulness | >80% satisfaction | User survey: warnings helped optimize |
| False Positive Rate | <20% | Warnings that were unnecessary |
| Cost Optimization Impact | 20-30% reduction | Users who acted on warnings |
| Hard Limit Adoption | Track only | Percentage of users enabling limits |

**Default Policy Impact:**
- Measure user behavior with warn-only mode
- Track conversion rate to limit mode
- Analyze warning dismissal patterns
- Correlate warnings with actual cost reduction
```

#### Section 2: Performance Metrics - Add UI/TUI Targets

**Add New Table:**
```markdown
### 2.4 User Interface Performance

| Operation | Target (P50) | Target (P95) | Measurement |
|-----------|--------------|--------------|-------------|
| Web UI Initial Load | <1s | <2s | Time to interactive |
| Web UI Page Transition | <200ms | <500ms | React Router navigation |
| Web UI Data Refresh | <500ms | <1s | TanStack Query refetch |
| TUI Startup | <500ms | <1s | Textual app initialization |
| TUI Screen Refresh | <50ms | <100ms | Widget re-render |
| CLI Command | <100ms | <200ms | Command execution (simple) |
```

#### Section 5: System Health Metrics - Add Database Metrics

**Add New Subsection:**
```markdown
### 5.4 Database Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| Agent Registry Query | <10ms P95 | PostgreSQL query time |
| Embeddings Search (pgvector) | <20ms P95 | Similarity search across 500+ agents |
| Analytics Query (TimescaleDB) | <100ms P95 | Continuous aggregate queries |
| Database Connection Pool | >90% utilization | Connection efficiency |
| Index Hit Rate | >98% | Cache effectiveness |
```

#### Section 6: Business Impact - Update Technology Costs

**Update Cost Savings Table:**
```markdown
### 6.1 Cost Savings (Updated for PostgreSQL + UI Investment)

| Component | Annual Cost | Annual Savings | Net Impact |
|-----------|-------------|----------------|------------|
| Token consumption (40% reduction) | - | +$18,720 | Positive |
| Developer productivity (2h/week) | - | +$103,920 | Positive |
| PostgreSQL hosting (managed) | -$1,200 | - | Negative |
| TimescaleDB hosting (managed) | -$1,800 | - | Negative |
| pgvector (included in PG) | $0 | - | Neutral |
| UI hosting (static) | -$200 | - | Negative |
| Infrastructure savings | - | +$3,000 | Positive |
| **Net Annual Impact** | **-$3,200** | **+$125,640** | **+$122,440** |

**ROI Updated:**
- Total investment: $100-130K (includes UI development)
- Annual savings: $122,440
- Payback period: 9-12 months
```

---

### 4. Technical Architecture Skills (`TECHNICAL_ARCHITECTURE_SKILLS.md`)

**File:** `/home/gerald/git/mycelium/docs/TECHNICAL_ARCHITECTURE_SKILLS.md`

#### Section 2.1: Skill Definition Schema - Update Registry Location

**Current:**
```json
"Location:** `plugins/mycelium-core/skills/registry.json`
```

**Change To:**
```markdown
**Location Options:**
- **Metadata Index:** `plugins/mycelium-core/skills/registry.json` (lightweight index)
- **Database:** PostgreSQL `skills` table (primary source of truth)
- **Embeddings:** pgvector in PostgreSQL (semantic search)

**Database Schema:**
```sql
-- Skills metadata table
CREATE TABLE skills (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    author VARCHAR(255),
    tier INTEGER,
    consensus INTEGER,
    capabilities JSONB,
    execution JSONB,
    performance JSONB,
    dependencies JSONB,
    telemetry JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Embeddings for capability search
CREATE TABLE skill_embeddings (
    skill_id VARCHAR(255) REFERENCES skills(id),
    embedding vector(384),  -- pgvector type
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create HNSW index for fast similarity search
CREATE INDEX ON skill_embeddings USING hnsw (embedding vector_cosine_ops);
```
```

#### Section 2.3: Skill Interface Contract - Add Token Budget Hooks

**Add After BaseSkill Class:**
```python
class BudgetAwareSkill(BaseSkill):
    """Extended base class for budget-aware skills."""

    def estimate_tokens(self, params: Dict[str, Any]) -> int:
        """Estimate token consumption for this execution.

        Used by budget allocator to provide warnings.

        Args:
            params: Skill execution parameters

        Returns:
            Estimated token count
        """
        return 1000  # Override with actual estimation

    def on_budget_warning(self, estimated: int, allocated: int):
        """Callback when budget warning is triggered.

        Default behavior: log warning and continue.
        Override to customize behavior.

        Args:
            estimated: Estimated token consumption
            allocated: Allocated budget (if limits enabled)
        """
        logger.warning(
            f"Budget warning: estimated {estimated} tokens, "
            f"allocated {allocated} tokens"
        )

    def on_budget_exceeded(self, estimated: int, allocated: int) -> bool:
        """Callback when hard budget limit exceeded.

        Only called if hard limits are enabled.

        Args:
            estimated: Estimated token consumption
            allocated: Allocated budget

        Returns:
            True to proceed anyway, False to abort
        """
        return False  # Default: respect hard limits
```

#### Section 7: Integration with Existing Systems - Add UI Integration

**Add New Subsection 7.4:**
```markdown
## 7.4 Web UI Integration

**File:** `plugins/mycelium-core/ui/`

### TanStack Setup

```typescript
// App setup with TanStack ecosystem
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createRouter, RouterProvider } from '@tanstack/react-router'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000, // 1 minute
      cacheTime: 5 * 60 * 1000, // 5 minutes
    },
  },
})

const router = createRouter({
  routes: [
    { path: '/', component: Dashboard },
    { path: '/skills', component: SkillsBrowser },
    { path: '/skills/:id', component: SkillDetail },
    { path: '/analytics', component: Analytics },
    { path: '/workflows', component: WorkflowBuilder },
  ],
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
      <ReactQueryDevtools />
    </QueryClientProvider>
  )
}
```

### Design System Integration

**File:** `plugins/mycelium-core/ui/design-system/`

```typescript
// Storybook configuration
// .storybook/main.ts
export default {
  stories: ['../design-system/**/*.stories.tsx'],
  addons: [
    '@storybook/addon-links',
    '@storybook/addon-essentials',
    '@storybook/addon-a11y',
  ],
  framework: '@storybook/react-vite',
}

// Component example with Storybook
// design-system/Button/Button.stories.tsx
export default {
  title: 'Components/Button',
  component: Button,
}

export const Primary = () => <Button variant="primary">Click me</Button>
export const Secondary = () => <Button variant="secondary">Cancel</Button>
```

### Skills Dashboard Component

```typescript
import { useQuery } from '@tanstack/react-query'
import { DataTable } from '@tanstack/react-table'

function SkillsDashboard() {
  const { data: skills, isLoading } = useQuery({
    queryKey: ['skills'],
    queryFn: () => fetch('/api/v1/skills').then(r => r.json())
  })

  if (isLoading) return <Skeleton />

  return (
    <div>
      <h1>Skills</h1>
      <DataTable
        data={skills}
        columns={[
          { accessorKey: 'name', header: 'Name' },
          { accessorKey: 'version', header: 'Version' },
          { accessorKey: 'tier', header: 'Tier' },
          { accessorKey: 'consensus', header: 'Consensus' },
        ]}
      />
    </div>
  )
}
```
```

---

### 5. Technical Roadmap (`SKILLS_TECHNICAL_ROADMAP.md`)

**File:** `/home/gerald/git/mycelium/docs/SKILLS_TECHNICAL_ROADMAP.md`

#### Week 1: Infrastructure - Update Task List

**Current:**
```markdown
├── Day 1-2: Skills infrastructure (16 dev-hours)
    ├── Create `skills/` directory structure
    ├── Implement `BaseSkill` interface (Python)
```

**Change To:**
```markdown
├── Day 1-2: Skills infrastructure (20 dev-hours, +4h for database)
    ├── Create `skills/` directory structure
    ├── Set up PostgreSQL database with pgvector extension
    ├── Create skills table schema and indexes
    ├── Implement `BaseSkill` interface (Python)
    ├── Set up database connection pooling
    ├── Configure TimescaleDB for analytics (future use)
```

#### Week 1: Day 3-4 - Add Embeddings Generation

**Add to S1 Tasks:**
```markdown
├── Day 3-4: S1 - Agent Discovery Skill (20 dev-hours, +4h for pgvector)
    ├── Extract TF-IDF logic from `scripts/agent_discovery.py`
    ├── **NEW:** Generate embeddings for all agents using sentence-transformers
    ├── **NEW:** Store embeddings in pgvector table
    ├── **NEW:** Implement HNSW similarity search
    ├── Implement `AgentVectorizer` class
    ├── Implement LRU cache for results
    ├── Create `search_agents()` convenience function
    ├── Add telemetry integration (Phase 2 analytics)
    ├── Write comprehensive tests (95% coverage)
    ├── Benchmark against <10ms target (pgvector search)
```

#### Week 2-3: Add UI Foundation Tasks

**Add New Week 2.5 Section:**
```markdown
### Week 2.5: UI Foundation (NEW - 24 dev-hours)

#### Days 1-2: Web UI Setup (16 dev-hours)
- [ ] Initialize React project with Vite
- [ ] Set up TanStack Query for data fetching
- [ ] Set up TanStack Router for navigation
- [ ] Configure Tailwind CSS and design tokens
- [ ] Create base layout components
- [ ] Set up Storybook for component development
- [ ] Create design system foundations (Button, Input, Card, etc.)
- [ ] Build Skills Dashboard prototype

#### Day 3: CLI Enhancement (8 dev-hours)
- [ ] Set up Textual framework
- [ ] Create main TUI application structure
- [ ] Implement skills browser widget
- [ ] Implement analytics dashboard widget
- [ ] Add keyboard navigation
- [ ] Style with rich text formatting
- [ ] Test TUI on macOS, Linux, Windows
```

#### Success Metrics Section - Add UI Metrics

**Add After Performance Metrics:**
```markdown
**User Interface Performance:**
- Web UI initial load <1s (p95)
- TUI startup <500ms
- Interactive responsiveness <100ms
- Storybook component coverage >90%
```

---

### 6. Implementation Quickstart (`SKILLS_IMPLEMENTATION_QUICKSTART.md`)

**File:** `/home/gerald/git/mycelium/docs/SKILLS_IMPLEMENTATION_QUICKSTART.md`

#### Development Environment Setup - Update Prerequisites

**Current:**
```bash
# 2. Install Python dependencies
pip install -r requirements.txt
pip install scikit-learn>=1.0.0 pytest pytest-asyncio pytest-benchmark
```

**Change To:**
```bash
# 2. Install Python dependencies
pip install -r requirements.txt
pip install scikit-learn>=1.0.0 pytest pytest-asyncio pytest-benchmark
pip install psycopg2-binary>=2.9.0  # PostgreSQL adapter
pip install pgvector>=0.2.0  # pgvector Python client
pip install sentence-transformers>=2.2.0  # For embeddings

# 3. Set up PostgreSQL with pgvector
# macOS
brew install postgresql@15
brew services start postgresql@15
psql postgres -c "CREATE DATABASE mycelium_skills;"
psql mycelium_skills -c "CREATE EXTENSION vector;"

# Linux (Ubuntu/Debian)
sudo apt install postgresql-15 postgresql-15-pgvector
sudo systemctl start postgresql
sudo -u postgres psql -c "CREATE DATABASE mycelium_skills;"
sudo -u postgres psql mycelium_skills -c "CREATE EXTENSION vector;"

# Verify pgvector installation
psql mycelium_skills -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

#### Day 1: Skills Infrastructure - Add Database Setup

**Add After Step 3:**
```markdown
### Step 3.5: Initialize Database Schema (30 minutes)

**File:** `plugins/mycelium-core/skills/schema.sql`

```sql
-- Create skills metadata table
CREATE TABLE IF NOT EXISTS skills (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    author VARCHAR(255),
    tier INTEGER,
    consensus INTEGER,
    capabilities JSONB,
    execution JSONB,
    performance JSONB,
    dependencies JSONB,
    telemetry JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create embeddings table with pgvector
CREATE TABLE IF NOT EXISTS skill_embeddings (
    id SERIAL PRIMARY KEY,
    skill_id VARCHAR(255) REFERENCES skills(id),
    embedding vector(384),  -- sentence-transformers/all-MiniLM-L6-v2
    model_name VARCHAR(255) DEFAULT 'all-MiniLM-L6-v2',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create HNSW index for similarity search
CREATE INDEX IF NOT EXISTS skill_embeddings_hnsw_idx
ON skill_embeddings USING hnsw (embedding vector_cosine_ops);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS skills_name_idx ON skills(name);
CREATE INDEX IF NOT EXISTS skills_tier_idx ON skills(tier);
CREATE INDEX IF NOT EXISTS skills_capabilities_idx ON skills USING gin(capabilities);
```

**Apply Schema:**
```bash
# Apply database schema
psql mycelium_skills -f plugins/mycelium-core/skills/schema.sql

# Verify tables created
psql mycelium_skills -c "\dt"
# Expected output:
#  public | skills            | table | <user>
#  public | skill_embeddings  | table | <user>
```

**Python Database Connection:**
```python
# plugins/mycelium-core/skills/database.py
import os
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from pgvector.psycopg2 import register_vector

class DatabaseManager:
    """Manages PostgreSQL connections for skills infrastructure."""

    def __init__(self):
        self.pool = SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            host=os.getenv('PGHOST', 'localhost'),
            database=os.getenv('PGDATABASE', 'mycelium_skills'),
            user=os.getenv('PGUSER', os.getenv('USER')),
            password=os.getenv('PGPASSWORD', '')
        )

    def get_connection(self):
        """Get connection from pool."""
        conn = self.pool.getconn()
        register_vector(conn)  # Enable pgvector support
        return conn

    def return_connection(self, conn):
        """Return connection to pool."""
        self.pool.putconn(conn)
```
```

#### Day 2-3: First Skill - Update with pgvector

**Update Step 3: Implement TF-IDF Vectorizer:**

**Add Before Class Definition:**
```python
"""
TF-IDF Vectorizer for agent search with pgvector integration.
Hybrid approach: TF-IDF for explainability + embeddings for semantic search.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import psycopg2
from pgvector.psycopg2 import register_vector

class AgentVectorizer:
    """Hybrid TF-IDF + Embeddings agent similarity ranking."""

    def __init__(self, index_path: str, db_manager: Optional['DatabaseManager'] = None):
        """Initialize vectorizer.

        Args:
            index_path: Path to agents/index.json
            db_manager: Database manager for pgvector (optional)
        """
        self.index_path = Path(index_path)
        self.db_manager = db_manager
        self.agents = self._load_agents()

        # TF-IDF for keyword matching (explainability)
        self.vectorizer = TfidfVectorizer(
            max_features=500,
            stop_words='english',
            ngram_range=(1, 2),
            lowercase=True
        )
        self.agent_vectors = self._vectorize_agents()

        # Sentence embeddings for semantic search (accuracy)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self._ensure_embeddings()

    def _ensure_embeddings(self):
        """Ensure all agents have embeddings in database."""
        if not self.db_manager:
            return  # Skip if no database

        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()

            # Check which agents need embeddings
            cursor.execute("""
                SELECT id FROM skills
                WHERE id NOT IN (SELECT skill_id FROM skill_embeddings)
            """)
            missing = [row[0] for row in cursor.fetchall()]

            if missing:
                print(f"Generating embeddings for {len(missing)} agents...")
                for agent in self.agents:
                    if agent['id'] in missing:
                        # Generate embedding
                        text = f"{agent.get('description', '')} {' '.join(agent.get('keywords', []))}"
                        embedding = self.embedding_model.encode(text)

                        # Store in database
                        cursor.execute("""
                            INSERT INTO skill_embeddings (skill_id, embedding)
                            VALUES (%s, %s)
                        """, (agent['id'], embedding.tolist()))

                conn.commit()
                print(f"✅ Generated {len(missing)} embeddings")
        finally:
            self.db_manager.return_connection(conn)

    def search(
        self,
        query: str,
        max_results: int = 5,
        category_filter: Optional[str] = None,
        min_score: float = 0.0,
        use_embeddings: bool = True
    ) -> List[Dict[str, Any]]:
        """Hybrid search using TF-IDF + embeddings.

        Args:
            query: Search query
            max_results: Max results to return
            category_filter: Optional category filter
            min_score: Minimum similarity score
            use_embeddings: Use pgvector semantic search (default: True)

        Returns:
            List of matching agents with scores
        """
        # TF-IDF search (fast, explainable)
        tfidf_results = self._tfidf_search(query, max_results * 2, category_filter)

        # Embedding search (accurate, semantic)
        if use_embeddings and self.db_manager:
            embedding_results = self._embedding_search(query, max_results * 2, category_filter)

            # Combine results (weighted average)
            combined = self._combine_results(tfidf_results, embedding_results, weights=(0.3, 0.7))
        else:
            combined = tfidf_results

        # Filter and return top results
        filtered = [r for r in combined if r['score'] >= min_score]
        return filtered[:max_results]

    def _embedding_search(
        self,
        query: str,
        max_results: int,
        category_filter: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Search using pgvector embeddings."""
        conn = self.db_manager.get_connection()
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query)

            # Similarity search using pgvector
            cursor = conn.cursor()
            sql = """
                SELECT s.id, s.name, s.description, s.category,
                       1 - (e.embedding <=> %s::vector) as similarity
                FROM skills s
                JOIN skill_embeddings e ON e.skill_id = s.id
            """
            params = [query_embedding.tolist()]

            if category_filter:
                sql += " WHERE s.category = %s"
                params.append(category_filter)

            sql += " ORDER BY e.embedding <=> %s::vector LIMIT %s"
            params.extend([query_embedding.tolist(), max_results])

            cursor.execute(sql, params)

            results = []
            for row in cursor.fetchall():
                agent_id, name, description, category, similarity = row
                results.append({
                    'agent_id': agent_id,
                    'score': float(similarity),
                    'explanation': f"Semantic match (embedding similarity: {similarity:.3f})",
                    'category': category or 'uncategorized'
                })

            return results
        finally:
            self.db_manager.return_connection(conn)

    def _combine_results(
        self,
        tfidf_results: List[Dict],
        embedding_results: List[Dict],
        weights: tuple = (0.3, 0.7)
    ) -> List[Dict]:
        """Combine TF-IDF and embedding results with weighted scores."""
        # Create maps for quick lookup
        tfidf_map = {r['agent_id']: r for r in tfidf_results}
        embedding_map = {r['agent_id']: r for r in embedding_results}

        # Get all unique agent IDs
        all_ids = set(tfidf_map.keys()) | set(embedding_map.keys())

        # Combine scores
        combined = []
        for agent_id in all_ids:
            tfidf_score = tfidf_map.get(agent_id, {}).get('score', 0.0)
            embedding_score = embedding_map.get(agent_id, {}).get('score', 0.0)

            # Weighted average
            final_score = weights[0] * tfidf_score + weights[1] * embedding_score

            # Use embedding result as template (better explanation)
            result = embedding_map.get(agent_id, tfidf_map.get(agent_id))
            result['score'] = final_score
            result['explanation'] = f"Hybrid match (TF-IDF: {tfidf_score:.3f}, Embedding: {embedding_score:.3f})"

            combined.append(result)

        # Sort by combined score
        combined.sort(key=lambda x: x['score'], reverse=True)
        return combined
```

---

### 7. M01 Milestone (`M01_AGENT_DISCOVERY_SKILLS.md`)

**File:** `/home/gerald/git/mycelium/docs/projects/claude-code-skills/milestones/M01_AGENT_DISCOVERY_SKILLS.md`

#### Task 1.1: Agent Registry Infrastructure - Update for PostgreSQL

**Current Acceptance Criteria:**
```markdown
- [ ] Agent metadata schema defined with fields for name, capabilities...
- [ ] Database tables created with proper indexing...
```

**Change To:**
```markdown
**Acceptance Criteria:**
- [ ] PostgreSQL database created: `mycelium_skills`
- [ ] pgvector extension installed and verified
- [ ] Agent metadata schema implemented with proper normalization
- [ ] skill_embeddings table created with HNSW indexing
- [ ] Connection pooling configured (min: 1, max: 10)
- [ ] Migration scripts created for schema evolution
- [ ] Registry populated with metadata for all 130+ existing Mycelium agents
- [ ] Embeddings generated for all agents (sentence-transformers/all-MiniLM-L6-v2)
- [ ] Query performance validated: <10ms for discovery, <20ms for embedding search (P95)
- [ ] Unit tests achieving >90% coverage for registry and embedding operations
- [ ] Database backup and recovery procedures documented
```

**Update Deliverables:**
```markdown
**Deliverables:**
- `/plugins/mycelium-core/registry/schema.sql` - PostgreSQL schema with pgvector
- `/plugins/mycelium-core/registry/registry.py` - Registry implementation
- `/plugins/mycelium-core/registry/embeddings.py` - Embedding generation and storage
- `/plugins/mycelium-core/registry/database.py` - Database connection management
- `/plugins/mycelium-core/registry/migrations/` - Schema migration scripts
- `/tests/unit/test_registry.py` - Unit test suite
- `/tests/unit/test_embeddings.py` - Embedding tests
- `/docs/api/registry-api.md` - Registry API documentation
- `/docs/operations/database-setup.md` - Database setup and maintenance guide
```

#### Task 1.3: NLP Capability Matching Engine - Update for pgvector

**Current:**
```markdown
**Acceptance Criteria:**
- [ ] Embedding model selected and integrated (sentence-transformers recommended)
- [ ] Agent capability embeddings pre-computed and cached for all 130+ agents
```

**Change To:**
```markdown
**Acceptance Criteria:**
- [ ] Embedding model integrated: sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)
- [ ] Agent capability embeddings generated and stored in pgvector table
- [ ] HNSW index created for approximate nearest neighbor search
- [ ] Hybrid matching algorithm implemented: TF-IDF (30%) + Embeddings (70%)
- [ ] Matching algorithm provides both semantic and keyword-based results
- [ ] Confidence scoring system implemented (0.0-1.0 scale) with separate scores for each method
- [ ] Fallback recommendations provided when no high-confidence matches exist
- [ ] Matching accuracy validated >90% on test dataset of 100+ queries (hybrid approach)
- [ ] Performance optimized: <10ms TF-IDF, <20ms embedding search (P95)
- [ ] Database queries use pgvector cosine similarity operator (<=>)
- [ ] Unit tests covering edge cases (ambiguous queries, no matches, multiple matches)
```

**Update Deliverables:**
```markdown
**Deliverables:**
- `/plugins/mycelium-core/matching/matcher.py` - Hybrid matching engine
- `/plugins/mycelium-core/matching/embeddings.py` - Embedding generation
- `/plugins/mycelium-core/matching/database_search.py` - pgvector similarity search
- `/tests/unit/test_matcher.py` - Unit test suite
- `/tests/unit/test_embedding_search.py` - pgvector search tests
- `/tests/fixtures/matching_test_queries.json` - Test dataset
- `/docs/technical/matching-algorithm.md` - Hybrid algorithm documentation
- `/docs/technical/pgvector-integration.md` - pgvector usage guide
```

---

### 8. M02 Milestone (`M02_SKILL_INFRASTRUCTURE.md`)

**File:** `/home/gerald/git/mycelium/docs/projects/claude-code-skills/milestones/M02_SKILL_INFRASTRUCTURE.md`

#### Overview Section - Update Effort Estimate

**Current:**
```markdown
| Duration | 5 weeks (100 hours) |
```

**Change To:**
```markdown
| Duration | 6 weeks (140 hours) |
| Additional Scope | +40 hours for Web UI foundation and Textual TUI |
```

#### Section: Requirements - Add UI Requirements

**Add New Subsection After IR-2.5:**
```markdown
### User Interface Requirements (UR)

#### UR-2.1: Web UI Foundation
**Priority:** P1 (High)
**Owner:** Frontend Developer (assisted by Infrastructure Architect)

Establish web UI foundation using TanStack ecosystem for future dashboard development:

**Technology Stack:**
- TanStack Query for data fetching and caching
- TanStack Router for client-side routing
- TanStack Table for data grids
- TanStack Virtual for performance optimization
- Storybook for component library documentation

**Acceptance Criteria:**
- [ ] React application initialized with Vite build system
- [ ] TanStack Query configured with proper cache settings
- [ ] TanStack Router configured with route definitions
- [ ] Design system foundations established (colors, typography, spacing)
- [ ] Storybook configured with component stories
- [ ] Base components created (Button, Input, Card, Table, etc.)
- [ ] Skills Dashboard prototype demonstrating data fetching
- [ ] Analytics Dashboard prototype with charts
- [ ] Responsive design working on mobile/tablet/desktop
- [ ] Performance: <1s initial load, <200ms page transitions

#### UR-2.2: CLI Enhancement with Textual TUI
**Priority:** P1 (High)
**Owner:** CLI Developer (assisted by Infrastructure Architect)

Implement dual CLI interface: traditional text commands + interactive TUI:

**Text Commands:**
- Scriptable commands for automation
- JSON output format support
- Piping and redirection support

**Textual TUI:**
- Interactive terminal UI using Textual framework
- Rich formatting and colors
- Live updates and progress indicators
- Keyboard navigation

**Acceptance Criteria:**
- [ ] Text commands implemented for core operations (install, list, search)
- [ ] Textual TUI application structure created
- [ ] Interactive widgets for skills browsing
- [ ] Live analytics dashboard in TUI
- [ ] Keyboard shortcuts documented and functional
- [ ] TUI works on macOS, Linux, and Windows Terminal
- [ ] Performance: <500ms TUI startup, <50ms screen refresh
- [ ] Documentation includes both command and TUI usage
```

#### Add New Tasks

**Insert After Task 2.6:**

```markdown
### Task 2.7: Web UI Foundation
**Owner:** Frontend Developer
**Effort:** 24 hours (Week 5-6)
**Dependencies:** Task 2.2 (API endpoints for data)
**Supports Requirements:** UR-2.1

Establish web UI foundation with TanStack ecosystem and design system.

**Acceptance Criteria:**
- [ ] React project initialized with TypeScript and Vite
- [ ] TanStack Query configured with QueryClient
- [ ] TanStack Router configured with route tree
- [ ] Tailwind CSS configured with design tokens
- [ ] Storybook configured with MDX documentation
- [ ] Design system components created (10+ base components)
- [ ] Skills Dashboard showing skill list with search/filter
- [ ] Analytics Dashboard with placeholder charts
- [ ] Component tests using React Testing Library
- [ ] Storybook deployed to static hosting
- [ ] Performance benchmarks meet targets

**Deliverables:**
1. `/home/gerald/git/mycelium/plugins/mycelium-core/ui/` - React application
2. `/home/gerald/git/mycelium/plugins/mycelium-core/ui/design-system/` - Component library
3. `/home/gerald/git/mycelium/plugins/mycelium-core/ui/.storybook/` - Storybook config
4. `/home/gerald/git/mycelium/plugins/mycelium-core/ui/src/pages/SkillsDashboard.tsx` - Skills page
5. `/home/gerald/git/mycelium/plugins/mycelium-core/ui/src/pages/Analytics.tsx` - Analytics page
6. `/home/gerald/git/mycelium/plugins/mycelium-core/ui/tests/` - Test suite
7. `/home/gerald/git/mycelium/docs/ui/design-system.md` - Design system documentation
8. `/home/gerald/git/mycelium/docs/ui/development-guide.md` - UI development guide

**Implementation Notes:**
```typescript
// TanStack Query setup
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000,
      cacheTime: 5 * 60 * 1000,
      refetchOnWindowFocus: false,
    },
  },
})

// TanStack Router setup
import { createRouter, RouterProvider } from '@tanstack/react-router'

const router = createRouter({
  routes: [
    { path: '/', component: () => <Dashboard /> },
    { path: '/skills', component: () => <SkillsBrowser /> },
    { path: '/skills/:id', component: ({ params }) => <SkillDetail id={params.id} /> },
    { path: '/analytics', component: () => <Analytics /> },
  ],
})

// App component
function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  )
}
```

### Task 2.8: CLI Enhancement with Textual TUI
**Owner:** CLI Developer
**Effort:** 16 hours (Week 6)
**Dependencies:** Task 2.2 (API endpoints), Task 2.5 (Registry)
**Supports Requirements:** UR-2.2

Implement dual CLI interface with text commands and interactive TUI.

**Acceptance Criteria:**
- [ ] Click-based CLI commands for core operations
- [ ] JSON output format for scripting
- [ ] Textual TUI application with main dashboard
- [ ] Interactive skills browser widget
- [ ] Live analytics display widget
- [ ] Keyboard navigation fully functional
- [ ] Rich formatting with progress bars and spinners
- [ ] Cross-platform testing (macOS, Linux, Windows)
- [ ] Documentation for both interfaces
- [ ] Performance targets met (<500ms startup)

**Deliverables:**
1. `/home/gerald/git/mycelium/plugins/mycelium-core/cli/commands/` - Click commands
2. `/home/gerald/git/mycelium/plugins/mycelium-core/cli/tui/app.py` - Textual application
3. `/home/gerald/git/mycelium/plugins/mycelium-core/cli/tui/widgets/` - Custom widgets
4. `/home/gerald/git/mycelium/plugins/mycelium-core/cli/tui/screens/` - TUI screens
5. `/home/gerald/git/mycelium/tests/cli/` - CLI test suite
6. `/home/gerald/git/mycelium/docs/cli/commands.md` - Command reference
7. `/home/gerald/git/mycelium/docs/cli/tui-guide.md` - TUI user guide
8. `/home/gerald/git/mycelium/docs/cli/keyboard-shortcuts.md` - Shortcut reference

**Implementation Notes:**
```python
# Click commands
import click

@click.group()
def cli():
    """Mycelium Skills CLI"""
    pass

@cli.command()
@click.argument('skill_name')
def install(skill_name: str):
    """Install a skill from the repository."""
    loader = SkillLoader()
    loader.install(skill_name)
    click.echo(f"✅ Installed {skill_name}")

@cli.command()
@click.option('--format', type=click.Choice(['table', 'json']), default='table')
def list(format: str):
    """List installed skills."""
    registry = SkillRegistry()
    skills = registry.list()

    if format == 'json':
        click.echo(json.dumps(skills, indent=2))
    else:
        # Table output
        for skill in skills:
            click.echo(f"{skill['name']:<30} {skill['version']:<10} {skill['tier']}")

# Textual TUI
from textual.app import App
from textual.widgets import Header, Footer, DataTable, Static
from textual.containers import Container

class MyceliumTUI(App):
    """Interactive TUI for Mycelium Skills."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("s", "skills", "Skills"),
        ("a", "analytics", "Analytics"),
    ]

    def compose(self):
        yield Header()
        yield Container(
            DataTable(id="skills_table"),
            Static(id="analytics_panel"),
        )
        yield Footer()

    def on_mount(self):
        table = self.query_one("#skills_table", DataTable)
        table.add_columns("Name", "Version", "Tier", "Status")

        # Load skills
        registry = SkillRegistry()
        for skill in registry.list():
            table.add_row(
                skill['name'],
                skill['version'],
                str(skill['tier']),
                "Active"
            )

if __name__ == '__main__':
    app = MyceliumTUI()
    app.run()
```
```

---

### 9. M03 Milestone (`M03_TOKEN_OPTIMIZATION.md`)

**File:** `/home/gerald/git/mycelium/docs/projects/claude-code-skills/milestones/M03_TOKEN_OPTIMIZATION.md`

#### Requirements Section - Add Budget Policy Requirement

**Add New Functional Requirement:**
```markdown
**FR-3.5: Configurable Token Budget Policy**
System shall support multiple budget enforcement modes: warn-only (default), hard limits (opt-in), and disabled, with per-agent policy overrides.

**Default Behavior:**
- Calculate budget recommendations without enforcement
- Provide warnings at 80% of calculated budget
- Allow execution to proceed regardless of budget
- Log actual consumption for optimization

**Configuration Options:**
```json
{
  "token_budget": {
    "mode": "warn",  // "warn" | "limit" | "off"
    "warn_threshold": 0.8,
    "hard_limit_enabled": false,
    "per_agent_overrides": {
      "security-expert": {"mode": "limit"},
      "code-reviewer": {"mode": "warn"}
    },
    "budget_calculation": {
      "method": "ml_prediction",  // "ml_prediction" | "static" | "historical"
      "buffer_percentage": 10
    }
  }
}
```
```

#### Task 3.2: Token Budget Optimizer - Update Implementation

**Current Acceptance Criteria:**
```markdown
- [ ] Task complexity estimator using agent metadata and historical data
- [ ] Constraint satisfaction solver allocates budgets meeting task requirements
```

**Change To:**
```markdown
**Acceptance Criteria:**
- [ ] Task complexity estimator using agent metadata and historical analytics
- [ ] Budget calculator provides recommendations (not enforced by default)
- [ ] Warning system triggers at configurable threshold (default: 80%)
- [ ] Hard limit enforcement available as opt-in feature
- [ ] Per-agent policy overrides supported in configuration
- [ ] Budget recommendations include confidence scores and justifications
- [ ] Handles budget warnings with clear messaging (not blocking)
- [ ] Optional enforcement mode respects hard limits when enabled
- [ ] Actual consumption tracking for model improvement (M05 integration)
- [ ] Integration with orchestration engine for workflow-level advisory
- [ ] Performance: <50ms budget calculation for 10-agent workflows
- [ ] Dashboard shows budget vs actual consumption trends
```

**Update Deliverables:**
```markdown
**Deliverables:**
1. `/home/gerald/git/mycelium/plugins/mycelium-core/optimization/budget_calculator.py` - Budget calculation (advisory)
2. `/home/gerald/git/mycelium/plugins/mycelium-core/optimization/warning_system.py` - Warning generation
3. `/home/gerald/git/mycelium/plugins/mycelium-core/optimization/policy_manager.py` - Policy configuration
4. `/home/gerald/git/mycelium/plugins/mycelium-core/optimization/enforcement.py` - Optional hard limits
5. `/home/gerald/git/mycelium/tests/optimization/test_budget_calculator.py` - Calculator tests
6. `/home/gerald/git/mycelium/tests/optimization/test_policy.py` - Policy tests
7. `/home/gerald/git/mycelium/docs/optimization/budget-policy.md` - Policy documentation
8. `/home/gerald/git/mycelium/docs/optimization/configuration-guide.md` - Configuration guide
```

**Add Implementation Example:**
```python
class TokenBudgetCalculator:
    """Calculate token budgets with advisory warnings (no enforcement by default)."""

    def __init__(self, policy_config: Dict[str, Any]):
        self.policy = PolicyManager(policy_config)
        self.predictor = MLTokenPredictor()  # From historical data

    def calculate_budget(
        self,
        workflow: Workflow,
        context: Dict[str, Any]
    ) -> BudgetRecommendation:
        """Calculate budget recommendation for workflow.

        Returns advisory budget with warnings, not hard limits.
        """
        # Predict token consumption
        estimated = self.predictor.predict(workflow, context)

        # Apply buffer
        buffer = self.policy.get_buffer_percentage()
        recommended = estimated * (1 + buffer / 100)

        # Generate recommendation
        return BudgetRecommendation(
            estimated_tokens=estimated,
            recommended_budget=recommended,
            confidence=self.predictor.confidence_score(),
            mode=self.policy.get_mode(),  # "warn" | "limit" | "off"
            warnings=self._generate_warnings(estimated, recommended),
            enforcement_enabled=self.policy.hard_limits_enabled()
        )

    def check_budget_status(
        self,
        consumed: int,
        budget: BudgetRecommendation
    ) -> BudgetStatus:
        """Check budget status and generate warnings if needed."""
        percentage = consumed / budget.recommended_budget

        status = BudgetStatus(
            consumed=consumed,
            recommended=budget.recommended_budget,
            percentage=percentage,
            warnings=[]
        )

        # Generate warnings based on policy
        if budget.mode == "warn" and percentage > self.policy.warn_threshold:
            status.warnings.append(
                f"⚠️ Token consumption at {percentage*100:.1f}% of recommended budget. "
                f"Consider optimizing or allocating more resources."
            )

        # Hard limit check (only if enabled)
        if budget.mode == "limit" and percentage > 1.0:
            if budget.enforcement_enabled:
                raise BudgetExceededError(
                    f"Hard budget limit exceeded: {consumed} > {budget.recommended_budget}"
                )
            else:
                status.warnings.append(
                    f"🚨 Budget exceeded but enforcement disabled. "
                    f"Enable hard limits if cost control is required."
                )

        return status
```

---

## Scope Impact Assessment

### Effort Increase Breakdown

| Milestone | Original Effort | Additional Effort | New Total | Primary Changes |
|-----------|----------------|-------------------|-----------|-----------------|
| M01 | 120 hours | +16 hours | 136 hours | PostgreSQL setup, pgvector integration, embeddings |
| M02 | 100 hours | +40 hours | 140 hours | Web UI foundation (24h), Textual TUI (16h) |
| M03 | 120 hours | +8 hours | 128 hours | Budget policy configuration, warning system |
| M04 | 80 hours | 0 hours | 80 hours | No changes (orchestration logic unchanged) |
| M05 | 100 hours | +12 hours | 112 hours | TimescaleDB setup, telemetry opt-in system |
| **Total** | **520 hours** | **+76 hours** | **596 hours** | **~15% increase** |

### New Infrastructure Components

**Database Infrastructure:**
- PostgreSQL 15+ installation and configuration
- pgvector extension setup and tuning
- TimescaleDB hypertables for analytics
- Connection pooling and optimization
- Backup and recovery procedures

**User Interface Components:**
- React application with Vite build system
- TanStack ecosystem integration (Query, Router, Table, Virtual)
- Design system with Storybook documentation
- Textual TUI application
- API endpoints for UI data access

**Configuration Management:**
- Token budget policy system
- Telemetry opt-in configuration
- Database connection parameters
- UI/TUI preferences

---

## Architectural Implications

### Positive Impacts

**1. Production-Ready Scalability**
- PostgreSQL handles growth to 1000+ agents and 1M+ analytics events
- pgvector provides sub-linear similarity search performance
- TimescaleDB optimizes time-series queries automatically
- No migration path needed from development to production

**2. Enhanced Developer Experience**
- Web UI provides visual exploration and configuration
- Textual TUI offers rich interactive experience in terminal
- Storybook documents component library for consistency
- Dual CLI modes support both automation and interaction

**3. Operational Flexibility**
- Token budgets inform rather than restrict (configurable)
- Telemetry opt-in respects privacy by default
- Private deployment support (configurable endpoint)
- Gradual adoption path for advanced features

**4. Future-Proof Foundation**
- pgvector enables advanced semantic search capabilities
- TimescaleDB supports advanced analytics and forecasting
- Web UI foundation supports future dashboard features
- Policy system allows experimentation with different approaches

### Challenges and Mitigations

**1. Increased Complexity**
- **Challenge:** More moving parts (PostgreSQL, pgvector, TimescaleDB, UI, TUI)
- **Mitigation:** Comprehensive documentation, automated setup scripts, Docker Compose for local development

**2. Infrastructure Dependencies**
- **Challenge:** Requires PostgreSQL + extensions, not just Python
- **Mitigation:** Provide installation scripts for all platforms, Docker image with all dependencies, clear setup documentation

**3. Development Environment Setup**
- **Challenge:** Longer onboarding time for new developers
- **Mitigation:** One-command setup script, VS Code dev container, detailed troubleshooting guide

**4. Testing Complexity**
- **Challenge:** Need test databases, embedding generation, UI testing
- **Mitigation:** Test fixtures with pre-generated embeddings, database mocking for unit tests, GitHub Actions CI with PostgreSQL service

---

## Implementation Guidance

### Phase 1: Database Foundation (Week 1)

**Priority:** Critical
**Blocking:** All subsequent work

**Tasks:**
1. Install PostgreSQL 15+ on development machines
2. Install pgvector extension
3. Set up TimescaleDB (for M05)
4. Create database schema
5. Write migration scripts
6. Document setup process
7. Create Docker Compose for local development

**Validation:**
- All developers can connect to PostgreSQL
- pgvector similarity search works (<20ms)
- Schema migrations run successfully
- Backup/restore procedures tested

### Phase 2: Hybrid Search Implementation (Week 2-3)

**Priority:** High
**Blocking:** M01 completion

**Tasks:**
1. Generate embeddings for all existing agents
2. Store embeddings in pgvector table
3. Create HNSW index
4. Implement hybrid search (TF-IDF + embeddings)
5. Benchmark search performance
6. Write comprehensive tests

**Validation:**
- Embedding generation <1s per agent
- Search accuracy >90% (hybrid approach)
- Search performance <20ms P95
- Test coverage >90%

### Phase 3: UI Foundation (Week 4-6)

**Priority:** Medium (can be parallelized)
**Non-blocking:** Can develop while other features progress

**Tasks:**
1. Set up React project with Vite
2. Configure TanStack ecosystem
3. Create design system foundations
4. Build Storybook component library
5. Implement Skills Dashboard prototype
6. Implement Analytics Dashboard prototype
7. Set up Textual TUI application
8. Implement interactive widgets

**Validation:**
- Web UI loads in <1s
- All components documented in Storybook
- TUI starts in <500ms
- Both interfaces functional for basic operations

### Phase 4: Policy Systems (Week 7-8)

**Priority:** Medium
**Blocking:** M03 completion

**Tasks:**
1. Implement policy configuration system
2. Create budget calculator (advisory mode)
3. Build warning generation system
4. Add optional hard limit enforcement
5. Integrate telemetry opt-in system
6. Write policy documentation

**Validation:**
- Default warn-only mode works correctly
- Hard limit mode functions when enabled
- Telemetry respects opt-in requirement
- Configuration changes take effect immediately

---

## Risk Mitigation Strategies

### Risk 1: PostgreSQL Setup Complexity

**Probability:** Medium
**Impact:** High (blocks all work)

**Mitigation:**
- Provide automated setup scripts for macOS, Linux, Windows
- Create Docker Compose configuration for instant setup
- Document common installation issues and solutions
- Offer pre-configured database dumps for quick start

**Contingency:**
- Provide managed database instance for team during development
- Create database-as-a-service Docker container
- Pair programming for setup assistance

### Risk 2: pgvector Performance Issues

**Probability:** Low
**Impact:** Medium (search slower than expected)

**Mitigation:**
- Benchmark early with realistic data volumes (500+ agents)
- Tune HNSW index parameters for optimal performance
- Implement caching layer for frequent queries
- Profile and optimize query patterns

**Contingency:**
- Fall back to TF-IDF only if pgvector underperforms
- Use pgvector for offline batch processing, cache results
- Upgrade to more powerful database instance

### Risk 3: UI Development Timeline

**Probability:** Medium
**Impact:** Low (UI is enhancement, not critical path)

**Mitigation:**
- Start UI development early (Week 4)
- Parallelize with other milestone work
- Use component library for faster development
- Scope MVP UI features carefully

**Contingency:**
- Defer advanced UI features to post-GA
- Focus on core functionality first (skills browsing)
- Release CLI/TUI first, Web UI follows

### Risk 4: Telemetry Privacy Concerns

**Probability:** Low
**Impact:** Medium (user trust)

**Mitigation:**
- Default to OFF, require explicit opt-in
- Support private deployment endpoints
- Document exactly what data is collected
- Provide data export and deletion capabilities

**Contingency:**
- Remove centralized telemetry entirely if needed
- Implement local-only analytics dashboard
- Make telemetry completely optional feature

---

## Testing Strategy Updates

### Database Testing

**Unit Tests:**
- Mock PostgreSQL connections using `pytest-postgresql`
- Test schema migrations forward and backward
- Verify embedding generation and storage
- Test query performance with realistic data

**Integration Tests:**
- Use test database with pgvector
- Pre-generated embeddings for test fixtures
- Test similarity search accuracy
- Benchmark query performance

### UI Testing

**Component Tests:**
- React Testing Library for component behavior
- Storybook interaction tests
- Visual regression testing with Chromatic

**E2E Tests:**
- Playwright for user workflows
- Test key scenarios (install skill, view analytics)
- Cross-browser testing (Chrome, Firefox, Safari)

### TUI Testing

**Snapshot Tests:**
- Textual snapshot testing for screen layouts
- Verify keyboard navigation
- Test different terminal sizes

**Manual Testing:**
- Test on macOS Terminal, iTerm2, Linux terminals, Windows Terminal
- Verify colors and formatting across terminals
- Test with screen readers for accessibility

---

## Documentation Priorities

### Critical Documentation (Before M01)
1. PostgreSQL setup guide (macOS, Linux, Windows)
2. pgvector installation and configuration
3. Database schema and migrations
4. Embedding generation process
5. Development environment setup (comprehensive)

### High Priority Documentation (Before M02)
6. Web UI development guide
7. Design system documentation (Storybook)
8. Textual TUI development guide
9. CLI command reference
10. Database backup and recovery procedures

### Medium Priority Documentation (Before M03)
11. Token budget policy configuration
12. Telemetry opt-in guide
13. Performance tuning guide
14. Troubleshooting guide (database, UI, TUI)

### Nice-to-Have Documentation (Post-GA)
15. Advanced database optimization
16. Custom UI theme development
17. TUI plugin development
18. Telemetry analytics cookbook

---

## Communication Plan

### Stakeholder Updates

**Immediate Actions:**
1. Share this plan with Gerald for approval
2. Present updated estimates to project team
3. Align on priorities and scope decisions
4. Get commitment on infrastructure setup timeline

**Weekly Updates:**
- Progress on database setup and pgvector integration
- UI/TUI development milestones
- Policy system implementation status
- Risks and blockers

**Milestone Reviews:**
- Demo database performance and search accuracy
- Showcase Web UI and TUI prototypes
- Validate budget policy configuration
- Review telemetry opt-in implementation

---

## Success Criteria (Updated)

### M01 Success Criteria (Updated)
- [ ] PostgreSQL with pgvector operational on all dev machines
- [ ] All 130+ agents have embeddings stored in database
- [ ] Hybrid search achieves >90% accuracy
- [ ] Search performance <20ms P95 (pgvector)
- [ ] Database schema supports future scaling to 1000+ agents

### M02 Success Criteria (Updated)
- [ ] All original M02 criteria met
- [ ] **NEW:** Web UI foundation functional with TanStack
- [ ] **NEW:** Skills Dashboard displays data from PostgreSQL
- [ ] **NEW:** Textual TUI provides interactive experience
- [ ] **NEW:** Storybook documents all components
- [ ] **NEW:** Both CLI modes functional (text + TUI)

### M03 Success Criteria (Updated)
- [ ] All original M03 criteria met
- [ ] **NEW:** Token budget policy configurable (warn/limit/off)
- [ ] **NEW:** Warning system provides actionable guidance
- [ ] **NEW:** Hard limit enforcement available as opt-in
- [ ] **NEW:** Telemetry opt-in system respects privacy defaults

---

## Appendix: Quick Reference

### Key Configuration Files

```bash
# Database connection
~/.mycelium/database.conf
# Token budget policy
~/.mycelium/token_budget.json
# Telemetry settings
~/.mycelium/telemetry.json
# UI preferences
~/.mycelium/ui_config.json
# TUI settings
~/.mycelium/tui_config.json
```

### Essential Commands

```bash
# Database setup
mycelium db init
mycelium db migrate
mycelium db status

# Embedding generation
mycelium embeddings generate
mycelium embeddings verify

# UI/TUI launch
mycelium ui start        # Web UI
mycelium tui             # Textual TUI

# Policy configuration
mycelium config token-budget mode warn
mycelium config token-budget mode limit
mycelium config telemetry enable
```

### Performance Targets (Quick Reference)

| Operation | Target | Technology |
|-----------|--------|------------|
| Agent search (keyword) | <10ms P95 | PostgreSQL B-tree |
| Agent search (semantic) | <20ms P95 | pgvector HNSW |
| Embeddings generation | <1s per agent | sentence-transformers |
| Web UI initial load | <1s | React + Vite |
| TUI startup | <500ms | Textual |
| Budget calculation | <50ms | Python (advisory) |

---

**Document Status:** Complete - Ready for Review
**Next Steps:**
1. Gerald reviews and approves changes
2. Technical lead creates implementation tasks
3. Team begins database setup (Week 1)
4. Parallel workstreams: database + UI foundation

**Questions or Concerns:** Contact technical lead for clarification on any changes.
