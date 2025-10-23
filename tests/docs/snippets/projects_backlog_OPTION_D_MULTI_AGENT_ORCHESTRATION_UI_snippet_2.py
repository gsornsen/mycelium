# Source: projects/backlog/OPTION_D_MULTI_AGENT_ORCHESTRATION_UI.md
# Line: 986
# Valid syntax: True
# Has imports: True
# Has assignments: True

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