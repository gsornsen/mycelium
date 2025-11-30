"""Unit tests for Mycelium configuration management."""

from pathlib import Path
from unittest.mock import patch

import pytest

from mycelium.config import AgentConfig, AgentLoader, ConfigManager, MyceliumConfig


# Helper to clear environment for tests
def clear_mycelium_env():
    """Return patch that clears all MYCELIUM_ and config-related env vars."""
    env_keys = [
        "MYCELIUM_REDIS_URL",
        "REDIS_URL",
        "MYCELIUM_DEV_SERVER_PORT",
        "DEV_SERVER_PORT",
        "MYCELIUM_API_PORT",
        "API_PORT",
        "MYCELIUM_AGENT_PORT_START",
        "AGENT_PORT_START",
        "MYCELIUM_PLUGIN_DIR",
        "PLUGIN_DIR",
        "MYCELIUM_LOG_DIR",
        "LOG_DIR",
        "MYCELIUM_AUTO_DISCOVER",
        "AUTO_DISCOVER",
        "MYCELIUM_LOG_LEVEL",
        "LOG_LEVEL",
    ]
    return patch.dict("os.environ", dict.fromkeys(env_keys, ""), clear=False)


class TestMyceliumConfig:
    """Test MyceliumConfig dataclass."""

    def test_default_values(self) -> None:
        """Test that default configuration values are set correctly."""
        config = MyceliumConfig()

        assert config.redis_url == "redis://localhost:6379"
        assert config.dev_server_port == 15850
        assert config.api_port == 15900
        assert config.agent_port_start == 17000
        assert config.auto_discover is True
        assert config.log_level == "INFO"
        assert isinstance(config.plugin_dir, Path)
        assert isinstance(config.log_dir, Path)

    def test_to_dict(self) -> None:
        """Test converting config to dictionary."""
        config = MyceliumConfig(
            redis_url="redis://example:6379",
            dev_server_port=9000,
        )

        config_dict = config.to_dict()

        assert config_dict["redis_url"] == "redis://example:6379"
        assert config_dict["dev_server_port"] == 9000
        assert isinstance(config_dict["plugin_dir"], str)
        assert isinstance(config_dict["log_dir"], str)

    def test_from_dict(self) -> None:
        """Test creating config from dictionary."""
        data = {
            "redis_url": "redis://test:6379",
            "dev_server_port": "8080",
            "auto_discover": "false",
            "plugin_dir": "/tmp/plugins",
        }

        config = MyceliumConfig.from_dict(data)

        assert config.redis_url == "redis://test:6379"
        assert config.dev_server_port == 8080
        assert config.auto_discover is False
        assert config.plugin_dir == Path("/tmp/plugins")


class TestConfigManager:
    """Test ConfigManager class."""

    def test_init_default(self) -> None:
        """Test ConfigManager initialization with default values."""
        manager = ConfigManager()

        assert manager.config_dir == Path.cwd()
        assert manager._config is None

    def test_init_custom_dir(self, tmp_path: Path) -> None:
        """Test ConfigManager initialization with custom directory."""
        manager = ConfigManager(config_dir=tmp_path)

        assert manager.config_dir == tmp_path

    @clear_mycelium_env()
    def test_load_defaults_only(self, tmp_path: Path) -> None:
        """Test loading with no .env files (defaults only)."""
        manager = ConfigManager(config_dir=tmp_path)
        config = manager.load()

        assert isinstance(config, MyceliumConfig)
        assert config.redis_url == "redis://localhost:6379"
        assert config.dev_server_port == 15850

    @clear_mycelium_env()
    def test_load_from_env_defaults(self, tmp_path: Path) -> None:
        """Test loading from .env.defaults file."""
        env_defaults = tmp_path / ".env.defaults"
        env_defaults.write_text("MYCELIUM_REDIS_URL=redis://custom:6379\nMYCELIUM_DEV_SERVER_PORT=9999\n")

        manager = ConfigManager(config_dir=tmp_path)
        config = manager.load()

        assert config.redis_url == "redis://custom:6379"
        assert config.dev_server_port == 9999

    @clear_mycelium_env()
    def test_load_from_env_local(self, tmp_path: Path) -> None:
        """Test loading from .env.local file."""
        env_local = tmp_path / ".env.local"
        env_local.write_text("MYCELIUM_API_PORT=8888\n")

        manager = ConfigManager(config_dir=tmp_path)
        config = manager.load()

        assert config.api_port == 8888

    @clear_mycelium_env()
    def test_load_hierarchy(self, tmp_path: Path) -> None:
        """Test that .env hierarchy is respected (later files override earlier)."""
        # Create .env.defaults
        env_defaults = tmp_path / ".env.defaults"
        env_defaults.write_text("MYCELIUM_REDIS_URL=redis://default:6379\nMYCELIUM_DEV_SERVER_PORT=15850\n")

        # Create .env that overrides redis_url
        env_file = tmp_path / ".env"
        env_file.write_text("MYCELIUM_REDIS_URL=redis://override:6379\n")

        # Create .env.local that overrides dev_server_port
        env_local = tmp_path / ".env.local"
        env_local.write_text("MYCELIUM_DEV_SERVER_PORT=9000\n")

        manager = ConfigManager(config_dir=tmp_path)
        config = manager.load()

        # redis_url should come from .env
        assert config.redis_url == "redis://override:6379"
        # dev_server_port should come from .env.local (highest priority)
        assert config.dev_server_port == 9000

    @clear_mycelium_env()
    def test_load_with_mode(self, tmp_path: Path) -> None:
        """Test loading mode-specific configuration."""
        # Create .env.production
        env_prod = tmp_path / ".env.production"
        env_prod.write_text("MYCELIUM_LOG_LEVEL=ERROR\nMYCELIUM_AUTO_DISCOVER=false\n")

        manager = ConfigManager(config_dir=tmp_path)
        config = manager.load(mode="production")

        assert config.log_level == "ERROR"
        assert config.auto_discover is False

    @patch.dict("os.environ", {"MYCELIUM_REDIS_URL": "redis://env:6379"}, clear=False)
    def test_load_from_environment(self, tmp_path: Path) -> None:
        """Test that environment variables override .env files."""
        # Create .env with different value
        env_file = tmp_path / ".env"
        env_file.write_text("MYCELIUM_REDIS_URL=redis://file:6379\n")

        manager = ConfigManager(config_dir=tmp_path)
        config = manager.load()

        # Environment variable should win
        assert config.redis_url == "redis://env:6379"

    @clear_mycelium_env()
    def test_validate_success(self, tmp_path: Path) -> None:
        """Test validation with valid configuration."""
        manager = ConfigManager(config_dir=tmp_path)
        manager.load()

        errors = manager.validate()

        assert errors == []

    @clear_mycelium_env()
    def test_validate_invalid_redis_url(self, tmp_path: Path) -> None:
        """Test validation catches invalid redis_url."""
        env_file = tmp_path / ".env"
        env_file.write_text("MYCELIUM_REDIS_URL=invalid://url\n")

        manager = ConfigManager(config_dir=tmp_path)
        manager.load()

        errors = manager.validate()

        assert len(errors) > 0
        assert any("redis_url" in error for error in errors)

    @clear_mycelium_env()
    def test_validate_invalid_port(self, tmp_path: Path) -> None:
        """Test validation catches invalid port numbers."""
        env_file = tmp_path / ".env"
        env_file.write_text("MYCELIUM_DEV_SERVER_PORT=99999\n")

        manager = ConfigManager(config_dir=tmp_path)
        manager.load()

        errors = manager.validate()

        assert len(errors) > 0
        assert any("dev_server_port" in error for error in errors)

    @clear_mycelium_env()
    def test_validate_invalid_log_level(self, tmp_path: Path) -> None:
        """Test validation catches invalid log level."""
        env_file = tmp_path / ".env"
        env_file.write_text("MYCELIUM_LOG_LEVEL=INVALID\n")

        manager = ConfigManager(config_dir=tmp_path)
        manager.load()

        errors = manager.validate()

        assert len(errors) > 0
        assert any("log_level" in error for error in errors)

    def test_validate_without_load(self, tmp_path: Path) -> None:
        """Test that validation fails if config not loaded."""
        manager = ConfigManager(config_dir=tmp_path)

        errors = manager.validate()

        assert len(errors) == 1
        assert "not loaded" in errors[0]

    @clear_mycelium_env()
    def test_to_dict(self, tmp_path: Path) -> None:
        """Test converting manager config to dictionary."""
        manager = ConfigManager(config_dir=tmp_path)
        manager.load()

        config_dict = manager.to_dict()

        assert isinstance(config_dict, dict)
        assert "redis_url" in config_dict
        assert isinstance(config_dict["plugin_dir"], str)

    def test_to_dict_without_load(self, tmp_path: Path) -> None:
        """Test that to_dict fails if config not loaded."""
        manager = ConfigManager(config_dir=tmp_path)

        with pytest.raises(RuntimeError, match="not loaded"):
            manager.to_dict()

    @clear_mycelium_env()
    def test_reload(self, tmp_path: Path) -> None:
        """Test reloading configuration."""
        env_file = tmp_path / ".env"
        env_file.write_text("MYCELIUM_REDIS_URL=redis://first:6379\n")

        manager = ConfigManager(config_dir=tmp_path)
        config1 = manager.load()

        # Update .env file
        env_file.write_text("MYCELIUM_REDIS_URL=redis://second:6379\n")

        config2 = manager.reload()

        assert config1.redis_url == "redis://first:6379"
        assert config2.redis_url == "redis://second:6379"

    @clear_mycelium_env()
    def test_get_success(self, tmp_path: Path) -> None:
        """Test getting current configuration."""
        manager = ConfigManager(config_dir=tmp_path)
        manager.load()

        config = manager.get()

        assert isinstance(config, MyceliumConfig)

    def test_get_without_load(self, tmp_path: Path) -> None:
        """Test that get fails if config not loaded."""
        manager = ConfigManager(config_dir=tmp_path)

        with pytest.raises(RuntimeError, match="not loaded"):
            manager.get()


class TestAgentConfig:
    """Test AgentConfig dataclass."""

    def test_from_file_valid(self, tmp_path: Path) -> None:
        """Test loading agent config from valid .md file."""
        agent_file = tmp_path / "01-core-backend-developer.md"
        content = """---
name: backend-developer
description: Senior backend engineer
tools: Read, Write, Bash
---

# Backend Developer

Content here...
"""
        agent_file.write_text(content)

        config = AgentConfig.from_file(agent_file)

        assert config.name == "backend-developer"
        assert config.category == "core"
        assert config.description == "Senior backend engineer"
        assert config.tools == ["Read", "Write", "Bash"]
        assert config.command == ["claude", "--agent", "backend-developer"]

    def test_from_file_no_name_uses_filename(self, tmp_path: Path) -> None:
        """Test that agent name is extracted from filename if not in frontmatter."""
        agent_file = tmp_path / "02-language-python-pro.md"
        content = """---
description: Python expert
---

# Python Pro
"""
        agent_file.write_text(content)

        config = AgentConfig.from_file(agent_file)

        assert config.name == "python-pro"
        assert config.category == "language"

    def test_from_file_missing(self, tmp_path: Path) -> None:
        """Test error when file doesn't exist."""
        agent_file = tmp_path / "nonexistent.md"

        with pytest.raises(ValueError, match="not found"):
            AgentConfig.from_file(agent_file)

    def test_from_file_no_frontmatter(self, tmp_path: Path) -> None:
        """Test error when no frontmatter found."""
        agent_file = tmp_path / "invalid.md"
        agent_file.write_text("# Just content, no frontmatter\n")

        with pytest.raises(ValueError, match="No frontmatter"):
            AgentConfig.from_file(agent_file)

    def test_clean_filename(self) -> None:
        """Test filename cleaning logic."""
        assert AgentConfig._clean_filename("01-core-backend-developer") == "backend-developer"
        assert AgentConfig._clean_filename("02-language-python-pro") == "python-pro"
        assert AgentConfig._clean_filename("03-specialized-data-engineer") == "data-engineer"
        assert AgentConfig._clean_filename("simple-name") == "simple-name"

    def test_extract_category(self) -> None:
        """Test category extraction from filename."""
        assert AgentConfig._extract_category("01-core-backend-developer") == "core"
        assert AgentConfig._extract_category("02-language-python-pro") == "language"
        assert AgentConfig._extract_category("03-specialized-data-engineer") == "specialized"
        assert AgentConfig._extract_category("simple-name") == "unknown"


class TestAgentLoader:
    """Test AgentLoader class."""

    def test_init(self, tmp_path: Path) -> None:
        """Test AgentLoader initialization."""
        loader = AgentLoader(tmp_path)

        assert loader.plugin_dir == tmp_path

    def test_load_agent_success(self, tmp_path: Path) -> None:
        """Test loading specific agent by name."""
        # Create agent file
        agent_file = tmp_path / "01-core-backend-developer.md"
        content = """---
name: backend-developer
description: Backend engineer
---
"""
        agent_file.write_text(content)

        loader = AgentLoader(tmp_path)
        config = loader.load_agent("backend-developer")

        assert config is not None
        assert config.name == "backend-developer"

    def test_load_agent_not_found(self, tmp_path: Path) -> None:
        """Test loading non-existent agent returns None."""
        loader = AgentLoader(tmp_path)
        config = loader.load_agent("nonexistent")

        assert config is None

    def test_load_agent_directory_not_exists(self, tmp_path: Path) -> None:
        """Test loading agent when directory doesn't exist."""
        nonexistent_dir = tmp_path / "nonexistent"
        loader = AgentLoader(nonexistent_dir)

        config = loader.load_agent("any-agent")

        assert config is None

    def test_list_agents(self, tmp_path: Path) -> None:
        """Test listing all agents."""
        # Create multiple agent files
        agent1 = tmp_path / "01-core-backend-developer.md"
        agent1.write_text("---\nname: backend-developer\ndescription: Backend\n---\n")

        agent2 = tmp_path / "02-language-python-pro.md"
        agent2.write_text("---\nname: python-pro\ndescription: Python\n---\n")

        loader = AgentLoader(tmp_path)
        agents = loader.list_agents()

        assert len(agents) == 2
        agent_names = {agent.name for agent in agents}
        assert "backend-developer" in agent_names
        assert "python-pro" in agent_names

    def test_list_agents_empty(self, tmp_path: Path) -> None:
        """Test listing agents in empty directory."""
        loader = AgentLoader(tmp_path)
        agents = loader.list_agents()

        assert agents == []

    def test_list_agents_skip_invalid(self, tmp_path: Path) -> None:
        """Test that invalid agent files are skipped."""
        # Create valid agent
        valid = tmp_path / "valid.md"
        valid.write_text("---\nname: valid\ndescription: Valid\n---\n")

        # Create invalid agent (no frontmatter)
        invalid = tmp_path / "invalid.md"
        invalid.write_text("# No frontmatter\n")

        loader = AgentLoader(tmp_path)
        agents = loader.list_agents()

        assert len(agents) == 1
        assert agents[0].name == "valid"

    def test_list_by_category(self, tmp_path: Path) -> None:
        """Test filtering agents by category."""
        # Create agents in different categories
        core1 = tmp_path / "01-core-backend.md"
        core1.write_text("---\nname: backend\ndescription: Backend\n---\n")

        core2 = tmp_path / "01-core-frontend.md"
        core2.write_text("---\nname: frontend\ndescription: Frontend\n---\n")

        lang1 = tmp_path / "02-language-python.md"
        lang1.write_text("---\nname: python\ndescription: Python\n---\n")

        loader = AgentLoader(tmp_path)
        core_agents = loader.list_by_category("core")
        lang_agents = loader.list_by_category("language")

        assert len(core_agents) == 2
        assert len(lang_agents) == 1
        assert all(agent.category == "core" for agent in core_agents)
        assert all(agent.category == "language" for agent in lang_agents)

    def test_get_categories(self, tmp_path: Path) -> None:
        """Test getting list of all categories."""
        # Create agents in different categories
        core = tmp_path / "01-core-backend.md"
        core.write_text("---\nname: backend\ndescription: Backend\n---\n")

        lang = tmp_path / "02-language-python.md"
        lang.write_text("---\nname: python\ndescription: Python\n---\n")

        specialized = tmp_path / "03-specialized-data.md"
        specialized.write_text("---\nname: data\ndescription: Data\n---\n")

        loader = AgentLoader(tmp_path)
        categories = loader.get_categories()

        assert len(categories) == 3
        assert "core" in categories
        assert "language" in categories
        assert "specialized" in categories
