# Source: projects/onboarding/milestones/M06_COORDINATION_TESTING.md
# Line: 423
# Valid syntax: True
# Has imports: True
# Has assignments: True

# tests/functional/test_coordination_patterns.py
"""Functional tests for coordination patterns."""

import pytest
import asyncio
from typing import Any

pytestmark = pytest.mark.asyncio

# ==================== PUB/SUB PATTERN ====================

async def test_pubsub_basic_message_delivery(redis_client):
    """Test basic pub/sub message delivery."""
    channel = "test:coordination:pubsub"
    message = "Hello from agent-1"

    # Subscribe to channel
    pubsub = await redis_client.subscribe(channel)

    # Publish message
    await redis_client.publish(channel, message)

    # Receive message
    received = await asyncio.wait_for(pubsub.get_message(), timeout=5.0)

    assert received is not None
    assert received['data'] == message

async def test_pubsub_multiple_subscribers(redis_client):
    """Test pub/sub with multiple subscribers."""
    channel = "test:coordination:multi_sub"
    message = "Broadcast message"

    # Create 3 subscribers
    subscribers = [
        await redis_client.subscribe(channel)
        for _ in range(3)
    ]

    # Publish once
    await redis_client.publish(channel, message)

    # All subscribers should receive
    for sub in subscribers:
        received = await asyncio.wait_for(sub.get_message(), timeout=5.0)
        assert received['data'] == message

# ==================== TASK QUEUE PATTERN ====================

async def test_task_queue_distribution(taskqueue_client):
    """Test task distribution across agents."""
    # Create project
    project = await taskqueue_client.create_project(
        name="test-project",
        description="Coordination test"
    )
    project_id = project['project_id']

    # Add 5 tasks
    tasks = []
    for i in range(5):
        task = await taskqueue_client.add_task(
            project_id=project_id,
            title=f"Task {i}",
            description=f"Test task {i}"
        )
        tasks.append(task)

    # Simulate 3 agents retrieving tasks
    retrieved = []
    for agent_id in range(3):
        task = await taskqueue_client.get_next_task(project_id)
        if task:
            retrieved.append(task)
            await taskqueue_client.update_task(
                project_id=project_id,
                task_id=task['task_id'],
                status='in_progress'
            )

    # Should retrieve 3 tasks (one per agent)
    assert len(retrieved) == 3

    # All should be different tasks
    task_ids = {t['task_id'] for t in retrieved}
    assert len(task_ids) == 3

async def test_task_queue_completion_flow(taskqueue_client):
    """Test complete task lifecycle."""
    project = await taskqueue_client.create_project(name="test-completion")
    project_id = project['project_id']

    # Add task
    task = await taskqueue_client.add_task(
        project_id=project_id,
        title="Complete me",
        description="Test completion"
    )
    task_id = task['task_id']

    # Get task
    retrieved = await taskqueue_client.get_next_task(project_id)
    assert retrieved['task_id'] == task_id
    assert retrieved['status'] == 'pending'

    # Mark in progress
    await taskqueue_client.update_task(
        project_id=project_id,
        task_id=task_id,
        status='in_progress'
    )

    # Complete task
    await taskqueue_client.update_task(
        project_id=project_id,
        task_id=task_id,
        status='done',
        completed_details='Task finished successfully'
    )

    # Verify status
    task_status = await taskqueue_client.get_task(project_id, task_id)
    assert task_status['status'] == 'done'

# ==================== REQUEST-REPLY PATTERN ====================

async def test_request_reply_pattern(redis_client):
    """Test request-reply coordination."""
    request_channel = "test:requests"
    reply_channel = "test:replies"

    # Subscriber (responder)
    async def responder():
        pubsub = await redis_client.subscribe(request_channel)
        msg = await pubsub.get_message()
        request_id = msg['data']

        # Send reply
        await redis_client.publish(reply_channel, f"reply-{request_id}")

    # Start responder
    responder_task = asyncio.create_task(responder())

    # Requester
    request_id = "req-12345"
    reply_sub = await redis_client.subscribe(reply_channel)

    # Send request
    await redis_client.publish(request_channel, request_id)

    # Wait for reply
    reply = await asyncio.wait_for(reply_sub.get_message(), timeout=5.0)

    assert reply['data'] == f"reply-{request_id}"
    await responder_task

# ==================== SCATTER-GATHER PATTERN ====================

async def test_scatter_gather_pattern(redis_client):
    """Test scatter-gather coordination."""
    scatter_channel = "test:scatter"
    gather_channel = "test:gather"

    num_workers = 5

    # Workers (process and reply)
    async def worker(worker_id: int):
        pubsub = await redis_client.subscribe(scatter_channel)
        msg = await pubsub.get_message()
        task_id = msg['data']

        # Simulate work
        await asyncio.sleep(0.1)

        # Send result
        await redis_client.publish(gather_channel, f"result-{worker_id}-{task_id}")

    # Start workers
    worker_tasks = [asyncio.create_task(worker(i)) for i in range(num_workers)]

    # Coordinator
    gather_sub = await redis_client.subscribe(gather_channel)

    # Scatter task
    task_id = "task-xyz"
    await redis_client.publish(scatter_channel, task_id)

    # Gather results
    results = []
    for _ in range(num_workers):
        result = await asyncio.wait_for(gather_sub.get_message(), timeout=10.0)
        results.append(result['data'])

    # Verify all workers responded
    assert len(results) == num_workers
    assert all(task_id in r for r in results)

    await asyncio.gather(*worker_tasks)

# ==================== BARRIER SYNCHRONIZATION ====================

async def test_barrier_synchronization(redis_client):
    """Test barrier synchronization pattern."""
    barrier_key = "test:barrier:sync"
    num_agents = 4

    # Agents wait at barrier
    async def agent(agent_id: int):
        # Increment barrier counter
        count = await redis_client.incr(barrier_key)

        # Wait until all agents reach barrier
        while True:
            current = await redis_client.get(barrier_key)
            if int(current) >= num_agents:
                break
            await asyncio.sleep(0.05)

        return agent_id

    # Run all agents
    results = await asyncio.gather(*[agent(i) for i in range(num_agents)])

    # All agents should complete
    assert len(results) == num_agents
    assert set(results) == set(range(num_agents))

# ==================== CIRCUIT BREAKER PATTERN ====================

async def test_circuit_breaker_pattern(redis_client):
    """Test circuit breaker for fault tolerance."""
    service_key = "test:circuit_breaker:failures"
    threshold = 3

    # Simulate service failures
    for _ in range(threshold):
        await redis_client.incr(service_key)

    failure_count = int(await redis_client.get(service_key))

    # Circuit should be open (too many failures)
    assert failure_count >= threshold

    # Reset after timeout
    await redis_client.delete(service_key)
    failure_count = await redis_client.get(service_key)

    # Circuit should be closed
    assert failure_count is None or int(failure_count) == 0