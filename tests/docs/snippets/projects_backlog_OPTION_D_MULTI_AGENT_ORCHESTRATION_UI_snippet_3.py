# Source: projects/backlog/OPTION_D_MULTI_AGENT_ORCHESTRATION_UI.md
# Line: 1220
# Valid syntax: True
# Has imports: True
# Has assignments: True

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