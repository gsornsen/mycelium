"""Tests for MCP execution tools.

This module tests the AgentDiscoveryTools class, including:
- invoke_agent with consent integration
- get_workflow_status with workflow state management
- Agent discovery and metadata retrieval
"""

from unittest.mock import MagicMock, patch

import pytest

from mycelium.mcp.tools import AgentDiscoveryTools


class TestAgentDiscoveryToolsBasics:
    """Test basic discovery and metadata operations."""

    @pytest.fixture
    def mock_plugin_dir(self, tmp_path):
        """Create a mock plugin directory with test agents."""
        plugin_dir = tmp_path / "plugins" / "mycelium-core" / "agents"
        plugin_dir.mkdir(parents=True)

        # Create test agent files
        agent1 = plugin_dir / "01-core-backend-developer.md"
        agent1.write_text("""---
name: backend-developer
category: core
description: Backend development expert
tools: Read, Write, Bash
---

# Backend Developer Agent
""")

        agent2 = plugin_dir / "02-language-python-pro.md"
        agent2.write_text("""---
name: python-pro
category: language
description: Python programming specialist
tools: Read, Write
---

# Python Pro Agent
""")

        return plugin_dir

    @pytest.fixture
    def tools(self, mock_plugin_dir):
        """Create AgentDiscoveryTools instance with mock plugin dir."""
        return AgentDiscoveryTools(plugin_dir=mock_plugin_dir)

    def test_init_default_plugin_dir(self):
        """Test initialization with default plugin directory."""
        tools = AgentDiscoveryTools()
        assert tools.loader is not None
        assert tools.loader.plugin_dir.name == "agents"

    def test_init_custom_plugin_dir(self, mock_plugin_dir):
        """Test initialization with custom plugin directory."""
        tools = AgentDiscoveryTools(plugin_dir=mock_plugin_dir)
        assert tools.loader.plugin_dir == mock_plugin_dir

    def test_discover_agents_by_name(self, tools):
        """Test discovering agents by name."""
        results = tools.discover_agents("backend")

        assert len(results) > 0
        assert any(agent["name"] == "backend-developer" for agent in results)

    def test_discover_agents_by_description(self, tools):
        """Test discovering agents by description."""
        results = tools.discover_agents("Python")

        assert len(results) > 0
        assert any(agent["name"] == "python-pro" for agent in results)

    def test_discover_agents_by_category(self, tools):
        """Test discovering agents by category."""
        results = tools.discover_agents("core")

        assert len(results) > 0
        assert any(agent["category"] == "core" for agent in results)

    def test_discover_agents_by_tools(self, tools):
        """Test discovering agents by tools."""
        results = tools.discover_agents("Bash")

        assert len(results) > 0
        assert any(agent["name"] == "backend-developer" for agent in results)

    def test_discover_agents_no_match(self, tools):
        """Test discovering agents with no matches."""
        results = tools.discover_agents("nonexistent-feature")
        assert len(results) == 0

    def test_discover_agents_case_insensitive(self, tools):
        """Test that discovery is case-insensitive."""
        results1 = tools.discover_agents("PYTHON")
        results2 = tools.discover_agents("python")

        assert len(results1) == len(results2)

    def test_get_agent_details_valid(self, tools):
        """Test getting details for valid agent."""
        details = tools.get_agent_details("backend-developer")

        assert details is not None
        assert details["name"] == "backend-developer"
        assert details["category"] == "core"
        assert "description" in details
        assert "tools" in details
        assert isinstance(details["tools"], list)

    def test_get_agent_details_not_found(self, tools):
        """Test getting details for non-existent agent."""
        details = tools.get_agent_details("nonexistent-agent")
        assert details is None

    def test_list_categories(self, tools):
        """Test listing all categories."""
        categories = tools.list_categories()

        assert len(categories) > 0
        assert all("category" in cat for cat in categories)
        assert all("count" in cat for cat in categories)

        # Verify our test categories are present
        category_names = {cat["category"] for cat in categories}
        assert "core" in category_names
        assert "language" in category_names

    def test_list_categories_sorted(self, tools):
        """Test that categories are sorted."""
        categories = tools.list_categories()
        category_names = [cat["category"] for cat in categories]

        assert category_names == sorted(category_names)


class TestInvokeAgent:
    """Test agent invocation with consent and workflow management."""

    @pytest.fixture
    def mock_plugin_dir(self, tmp_path):
        """Create mock plugin directory with agents."""
        plugin_dir = tmp_path / "plugins" / "mycelium-core" / "agents"
        plugin_dir.mkdir(parents=True)

        # High-risk agent
        high_risk = plugin_dir / "01-core-high-risk-agent.md"
        high_risk.write_text("""---
name: high-risk-agent
category: core
description: High risk agent with unrestricted access
tools: Bash(*), Write(*)
---

# High Risk Agent
""")

        # Low-risk agent
        low_risk = plugin_dir / "02-core-low-risk-agent.md"
        low_risk.write_text("""---
name: low-risk-agent
category: core
description: Low risk agent with restricted access
tools: Read
---

# Low Risk Agent
""")

        return plugin_dir

    @pytest.fixture
    def tools(self, mock_plugin_dir):
        """Create tools instance with mocked dependencies."""
        return AgentDiscoveryTools(plugin_dir=mock_plugin_dir)

    @pytest.fixture
    def mock_process_manager(self):
        """Create mock ProcessManager."""
        manager = MagicMock()
        manager.start_agent.return_value = 12345  # Mock PID
        manager.get_process_status.return_value = {"status": "running", "pid": 12345}
        return manager

    @pytest.fixture
    def mock_registry_client(self):
        """Create mock RegistryClient."""
        client = MagicMock()
        client._redis_store_hash.return_value = None
        client._redis_get_hash.return_value = {}
        return client

    def test_invoke_agent_not_found(self, tools):
        """Test invoking non-existent agent."""
        result = tools.invoke_agent(agent_name="nonexistent-agent", task_description="Do something")

        assert result["status"] == "failed"
        assert result["workflow_id"] is None
        assert result["error"] == "AGENT_NOT_FOUND"
        assert "not found" in result["message"].lower()

    @patch("mycelium.mcp.tools.AgentDiscoveryTools._get_process_manager")
    @patch("mycelium.mcp.tools.AgentDiscoveryTools._get_registry_client")
    def test_invoke_agent_success_low_risk(
        self, mock_get_registry, mock_get_process, tools, mock_process_manager, mock_registry_client
    ):
        """Test successfully invoking low-risk agent."""
        mock_get_process.return_value = mock_process_manager
        mock_get_registry.return_value = mock_registry_client

        result = tools.invoke_agent(agent_name="low-risk-agent", task_description="Test task")

        assert result["status"] == "started"
        assert result["workflow_id"] is not None
        assert result["workflow_id"].startswith("wf_")
        assert result["agent_name"] == "low-risk-agent"
        assert result["pid"] == 12345
        assert "risk_level" in result

    @patch("builtins.input")
    @patch("mycelium.mcp.tools.AgentDiscoveryTools._get_process_manager")
    @patch("mycelium.mcp.tools.AgentDiscoveryTools._get_registry_client")
    def test_invoke_agent_high_risk_consent_granted(
        self, mock_get_registry, mock_get_process, mock_input, tools, mock_process_manager, mock_registry_client
    ):
        """Test invoking high-risk agent with consent granted."""
        mock_input.return_value = "yes"
        mock_get_process.return_value = mock_process_manager
        mock_get_registry.return_value = mock_registry_client

        result = tools.invoke_agent(agent_name="high-risk-agent", task_description="Test task")

        assert result["status"] == "started"
        assert result["workflow_id"] is not None
        assert result["risk_level"] == "high"

    @patch("mycelium.mcp.consent.ConsentManager")
    @patch("mycelium.mcp.tools.AgentDiscoveryTools._get_process_manager")
    @patch("mycelium.mcp.tools.AgentDiscoveryTools._get_registry_client")
    def test_invoke_agent_high_risk_consent_denied(
        self,
        mock_get_registry,
        mock_get_process,
        mock_consent_manager,
        tools,
        mock_process_manager,
        mock_registry_client,
    ):
        """Test invoking high-risk agent with consent denied."""
        # Mock consent manager to deny consent
        mock_consent_mgr = MagicMock()
        mock_consent_mgr.check_consent.return_value = False
        mock_consent_mgr.request_consent.return_value = False  # User denies
        mock_consent_manager.return_value = mock_consent_mgr

        mock_get_process.return_value = mock_process_manager
        mock_get_registry.return_value = mock_registry_client

        result = tools.invoke_agent(agent_name="high-risk-agent", task_description="Test task")

        assert result["status"] == "failed"
        assert result["workflow_id"] is None
        assert result["error"] == "CONSENT_DENIED"
        assert "denied consent" in result["message"].lower()

    @patch("mycelium.mcp.consent.ConsentManager")
    @patch("mycelium.mcp.tools.AgentDiscoveryTools._get_process_manager")
    @patch("mycelium.mcp.tools.AgentDiscoveryTools._get_registry_client")
    def test_invoke_agent_high_risk_with_existing_consent(
        self,
        mock_get_registry,
        mock_get_process,
        mock_consent_manager,
        tools,
        mock_process_manager,
        mock_registry_client,
    ):
        """Test invoking high-risk agent with pre-existing consent."""
        # Mock consent manager with existing consent
        mock_consent_mgr = MagicMock()
        mock_consent_mgr.check_consent.return_value = True  # Consent already exists
        mock_consent_manager.return_value = mock_consent_mgr

        mock_get_process.return_value = mock_process_manager
        mock_get_registry.return_value = mock_registry_client

        result = tools.invoke_agent(agent_name="high-risk-agent", task_description="Test task")

        # Should succeed without prompting (consent already exists)
        assert result["status"] == "started"
        # Should not have called request_consent since check_consent returned True
        mock_consent_mgr.request_consent.assert_not_called()

    @patch("mycelium.mcp.tools.AgentDiscoveryTools._get_process_manager")
    @patch("mycelium.mcp.tools.AgentDiscoveryTools._get_registry_client")
    def test_invoke_agent_process_start_failure(self, mock_get_registry, mock_get_process, tools, mock_registry_client):
        """Test agent invocation when process fails to start."""
        # Mock ProcessManager to raise exception
        mock_process_manager = MagicMock()
        mock_process_manager.start_agent.side_effect = Exception("Failed to start")

        mock_get_process.return_value = mock_process_manager
        mock_get_registry.return_value = mock_registry_client

        result = tools.invoke_agent(agent_name="low-risk-agent", task_description="Test task")

        assert result["status"] == "failed"
        assert "Failed to start" in result["message"]
        assert "error" in result

    @patch("mycelium.mcp.consent.ConsentManager")
    @patch("mycelium.mcp.tools.AgentDiscoveryTools._get_process_manager")
    @patch("mycelium.mcp.tools.AgentDiscoveryTools._get_registry_client")
    def test_invoke_agent_with_context(
        self,
        mock_get_registry,
        mock_get_process,
        mock_consent_manager,
        tools,
        mock_process_manager,
        mock_registry_client,
    ):
        """Test invoking agent with context data."""
        # Mock consent manager (low-risk agents may still be checked)
        mock_consent_mgr = MagicMock()
        mock_consent_mgr.check_consent.return_value = True
        mock_consent_manager.return_value = mock_consent_mgr

        mock_get_process.return_value = mock_process_manager
        mock_get_registry.return_value = mock_registry_client

        context = {"files": ["/path/to/file.py"], "data": {"key": "value"}}

        result = tools.invoke_agent(agent_name="low-risk-agent", task_description="Test task", _context=context)

        assert result["status"] == "started"

    @patch("mycelium.mcp.tools.AgentDiscoveryTools._get_process_manager")
    @patch("mycelium.mcp.tools.AgentDiscoveryTools._get_registry_client")
    def test_invoke_agent_workflow_id_format(
        self, mock_get_registry, mock_get_process, tools, mock_process_manager, mock_registry_client
    ):
        """Test that workflow IDs have correct format."""
        mock_get_process.return_value = mock_process_manager
        mock_get_registry.return_value = mock_registry_client

        result = tools.invoke_agent(agent_name="low-risk-agent", task_description="Test task")

        workflow_id = result["workflow_id"]
        assert workflow_id.startswith("wf_")
        # Should be wf_ + 12 hex chars
        assert len(workflow_id) == 15  # "wf_" + 12 chars


class TestGetWorkflowStatus:
    """Test workflow status retrieval."""

    @pytest.fixture
    def mock_plugin_dir(self, tmp_path):
        """Create mock plugin directory."""
        plugin_dir = tmp_path / "plugins" / "mycelium-core" / "agents"
        plugin_dir.mkdir(parents=True)

        agent = plugin_dir / "01-core-test-agent.md"
        agent.write_text("""---
name: test-agent
category: core
description: Test agent
tools: Read
---

# Test Agent
""")

        return plugin_dir

    @pytest.fixture
    def tools(self, mock_plugin_dir):
        """Create tools instance."""
        return AgentDiscoveryTools(plugin_dir=mock_plugin_dir)

    @pytest.fixture
    def mock_process_manager(self):
        """Create mock ProcessManager."""
        return MagicMock()

    @pytest.fixture
    def mock_registry_client(self):
        """Create mock RegistryClient."""
        return MagicMock()

    @patch("mycelium.mcp.tools.AgentDiscoveryTools._get_process_manager")
    @patch("mycelium.mcp.tools.AgentDiscoveryTools._get_registry_client")
    def test_get_workflow_status_not_found(
        self, mock_get_registry, mock_get_process, tools, mock_process_manager, mock_registry_client
    ):
        """Test getting status of non-existent workflow."""
        mock_registry_client._redis_get_hash.return_value = {}
        mock_get_registry.return_value = mock_registry_client
        mock_get_process.return_value = mock_process_manager

        result = tools.get_workflow_status("wf_nonexistent")

        assert result["status"] == "not_found"
        assert result["workflow_id"] == "wf_nonexistent"

    @patch("mycelium.mcp.tools.AgentDiscoveryTools._get_process_manager")
    @patch("mycelium.mcp.tools.AgentDiscoveryTools._get_registry_client")
    def test_get_workflow_status_running(
        self, mock_get_registry, mock_get_process, tools, mock_process_manager, mock_registry_client
    ):
        """Test getting status of running workflow."""
        workflow_data = {
            "workflow_id": "wf_test123",
            "agent_name": "test-agent",
            "task": "Test task",
            "status": "running",
            "started_at": "2025-01-01T00:00:00Z",
        }

        mock_registry_client._redis_get_hash.return_value = workflow_data
        mock_process_manager.get_process_status.return_value = {"status": "running", "pid": 12345}

        mock_get_registry.return_value = mock_registry_client
        mock_get_process.return_value = mock_process_manager

        result = tools.get_workflow_status("wf_test123")

        assert result["status"] == "running"
        assert result["workflow_id"] == "wf_test123"
        assert result["agent_name"] == "test-agent"
        assert result["started_at"] == "2025-01-01T00:00:00Z"

    @patch("mycelium.mcp.tools.AgentDiscoveryTools._get_process_manager")
    @patch("mycelium.mcp.tools.AgentDiscoveryTools._get_registry_client")
    def test_get_workflow_status_completed(
        self, mock_get_registry, mock_get_process, tools, mock_process_manager, mock_registry_client
    ):
        """Test getting status of completed workflow."""
        workflow_data = {
            "workflow_id": "wf_test123",
            "agent_name": "test-agent",
            "task": "Test task",
            "status": "running",
            "started_at": "2025-01-01T00:00:00Z",
        }

        mock_registry_client._redis_get_hash.return_value = workflow_data
        mock_process_manager.get_process_status.return_value = {"status": "stopped", "exit_code": 0}

        mock_get_registry.return_value = mock_registry_client
        mock_get_process.return_value = mock_process_manager

        result = tools.get_workflow_status("wf_test123")

        assert result["status"] == "completed"
        assert "completed_at" in result

    @patch("mycelium.mcp.tools.AgentDiscoveryTools._get_process_manager")
    @patch("mycelium.mcp.tools.AgentDiscoveryTools._get_registry_client")
    def test_get_workflow_status_failed(
        self, mock_get_registry, mock_get_process, tools, mock_process_manager, mock_registry_client
    ):
        """Test getting status of failed workflow."""
        workflow_data = {
            "workflow_id": "wf_test123",
            "agent_name": "test-agent",
            "task": "Test task",
            "status": "running",
            "started_at": "2025-01-01T00:00:00Z",
        }

        mock_registry_client._redis_get_hash.return_value = workflow_data
        mock_process_manager.get_process_status.return_value = {"status": "stopped", "exit_code": 1}

        mock_get_registry.return_value = mock_registry_client
        mock_get_process.return_value = mock_process_manager

        result = tools.get_workflow_status("wf_test123")

        assert result["status"] == "failed"
        assert "error" in result
        assert "exit_code" in result

    @patch("mycelium.mcp.tools.AgentDiscoveryTools._get_process_manager")
    @patch("mycelium.mcp.tools.AgentDiscoveryTools._get_registry_client")
    def test_get_workflow_status_error(
        self, mock_get_registry, mock_get_process, tools, mock_process_manager, mock_registry_client
    ):
        """Test getting workflow status when query fails."""
        mock_registry_client._redis_get_hash.side_effect = Exception("Redis error")
        mock_get_registry.return_value = mock_registry_client
        mock_get_process.return_value = mock_process_manager

        result = tools.get_workflow_status("wf_test123")

        assert result["status"] == "error"
        assert "error" in result
        assert "Redis error" in result["message"]


class TestLazyLoading:
    """Test lazy loading of dependencies."""

    @pytest.fixture
    def mock_plugin_dir(self, tmp_path):
        """Create minimal mock plugin directory."""
        plugin_dir = tmp_path / "plugins" / "mycelium-core" / "agents"
        plugin_dir.mkdir(parents=True)
        return plugin_dir

    def test_process_manager_lazy_load(self, mock_plugin_dir):
        """Test that ProcessManager is lazy-loaded."""
        tools = AgentDiscoveryTools(plugin_dir=mock_plugin_dir)

        # Should be None initially
        assert tools._process_manager is None

        # Should be loaded on first access - patch at import location inside function
        with patch("mycelium.supervisor.manager.ProcessManager") as mock_pm_class:
            mock_pm = MagicMock()
            mock_pm_class.return_value = mock_pm

            manager = tools._get_process_manager()
            # First call triggers import and instantiation
            assert tools._process_manager is not None

            # Should reuse cached instance
            manager2 = tools._get_process_manager()
            assert manager2 is manager

    def test_registry_client_lazy_load(self, mock_plugin_dir):
        """Test that RegistryClient is lazy-loaded."""
        tools = AgentDiscoveryTools(plugin_dir=mock_plugin_dir)

        # Should be None initially
        assert tools._registry_client is None

        # Should be loaded on first access - patch at import location inside function
        with patch("mycelium.registry.client.RegistryClient") as mock_rc_class:
            mock_rc = MagicMock()
            mock_rc_class.return_value = mock_rc

            client = tools._get_registry_client()
            # First call triggers import and instantiation
            assert tools._registry_client is not None

            # Should reuse cached instance
            client2 = tools._get_registry_client()
            assert client2 is client
