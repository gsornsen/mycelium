#!/usr/bin/env node

/**
 * Mycelium Integration Test
 *
 * Tests coordination, pub/sub, and workflow functionality across all modes.
 */

import { createMyceliumClient } from '../../lib/index.js';
import { strict as assert } from 'assert';

async function testCoordination() {
  console.log('🍄 Testing Mycelium Coordination...\n');

  const mycelium = await createMyceliumClient();

  console.log(`✓ Initialized with mode: ${mycelium.mode}\n`);

  // Test 1: Store and retrieve agent status
  console.log('Test 1: Agent status coordination');
  await mycelium.coordination.storeAgentStatus('test-agent', {
    status: 'busy',
    active_tasks: [
      {
        task_id: 'test-task-1',
        title: 'Test Task',
        started_at: new Date().toISOString()
      }
    ],
    metrics: {
      workload_pct: 75,
      success_rate: 0.95
    }
  });

  const status = await mycelium.coordination.getAgentStatus('test-agent');
  assert(status !== null, 'Agent status should be stored');
  assert(status.status === 'busy', 'Agent status should be busy');
  assert(status.active_tasks.length === 1, 'Should have 1 active task');
  console.log('✓ Agent status stored and retrieved\n');

  // Test 2: List all agent statuses
  console.log('Test 2: List agent statuses');
  const statuses = await mycelium.coordination.listAgentStatuses();
  assert(statuses.length >= 1, 'Should have at least 1 agent status');
  console.log(`✓ Found ${statuses.length} agent status(es)\n`);

  // Test 3: Create and retrieve task
  console.log('Test 3: Task coordination');
  const taskId = await mycelium.coordination.createTask('task-123', {
    title: 'Test Task',
    description: 'A test task for Mycelium',
    assigned_agent: 'test-agent',
    priority: 'high'
  });

  const task = await mycelium.coordination.getTask(taskId);
  assert(task !== null, 'Task should be stored');
  assert(task.title === 'Test Task', 'Task title should match');
  console.log('✓ Task created and retrieved\n');

  // Test 4: Update task
  console.log('Test 4: Task update');
  await mycelium.coordination.updateTask(taskId, {
    status: 'in_progress',
    progress: 0.5
  });

  const updatedTask = await mycelium.coordination.getTask(taskId);
  assert(updatedTask.status === 'in_progress', 'Task status should be updated');
  assert(updatedTask.progress === 0.5, 'Task progress should be updated');
  console.log('✓ Task updated successfully\n');

  // Test 5: Pub/Sub (real-time in Redis, polling in others)
  console.log('Test 5: Pub/Sub messaging');
  let messageReceived = false;
  let receivedMessage = null;

  await mycelium.pubsub.subscribe('test-channel', (message) => {
    messageReceived = true;
    receivedMessage = message;
    console.log('✓ Message received:', message);
  });

  await mycelium.pubsub.publish('test-channel', {
    event: 'test',
    data: 'Hello from Mycelium!',
    timestamp: new Date().toISOString()
  });

  // Wait for message (polling modes need time)
  await sleep(2000);

  if (mycelium.mode === 'redis') {
    // Real-time mode should receive immediately
    assert(messageReceived, 'Message should be received in Redis mode');
  }

  console.log('✓ Pub/Sub tested\n');

  // Test 6: Workflow creation
  console.log('Test 6: Workflow orchestration');
  const workflowId = await mycelium.workflow.createWorkflow('test-workflow', {
    task: 'test',
    iterations: 10
  }, {
    metadata: {
      test: true,
      created_by: 'integration-test'
    }
  });

  const workflow = await mycelium.workflow.getWorkflow(workflowId);
  assert(workflow !== null, 'Workflow should be created');
  assert(workflow.workflow_type === 'test-workflow', 'Workflow type should match');
  console.log('✓ Workflow created\n');

  // Test 7: Workflow execution
  console.log('Test 7: Workflow execution');
  await mycelium.workflow.startWorkflow(workflowId);

  const runningWorkflow = await mycelium.workflow.getWorkflow(workflowId);
  assert(runningWorkflow.status === 'running', 'Workflow should be running');

  await mycelium.workflow.addWorkflowStep(workflowId, {
    agent: 'test-agent',
    action: 'process',
    status: 'completed'
  });

  await mycelium.workflow.completeWorkflow(workflowId, {
    success: true,
    result: 'Test completed'
  });

  const completedWorkflow = await mycelium.workflow.getWorkflow(workflowId);
  assert(completedWorkflow.status === 'completed', 'Workflow should be completed');
  assert(completedWorkflow.steps.length === 1, 'Should have 1 step');
  console.log('✓ Workflow executed successfully\n');

  // Cleanup
  await mycelium.pubsub.cleanup();

  console.log('==========================================');
  console.log('🍄 All Mycelium tests passed!');
  console.log(`   Coordination mode: ${mycelium.mode}`);
  console.log('==========================================\n');

  return true;
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Run tests
testCoordination()
  .then(() => {
    console.log('✓ Integration tests completed successfully');
    process.exit(0);
  })
  .catch((error) => {
    console.error('✗ Integration tests failed:', error);
    process.exit(1);
  });
