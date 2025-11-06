# Option D: Multi-Agent Orchestration UI

**Status**: Draft Backlog **Author**: @claude-code-developer + @project-manager **Created**: 2025-10-18 **Estimated
Effort**: 10-14 days (4-person team) **Complexity**: High (Full-Stack + Real-Time) **Dependencies**: Phase 2 Performance
Analytics (completed), Redis MCP Server

______________________________________________________________________

## Executive Summary

Build a **visual workflow orchestration dashboard** for designing, executing, and monitoring multi-agent collaborations.
Provides drag-and-drop DAG editor, real-time execution monitoring, and performance analytics for complex agent
workflows.

**Value Proposition**:

- **Visualization**: See agent workflows as interactive DAGs
- **Orchestration**: Design complex multi-agent pipelines without code
- **Monitoring**: Real-time status updates, logs, and performance metrics
- **Reusability**: Save workflows as templates for future use
- **Analytics**: Historical workflow performance and optimization insights

**Use Cases**:

1. **Project Setup**: Orchestrate @devops-engineer → @python-pro → @documentation-engineer
1. **Code Review**: Parallel execution of linters, tests, and security scans
1. **Documentation**: Multi-stage pipeline (analyze code → generate docs → review → publish)
1. **CI/CD Integration**: Trigger agent workflows from GitHub Actions

______________________________________________________________________

## Technical Architecture

### Technology Stack

```yaml
frontend:
  framework: React 18.3+
  state_management: Redux Toolkit + RTK Query
  routing: React Router v6.x
  ui_library: TailwindCSS 3.x + shadcn/ui
  visualization:
    workflow_editor: react-flow 11.x  # DAG editing
    charts: recharts 2.x  # Performance metrics
    syntax_highlighting: prism-react-renderer
  real_time: Socket.io-client 4.x
  build_tool: Vite 5.x
  package_manager: pnpm

backend:
  framework: FastAPI 0.110+
  async_runtime: asyncio + uvicorn
  database:
    workflows: PostgreSQL 15+ (persistence)
    cache: Redis 7+ (state + pub/sub)
  websocket: Socket.io 4.x (Python)
  task_queue: Celery 5.x (async execution)
  monitoring: Prometheus + Grafana

deployment:
  containerization: Docker + Docker Compose
  reverse_proxy: Caddy 2.x (TLS termination)
  orchestration: Kubernetes (optional, for scale)
  ci_cd: GitHub Actions
  hosting: Self-hosted or AWS/GCP

infrastructure:
  redis: Redis 7+ (state management, pub/sub)
  postgres: PostgreSQL 15+ (workflow storage)
  mcp_server: Redis MCP Server (coordination)
```

______________________________________________________________________

### System Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    React Frontend (Vite)                  │
│  ┌─────────────────┐  ┌──────────────────────────────┐  │
│  │ Workflow Editor │  │ Execution Dashboard          │  │
│  │ (React Flow)    │  │ (Real-time WebSocket)        │  │
│  └─────────────────┘  └──────────────────────────────┘  │
│  ┌─────────────────┐  ┌──────────────────────────────┐  │
│  │ Agent Library   │  │ Performance Analytics        │  │
│  │ (Redux Store)   │  │ (Recharts)                   │  │
│  └─────────────────┘  └──────────────────────────────┘  │
└──────────────────┬───────────────────────────────────────┘
                   │ HTTP/REST + WebSocket
                   ↓
┌──────────────────────────────────────────────────────────┐
│                 FastAPI Backend (Uvicorn)                 │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ REST API                                             │ │
│  │  - GET /api/workflows (list)                        │ │
│  │  - POST /api/workflows (create)                     │ │
│  │  - POST /api/workflows/{id}/execute (run)           │ │
│  │  - GET /api/agents (list available agents)          │ │
│  └─────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ WebSocket Server (Socket.io)                        │ │
│  │  - /ws/workflows/{id} (real-time updates)           │ │
│  └─────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ Workflow Executor (Celery Tasks)                    │ │
│  │  - execute_workflow(workflow_id)                    │ │
│  │  - execute_agent_node(node_id)                      │ │
│  └─────────────────────────────────────────────────────┘ │
└──────────────────┬───────────────────────────────────────┘
                   │
                   ↓
┌──────────────────────────────────────────────────────────┐
│                   Data Layer                              │
│  ┌──────────────────┐  ┌─────────────────────────────┐  │
│  │ PostgreSQL       │  │ Redis                        │  │
│  │ - Workflows      │  │ - Execution State            │  │
│  │ - Executions     │  │ - Pub/Sub (events)           │  │
│  │ - Templates      │  │ - Session Cache              │  │
│  └──────────────────┘  └─────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Redis MCP Server (Agent Coordination)             │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

______________________________________________________________________

### Data Flow (Workflow Execution)

```
User clicks "Execute" in UI
     ↓
[Frontend] POST /api/workflows/{id}/execute
     ↓
[Backend] Create ExecutionRecord in PostgreSQL
     ↓
[Backend] Enqueue Celery task: execute_workflow(workflow_id)
     ↓
[Celery Worker] Load workflow DAG from PostgreSQL
     ↓
[Celery Worker] Topological sort (execution order)
     ↓
[For each node in DAG]:
  ├─ Update node status → "running"
  ├─ Publish status update → Redis Pub/Sub
  ├─ Execute agent (invoke Claude Code)
  ├─ Collect logs + outputs
  ├─ Update node status → "completed" | "failed"
  └─ Publish status update → Redis Pub/Sub
     ↓
[Redis Pub/Sub] → WebSocket Server
     ↓
[WebSocket] Broadcast to connected clients
     ↓
[Frontend] React component re-renders with new status
     ↓
[UI] Shows real-time progress (green/yellow/red nodes)
```

______________________________________________________________________

## Database Schema

### PostgreSQL Tables

```sql
-- Workflow definitions
CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255),  -- User ID (future auth)
    is_template BOOLEAN DEFAULT FALSE,

    -- DAG structure (JSON)
    nodes JSONB NOT NULL,  -- [{"id": "node-1", "agent_id": "python-pro", ...}, ...]
    edges JSONB NOT NULL,  -- [{"source": "node-1", "target": "node-2", ...}, ...]

    -- Metadata
    tags VARCHAR[] DEFAULT '{}',
    category VARCHAR(100),

    CONSTRAINT valid_nodes CHECK (jsonb_typeof(nodes) = 'array'),
    CONSTRAINT valid_edges CHECK (jsonb_typeof(edges) = 'array')
);

-- Workflow executions
CREATE TABLE executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,

    -- Execution metadata
    status VARCHAR(50) DEFAULT 'pending',  -- pending, running, completed, failed, cancelled
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds FLOAT,

    -- Execution context
    trigger VARCHAR(100),  -- manual, scheduled, webhook, github-action
    triggered_by VARCHAR(255),  -- User ID
    input_params JSONB DEFAULT '{}',

    -- Results
    output_data JSONB,
    error_message TEXT,

    -- Node-level status
    node_statuses JSONB DEFAULT '{}',  -- {"node-1": "completed", "node-2": "running", ...}

    CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'))
);

-- Execution logs (detailed logs for each node)
CREATE TABLE execution_logs (
    id BIGSERIAL PRIMARY KEY,
    execution_id UUID NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
    node_id VARCHAR(100) NOT NULL,

    -- Log entry
    timestamp TIMESTAMP DEFAULT NOW(),
    level VARCHAR(20),  -- debug, info, warning, error
    message TEXT NOT NULL,

    -- Optional structured data
    metadata JSONB,

    INDEX idx_execution_logs_execution_id (execution_id),
    INDEX idx_execution_logs_node_id (node_id)
);

-- Workflow templates (pre-built workflows)
CREATE TABLE workflow_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),

    -- Template data (same structure as workflows)
    nodes JSONB NOT NULL,
    edges JSONB NOT NULL,

    -- Usage stats
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),

    -- Discoverability
    tags VARCHAR[] DEFAULT '{}',
    keywords VARCHAR[] DEFAULT '{}'
);

-- Indexes for performance
CREATE INDEX idx_workflows_created_at ON workflows(created_at DESC);
CREATE INDEX idx_executions_workflow_id ON executions(workflow_id);
CREATE INDEX idx_executions_status ON executions(status);
CREATE INDEX idx_executions_started_at ON executions(started_at DESC);
```

______________________________________________________________________

## API Endpoints

### REST API (FastAPI)

```python
from fastapi import FastAPI, HTTPException, WebSocket
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

app = FastAPI(title="Mycelium Orchestration API", version="1.0.0")


# ============================================================================
# Data Models (Pydantic)
# ============================================================================

class AgentNode(BaseModel):
    """Agent node in workflow DAG."""
    id: str = Field(..., description="Unique node ID")
    agent_type: str = Field(..., description="Agent ID (e.g., 'python-pro')")
    position: tuple[int, int] = Field(..., description="(x, y) position in canvas")
    config: Dict[str, Any] = Field(default_factory=dict, description="Node-specific config")


class WorkflowEdge(BaseModel):
    """Edge connecting two nodes."""
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    condition: Optional[str] = Field(None, description="Conditional edge (e.g., 'on_success')")


class WorkflowCreate(BaseModel):
    """Create workflow request."""
    name: str
    description: Optional[str] = None
    nodes: List[AgentNode]
    edges: List[WorkflowEdge]
    tags: List[str] = Field(default_factory=list)
    category: Optional[str] = None


class WorkflowResponse(BaseModel):
    """Workflow response."""
    id: uuid.UUID
    name: str
    description: Optional[str]
    nodes: List[AgentNode]
    edges: List[WorkflowEdge]
    created_at: datetime
    updated_at: datetime
    is_template: bool


class ExecutionCreate(BaseModel):
    """Execute workflow request."""
    input_params: Dict[str, Any] = Field(default_factory=dict)
    trigger: str = "manual"


class ExecutionResponse(BaseModel):
    """Execution response."""
    id: uuid.UUID
    workflow_id: uuid.UUID
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    node_statuses: Dict[str, str]
    error_message: Optional[str]


# ============================================================================
# Endpoints
# ============================================================================

@app.get("/api/agents", response_model=List[Dict[str, Any]])
async def list_agents():
    """List all available agents from discovery system.

    Returns:
        List of agent metadata dictionaries

    Example:
        GET /api/agents

        Response:
        [
            {
                "id": "python-pro",
                "name": "Python Pro",
                "category": "core-development",
                "description": "Senior Python developer...",
                "keywords": ["python", "backend", "testing"]
            },
            ...
        ]
    """
    from scripts.agent_discovery import AgentDiscovery
    from pathlib import Path

    discovery = AgentDiscovery(Path("plugins/mycelium-core/agents/index.json"))
    agents = discovery.list_agents()

    return agents


@app.get("/api/workflows", response_model=List[WorkflowResponse])
async def list_workflows(
    category: Optional[str] = None,
    is_template: Optional[bool] = None,
    limit: int = 50
):
    """List workflows with optional filtering.

    Args:
        category: Filter by category
        is_template: Filter templates (True) or user workflows (False)
        limit: Maximum number of results

    Returns:
        List of workflow objects

    Example:
        GET /api/workflows?category=ci-cd&limit=10
    """
    # TODO: Implement database query
    # For now, return empty list
    return []


@app.post("/api/workflows", response_model=WorkflowResponse, status_code=201)
async def create_workflow(workflow: WorkflowCreate):
    """Create new workflow.

    Args:
        workflow: Workflow definition

    Returns:
        Created workflow object

    Example:
        POST /api/workflows

        Body:
        {
            "name": "Python Code Review",
            "description": "Automated code review workflow",
            "nodes": [
                {"id": "node-1", "agent_type": "python-pro", "position": [100, 100]},
                {"id": "node-2", "agent_type": "devops-engineer", "position": [300, 100]}
            ],
            "edges": [
                {"source": "node-1", "target": "node-2"}
            ],
            "tags": ["python", "code-review"],
            "category": "quality"
        }
    """
    # TODO: Implement database insert
    # Validate DAG (no cycles)
    # Store in PostgreSQL
    raise HTTPException(status_code=501, detail="Not implemented")


@app.get("/api/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: uuid.UUID):
    """Get workflow by ID.

    Args:
        workflow_id: Workflow UUID

    Returns:
        Workflow object

    Example:
        GET /api/workflows/123e4567-e89b-12d3-a456-426614174000
    """
    # TODO: Implement database query
    raise HTTPException(status_code=404, detail="Workflow not found")


@app.put("/api/workflows/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(workflow_id: uuid.UUID, workflow: WorkflowCreate):
    """Update existing workflow.

    Args:
        workflow_id: Workflow UUID
        workflow: Updated workflow definition

    Returns:
        Updated workflow object
    """
    # TODO: Implement database update
    raise HTTPException(status_code=501, detail="Not implemented")


@app.delete("/api/workflows/{workflow_id}", status_code=204)
async def delete_workflow(workflow_id: uuid.UUID):
    """Delete workflow.

    Args:
        workflow_id: Workflow UUID

    Example:
        DELETE /api/workflows/123e4567-e89b-12d3-a456-426614174000
    """
    # TODO: Implement database delete
    # Check if workflow has running executions
    raise HTTPException(status_code=501, detail="Not implemented")


@app.post("/api/workflows/{workflow_id}/execute", response_model=ExecutionResponse)
async def execute_workflow(workflow_id: uuid.UUID, execution: ExecutionCreate):
    """Execute workflow asynchronously.

    Creates execution record and enqueues Celery task for async execution.
    Client should connect to WebSocket for real-time updates.

    Args:
        workflow_id: Workflow UUID
        execution: Execution parameters

    Returns:
        Execution object with status "pending"

    Example:
        POST /api/workflows/123e4567-e89b-12d3-a456-426614174000/execute

        Body:
        {
            "input_params": {"branch": "main", "run_tests": true},
            "trigger": "manual"
        }

        Response:
        {
            "id": "exec-456...",
            "workflow_id": "123e4567-...",
            "status": "pending",
            "started_at": null,
            "node_statuses": {}
        }
    """
    # TODO: Implement workflow execution
    # 1. Validate workflow exists
    # 2. Create execution record in PostgreSQL
    # 3. Enqueue Celery task: execute_workflow.delay(execution_id)
    # 4. Return execution object
    raise HTTPException(status_code=501, detail="Not implemented")


@app.get("/api/workflows/{workflow_id}/executions", response_model=List[ExecutionResponse])
async def list_executions(
    workflow_id: uuid.UUID,
    status: Optional[str] = None,
    limit: int = 50
):
    """List executions for workflow.

    Args:
        workflow_id: Workflow UUID
        status: Filter by status (pending, running, completed, failed, cancelled)
        limit: Maximum number of results

    Returns:
        List of execution objects

    Example:
        GET /api/workflows/123e4567-e89b-12d3-a456-426614174000/executions?status=completed
    """
    # TODO: Implement database query
    return []


@app.get("/api/executions/{execution_id}", response_model=ExecutionResponse)
async def get_execution(execution_id: uuid.UUID):
    """Get execution details.

    Args:
        execution_id: Execution UUID

    Returns:
        Execution object with node statuses and logs
    """
    # TODO: Implement database query
    raise HTTPException(status_code=404, detail="Execution not found")


@app.post("/api/executions/{execution_id}/cancel", status_code=204)
async def cancel_execution(execution_id: uuid.UUID):
    """Cancel running execution.

    Args:
        execution_id: Execution UUID

    Example:
        POST /api/executions/exec-456.../cancel
    """
    # TODO: Implement cancellation
    # 1. Update execution status to "cancelled"
    # 2. Revoke Celery task
    # 3. Publish cancellation event via Redis Pub/Sub
    raise HTTPException(status_code=501, detail="Not implemented")


@app.get("/api/executions/{execution_id}/logs")
async def get_execution_logs(
    execution_id: uuid.UUID,
    node_id: Optional[str] = None,
    level: Optional[str] = None,
    limit: int = 1000
):
    """Get execution logs.

    Args:
        execution_id: Execution UUID
        node_id: Optional node ID filter
        level: Optional log level filter (debug, info, warning, error)
        limit: Maximum number of log entries

    Returns:
        List of log entries

    Example:
        GET /api/executions/exec-456.../logs?node_id=node-1&level=error

        Response:
        [
            {
                "id": 12345,
                "node_id": "node-1",
                "timestamp": "2025-10-19T12:00:00Z",
                "level": "error",
                "message": "Agent execution failed: ...",
                "metadata": {"error_code": "AGENT_TIMEOUT"}
            },
            ...
        ]
    """
    # TODO: Implement database query
    return []


@app.get("/api/metrics")
async def get_metrics(days: int = 7):
    """Get orchestration performance metrics.

    Integrates with Phase 2 analytics to provide workflow-level metrics.

    Args:
        days: Number of days to analyze

    Returns:
        Metrics dictionary with workflow statistics

    Example:
        GET /api/metrics?days=30

        Response:
        {
            "total_workflows": 42,
            "total_executions": 256,
            "success_rate": 94.5,
            "avg_duration_seconds": 45.2,
            "top_workflows": [
                {"name": "Python Code Review", "executions": 82, "success_rate": 98.8},
                ...
            ]
        }
    """
    # TODO: Implement analytics query
    # Combine PostgreSQL execution data with Phase 2 analytics
    return {}


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@app.websocket("/ws/workflows/{workflow_id}")
async def workflow_websocket(websocket: WebSocket, workflow_id: uuid.UUID):
    """WebSocket endpoint for real-time workflow updates.

    Clients connect to receive live status updates during execution.

    Protocol:
        - Client connects to /ws/workflows/{workflow_id}
        - Server sends status updates as JSON:
          {
              "event": "node_status_update",
              "execution_id": "exec-456...",
              "node_id": "node-1",
              "status": "running",
              "timestamp": "2025-10-19T12:00:00Z"
          }
        - Client can send ping to keep connection alive

    Example (JavaScript):
        const socket = new WebSocket('ws://localhost:8000/ws/workflows/123e4567-...');
        socket.onmessage = (event) => {
            const update = JSON.parse(event.data);
            console.log('Node status:', update);
        };
    """
    await websocket.accept()

    # Subscribe to Redis Pub/Sub for this workflow
    # Forward messages to WebSocket client

    try:
        while True:
            # Keep connection alive
            # Forward Redis messages to client
            data = await websocket.receive_text()
            # Handle client messages (ping, etc.)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Unsubscribe from Redis Pub/Sub
        pass
```

______________________________________________________________________

## Frontend Components

### React Flow Workflow Editor

```typescript
// src/components/WorkflowEditor.tsx
import React, { useCallback, useState } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Background,
  Controls,
  MiniMap,
  Connection,
  useNodesState,
  useEdgesState,
  NodeTypes,
} from 'reactflow';
import 'reactflow/dist/style.css';

import AgentNode from './AgentNode';
import { useCreateWorkflowMutation } from '../services/api';

// Custom node types
const nodeTypes: NodeTypes = {
  agentNode: AgentNode,
};

interface WorkflowEditorProps {
  initialNodes?: Node[];
  initialEdges?: Edge[];
  onSave?: (workflow: { nodes: Node[]; edges: Edge[] }) => void;
}

const WorkflowEditor: React.FC<WorkflowEditorProps> = ({
  initialNodes = [],
  initialEdges = [],
  onSave,
}) => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [workflowName, setWorkflowName] = useState('');

  const [createWorkflow, { isLoading }] = useCreateWorkflowMutation();

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const handleAddNode = (agentType: string) => {
    const newNode: Node = {
      id: `node-${Date.now()}`,
      type: 'agentNode',
      position: { x: Math.random() * 500, y: Math.random() * 500 },
      data: {
        agent_type: agentType,
        label: agentType,
      },
    };
    setNodes((nds) => [...nds, newNode]);
  };

  const handleSave = async () => {
    const workflow = {
      name: workflowName,
      nodes: nodes.map(n => ({
        id: n.id,
        agent_type: n.data.agent_type,
        position: [n.position.x, n.position.y],
        config: n.data.config || {},
      })),
      edges: edges.map(e => ({
        source: e.source,
        target: e.target,
        condition: e.data?.condition,
      })),
      tags: [],
      category: 'custom',
    };

    try {
      await createWorkflow(workflow).unwrap();
      alert('Workflow saved successfully!');
      if (onSave) onSave(workflow);
    } catch (error) {
      console.error('Failed to save workflow:', error);
      alert('Failed to save workflow');
    }
  };

  return (
    <div className="h-screen flex flex-col">
      {/* Toolbar */}
      <div className="bg-gray-800 text-white p-4 flex items-center gap-4">
        <input
          type="text"
          placeholder="Workflow Name"
          value={workflowName}
          onChange={(e) => setWorkflowName(e.target.value)}
          className="px-3 py-2 bg-gray-700 rounded"
        />
        <button
          onClick={handleSave}
          disabled={isLoading || !workflowName}
          className="px-4 py-2 bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {isLoading ? 'Saving...' : 'Save Workflow'}
        </button>
      </div>

      {/* Agent Palette */}
      <div className="bg-gray-100 p-4 border-b">
        <h3 className="font-semibold mb-2">Agents</h3>
        <div className="flex gap-2 overflow-x-auto">
          {['python-pro', 'devops-engineer', 'react-tanstack-developer', 'documentation-engineer'].map(agent => (
            <button
              key={agent}
              onClick={() => handleAddNode(agent)}
              className="px-3 py-1 bg-white border rounded hover:bg-gray-50 whitespace-nowrap"
            >
              + {agent}
            </button>
          ))}
        </div>
      </div>

      {/* Canvas */}
      <div className="flex-1">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          fitView
        >
          <Controls />
          <MiniMap />
          <Background />
        </ReactFlow>
      </div>
    </div>
  );
};

export default WorkflowEditor;
```

### Custom Agent Node

```typescript
// src/components/AgentNode.tsx
import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

interface AgentNodeData {
  agent_type: string;
  label: string;
  status?: 'idle' | 'running' | 'completed' | 'failed';
}

const AgentNode: React.FC<NodeProps<AgentNodeData>> = ({ data }) => {
  const getStatusColor = () => {
    switch (data.status) {
      case 'running':
        return 'bg-yellow-400';
      case 'completed':
        return 'bg-green-500';
      case 'failed':
        return 'bg-red-500';
      default:
        return 'bg-gray-300';
    }
  };

  return (
    <div className={`px-4 py-2 rounded shadow-lg border-2 ${getStatusColor()}`}>
      <Handle type="target" position={Position.Top} />

      <div className="font-semibold text-sm">{data.label}</div>
      {data.status && (
        <div className="text-xs text-gray-700 mt-1">{data.status}</div>
      )}

      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};

export default memo(AgentNode);
```

### Real-Time Execution Dashboard

```typescript
// src/components/ExecutionDashboard.tsx
import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import io, { Socket } from 'socket.io-client';
import { useGetExecutionQuery } from '../services/api';
import WorkflowVisualization from './WorkflowVisualization';

interface StatusUpdate {
  event: string;
  execution_id: string;
  node_id: string;
  status: string;
  timestamp: string;
}

const ExecutionDashboard: React.FC = () => {
  const { workflowId, executionId } = useParams<{ workflowId: string; executionId: string }>();
  const { data: execution, isLoading } = useGetExecutionQuery(executionId!);

  const [socket, setSocket] = useState<Socket | null>(null);
  const [nodeStatuses, setNodeStatuses] = useState<Record<string, string>>({});
  const [logs, setLogs] = useState<any[]>([]);

  useEffect(() => {
    // Connect to WebSocket
    const newSocket = io(`http://localhost:8000/ws/workflows/${workflowId}`);

    newSocket.on('connect', () => {
      console.log('Connected to workflow WebSocket');
    });

    newSocket.on('node_status_update', (update: StatusUpdate) => {
      console.log('Status update:', update);
      setNodeStatuses(prev => ({
        ...prev,
        [update.node_id]: update.status,
      }));

      // Add to logs
      setLogs(prev => [...prev, {
        timestamp: update.timestamp,
        message: `Node ${update.node_id}: ${update.status}`,
      }]);
    });

    setSocket(newSocket);

    return () => {
      newSocket.disconnect();
    };
  }, [workflowId]);

  if (isLoading) {
    return <div className="p-8">Loading execution...</div>;
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="bg-gray-800 text-white p-4">
        <h2 className="text-xl font-semibold">Execution: {executionId}</h2>
        <p className="text-sm text-gray-400">
          Status: {execution?.status || 'Unknown'} |
          Duration: {execution?.duration_seconds?.toFixed(2) || 'N/A'}s
        </p>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex">
        {/* Workflow Visualization */}
        <div className="flex-1 p-4">
          <WorkflowVisualization
            workflow={execution?.workflow}
            nodeStatuses={nodeStatuses}
          />
        </div>

        {/* Logs Panel */}
        <div className="w-96 bg-gray-50 border-l p-4 overflow-y-auto">
          <h3 className="font-semibold mb-4">Execution Logs</h3>
          <div className="space-y-2">
            {logs.map((log, i) => (
              <div key={i} className="text-sm">
                <span className="text-gray-500">{new Date(log.timestamp).toLocaleTimeString()}</span>
                <p className="text-gray-800">{log.message}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExecutionDashboard;
```

______________________________________________________________________

## Celery Task Executor

```python
# backend/tasks.py
from celery import Celery
import subprocess
import json
from datetime import datetime
import redis

celery_app = Celery(
    'mycelium_orchestrator',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1'
)

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)


@celery_app.task
def execute_workflow(execution_id: str):
    """Execute workflow asynchronously.

    Loads workflow DAG, performs topological sort, and executes nodes
    in dependency order. Publishes real-time updates via Redis Pub/Sub.

    Args:
        execution_id: UUID of execution record
    """
    # Load execution from database
    # TODO: Query PostgreSQL for execution + workflow

    # Publish execution started event
    publish_event({
        'event': 'execution_started',
        'execution_id': execution_id,
        'timestamp': datetime.utcnow().isoformat(),
    })

    try:
        # Topological sort of DAG
        # TODO: Implement topological sort
        execution_order = topological_sort(workflow['nodes'], workflow['edges'])

        # Execute nodes in order
        for node_id in execution_order:
            execute_node(execution_id, node_id, workflow['nodes'])

        # Mark execution as completed
        # TODO: Update PostgreSQL execution record
        publish_event({
            'event': 'execution_completed',
            'execution_id': execution_id,
            'timestamp': datetime.utcnow().isoformat(),
        })

    except Exception as e:
        # Mark execution as failed
        # TODO: Update PostgreSQL with error
        publish_event({
            'event': 'execution_failed',
            'execution_id': execution_id,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat(),
        })
        raise


def execute_node(execution_id: str, node_id: str, nodes: list):
    """Execute single agent node.

    Args:
        execution_id: Execution UUID
        node_id: Node ID to execute
        nodes: List of all nodes (for config lookup)
    """
    node = next(n for n in nodes if n['id'] == node_id)
    agent_type = node['agent_type']

    # Publish node started event
    publish_event({
        'event': 'node_status_update',
        'execution_id': execution_id,
        'node_id': node_id,
        'status': 'running',
        'timestamp': datetime.utcnow().isoformat(),
    })

    try:
        # Invoke Claude Code with agent
        # TODO: Construct prompt from node config
        result = subprocess.run(
            ['claude', '--agents', agent_type, '-p', 'Execute node task'],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode == 0:
            # Node succeeded
            publish_event({
                'event': 'node_status_update',
                'execution_id': execution_id,
                'node_id': node_id,
                'status': 'completed',
                'output': result.stdout,
                'timestamp': datetime.utcnow().isoformat(),
            })
        else:
            # Node failed
            publish_event({
                'event': 'node_status_update',
                'execution_id': execution_id,
                'node_id': node_id,
                'status': 'failed',
                'error': result.stderr,
                'timestamp': datetime.utcnow().isoformat(),
            })
            raise RuntimeError(f"Node {node_id} failed: {result.stderr}")

    except subprocess.TimeoutExpired:
        publish_event({
            'event': 'node_status_update',
            'execution_id': execution_id,
            'node_id': node_id,
            'status': 'failed',
            'error': 'Execution timeout (5 minutes)',
            'timestamp': datetime.utcnow().isoformat(),
        })
        raise
    except Exception as e:
        publish_event({
            'event': 'node_status_update',
            'execution_id': execution_id,
            'node_id': node_id,
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat(),
        })
        raise


def publish_event(event: dict):
    """Publish event to Redis Pub/Sub.

    Args:
        event: Event dictionary to publish
    """
    channel = f"mycelium:events:{event['execution_id']}"
    redis_client.publish(channel, json.dumps(event))


def topological_sort(nodes: list, edges: list) -> list:
    """Perform topological sort on DAG.

    Args:
        nodes: List of node dictionaries
        edges: List of edge dictionaries

    Returns:
        Ordered list of node IDs (execution order)

    Raises:
        ValueError: If DAG contains cycles
    """
    # TODO: Implement topological sort (Kahn's algorithm)
    # For now, return nodes in order
    return [n['id'] for n in nodes]
```

______________________________________________________________________

## Implementation Milestones

### M1 (Days 1-3): Backend Foundation

**Team**: @python-pro + @devops-engineer

- Day 1: Database schema + migrations (PostgreSQL)
- Day 2: FastAPI REST API (CRUD endpoints)
- Day 3: WebSocket server (Socket.io integration)

**Deliverables**:

- PostgreSQL tables created
- REST API with Swagger docs
- WebSocket connection working

______________________________________________________________________

### M2 (Days 4-7): React Frontend

**Team**: @nextjs-developer + @react-tanstack-developer

- Day 4: React app scaffold (Vite + TailwindCSS)
- Day 5: React Flow DAG editor (drag-and-drop)
- Day 6: Redux state management + RTK Query
- Day 7: Agent library UI + workflow CRUD

**Deliverables**:

- Workflow editor functional
- Agent palette working
- Save/load workflows

______________________________________________________________________

### M3 (Days 8-10): Real-Time Execution

**Team**: @python-pro + @react-tanstack-developer

- Day 8: Celery task executor (workflow execution logic)
- Day 9: Redis Pub/Sub integration
- Day 10: WebSocket real-time updates in UI

**Deliverables**:

- Workflows execute asynchronously
- Real-time status updates
- Execution logs displayed

______________________________________________________________________

### M4 (Days 11-14): Polish & Deploy

**Team**: Full team (4 people)

- Day 11: Performance metrics integration (Phase 2 analytics)
- Day 12: Error handling + recovery UI
- Day 13: Docker Compose setup + deployment
- Day 14: E2E testing (Playwright) + documentation

**Deliverables**:

- Production-ready deployment
- E2E test coverage
- User documentation

______________________________________________________________________

## Testing Strategy

### Unit Tests (Backend)

```python
# tests/test_workflow_api.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_list_agents():
    """Test agent listing endpoint."""
    response = client.get("/api/agents")
    assert response.status_code == 200
    agents = response.json()
    assert isinstance(agents, list)
    assert len(agents) > 0


def test_create_workflow():
    """Test workflow creation."""
    workflow = {
        "name": "Test Workflow",
        "nodes": [
            {"id": "node-1", "agent_type": "python-pro", "position": [100, 100]}
        ],
        "edges": [],
        "tags": ["test"]
    }
    response = client.post("/api/workflows", json=workflow)
    assert response.status_code == 201
    created = response.json()
    assert created["name"] == "Test Workflow"


def test_execute_workflow():
    """Test workflow execution."""
    # Create workflow first
    workflow = {...}  # Workflow definition
    create_response = client.post("/api/workflows", json=workflow)
    workflow_id = create_response.json()["id"]

    # Execute workflow
    execution = {"input_params": {}, "trigger": "manual"}
    response = client.post(f"/api/workflows/{workflow_id}/execute", json=execution)
    assert response.status_code == 200
    execution_data = response.json()
    assert execution_data["status"] in ["pending", "running"]
```

### E2E Tests (Frontend)

```typescript
// tests/e2e/workflow-editor.spec.ts
import { test, expect } from '@playwright/test';

test('create workflow with two agents', async ({ page }) => {
  await page.goto('http://localhost:5173/editor');

  // Add workflow name
  await page.fill('input[placeholder="Workflow Name"]', 'Test Workflow');

  // Add two agent nodes
  await page.click('button:has-text("+ python-pro")');
  await page.click('button:has-text("+ devops-engineer")');

  // Connect nodes
  // TODO: Simulate drag-and-drop connection

  // Save workflow
  await page.click('button:has-text("Save Workflow")');

  // Verify success message
  await expect(page.locator('text=Workflow saved successfully')).toBeVisible();
});

test('execute workflow and see real-time updates', async ({ page }) => {
  await page.goto('http://localhost:5173/workflows/123e4567-...');

  // Click execute button
  await page.click('button:has-text("Execute")');

  // Wait for WebSocket connection
  await page.waitForTimeout(1000);

  // Verify node status changes to "running"
  await expect(page.locator('.node-status:has-text("running")')).toBeVisible({ timeout: 5000 });

  // Verify completion
  await expect(page.locator('.node-status:has-text("completed")')).toBeVisible({ timeout: 30000 });
});
```

______________________________________________________________________

## Deployment (Docker Compose)

```yaml
# docker-compose.yml
version: '3.8'

services:
  # PostgreSQL database
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: mycelium_orchestration
      POSTGRES_USER: mycelium
      POSTGRES_PASSWORD: secure_password_here
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  # Redis (cache + pub/sub)
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  # FastAPI backend
  backend:
    build: ./backend
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://mycelium:secure_password_here@postgres/mycelium_orchestration
      REDIS_URL: redis://redis:6379/0

  # Celery worker
  celery_worker:
    build: ./backend
    command: celery -A tasks worker --loglevel=info
    volumes:
      - ./backend:/app
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://mycelium:secure_password_here@postgres/mycelium_orchestration
      REDIS_URL: redis://redis:6379/0

  # React frontend (Vite dev server)
  frontend:
    build: ./frontend
    command: npm run dev -- --host
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "5173:5173"
    depends_on:
      - backend

  # Caddy (reverse proxy + TLS)
  caddy:
    image: caddy:2
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - backend
      - frontend

volumes:
  postgres_data:
  caddy_data:
  caddy_config:
```

______________________________________________________________________

## Effort Estimate

**Complexity**: High (Full-Stack + Real-Time + Infrastructure)

**Team Composition**:

- 1x @python-pro (backend lead, Celery)
- 1x @nextjs-developer (frontend lead, React Flow)
- 1x @react-tanstack-developer (state management, WebSocket)
- 1x @devops-engineer (database, deployment, Docker)

**Breakdown**:

- Backend (REST + WebSocket): 3 days
- Frontend (React + React Flow): 4 days
- Celery execution engine: 2 days
- Real-time integration: 1 day
- Deployment + testing: 3 days
- Polish + documentation: 1 day

**Total**: 10-14 days (team of 4)

______________________________________________________________________

## Dependencies

**Required**:

- Phase 2 Performance Analytics (✅ Complete)
- Redis MCP Server (✅ Available)
- PostgreSQL 15+
- Python libraries: FastAPI, Celery, asyncpg, python-socketio
- Node libraries: React, React Flow, Socket.io-client, Redux Toolkit

**Installation** (Backend):

```bash
uv pip install fastapi uvicorn celery asyncpg python-socketio redis
```

**Installation** (Frontend):

```bash
pnpm add react react-dom react-router-dom reactflow recharts socket.io-client @reduxjs/toolkit
pnpm add -D tailwindcss @shadcn/ui vite @vitejs/plugin-react
```

______________________________________________________________________

## Success Metrics

**Acceptance Criteria**:

1. ✅ Drag-and-drop workflow editor (React Flow)
1. ✅ Save/load workflows to PostgreSQL
1. ✅ Async workflow execution (Celery)
1. ✅ Real-time status updates (WebSocket + Redis Pub/Sub)
1. ✅ Execution logs viewable in UI
1. ✅ Performance metrics dashboard
1. ✅ Docker Compose deployment working
1. ✅ E2E test coverage (Playwright)

**Performance Targets**:

- Workflow save/load: p95 \< 500ms
- WebSocket latency: p95 \< 100ms
- Execution start time: p95 \< 2s
- UI responsiveness: 60 FPS (React Flow)

______________________________________________________________________

## Risk Assessment

**Technical Risks**: HIGH

- WebSocket connection stability under load
- React Flow performance with large DAGs (50+ nodes)
- Celery task queue reliability
- Database schema complexity

**Blockers**: MODERATE

- Requires dedicated DevOps for PostgreSQL setup
- Frontend team needs React Flow expertise
- WebSocket integration requires Socket.io knowledge

**Mitigation**:

- Start with MVP (3-5 nodes, simple workflows)
- Load testing for WebSocket (100+ concurrent clients)
- Database migration strategy (Alembic)
- Fallback to polling if WebSocket fails

______________________________________________________________________

## Future Enhancements

**Phase 2 (Advanced Features)**:

- Workflow templates marketplace
- Conditional branching (if/else nodes)
- Parallel execution (fan-out/fan-in)
- Scheduled workflows (cron triggers)
- GitHub Actions integration
- Approval gates (human-in-the-loop)
- Workflow versioning + rollback

**Phase 3 (Scale)**:

- Kubernetes deployment
- Horizontal scaling (multiple Celery workers)
- Distributed tracing (OpenTelemetry)
- Multi-tenancy (team workspaces)

______________________________________________________________________

## Conclusion

Option D is the **most ambitious** feature, providing a visual orchestration platform for multi-agent workflows. High
complexity but **transformative UX** for power users managing complex agent collaborations.

**Recommendation**: **APPROVED for Future Roadmap** (after Options A/B/C complete, requires dedicated team)

______________________________________________________________________

**Next Steps**:

1. Approve for Q1 2026 roadmap
1. Assemble full-stack team (4 people)
1. Set up infrastructure (PostgreSQL, Redis, Celery)
1. Build MVP with 3 milestones (M1-M3)
1. Beta test with internal team before public release
