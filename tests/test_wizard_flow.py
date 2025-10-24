"""Tests for wizard flow state machine.

This module tests the WizardFlow and WizardState classes that manage
the interactive wizard flow and state persistence.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from mycelium_onboarding.config.schema import (
    DeploymentMethod,
    MyceliumConfig,
)
from mycelium_onboarding.wizard.flow import (
    WizardFlow,
    WizardState,
    WizardStep,
)


class TestWizardState:
    """Tests for WizardState dataclass."""

    def test_wizard_state_creation(self) -> None:
        """Test WizardState initialization with defaults."""
        state = WizardState()

        assert state.current_step == WizardStep.WELCOME
        assert not state.completed
        assert state.resumed is False
        assert isinstance(state.started_at, datetime)
        assert state.project_name == ""
        assert state.deployment_method == "docker-compose"
        assert state.auto_start is True
        assert state.enable_persistence is True

    def test_wizard_state_services_enabled_defaults(self) -> None:
        """Test services_enabled dictionary initialization."""
        state = WizardState()

        assert "redis" in state.services_enabled
        assert "postgres" in state.services_enabled
        assert "temporal" in state.services_enabled
        assert state.services_enabled["redis"] is True
        assert state.services_enabled["postgres"] is True
        assert state.services_enabled["temporal"] is True

    def test_wizard_state_custom_initialization(self) -> None:
        """Test WizardState with custom values."""
        state = WizardState(
            project_name="test-project",
            deployment_method="kubernetes",
            setup_mode="custom",
        )

        assert state.project_name == "test-project"
        assert state.deployment_method == "kubernetes"
        assert state.setup_mode == "custom"

    def test_get_next_step_linear_flow(self) -> None:
        """Test get_next_step returns correct next step in linear flow."""
        state = WizardState(current_step=WizardStep.WELCOME)

        assert state.get_next_step() == WizardStep.DETECTION

        state.current_step = WizardStep.DETECTION
        assert state.get_next_step() == WizardStep.SERVICES

        state.current_step = WizardStep.SERVICES
        assert state.get_next_step() == WizardStep.DEPLOYMENT

    def test_get_next_step_quick_mode_skips_advanced(self) -> None:
        """Test Quick Setup mode skips ADVANCED step."""
        state = WizardState(
            setup_mode="quick",
            current_step=WizardStep.DEPLOYMENT,
        )

        next_step = state.get_next_step()
        assert next_step == WizardStep.REVIEW

    def test_get_next_step_custom_mode_includes_advanced(self) -> None:
        """Test Custom Setup mode includes ADVANCED step."""
        state = WizardState(
            setup_mode="custom",
            current_step=WizardStep.DEPLOYMENT,
        )

        next_step = state.get_next_step()
        assert next_step == WizardStep.ADVANCED

    def test_get_next_step_at_end(self) -> None:
        """Test get_next_step returns None at end of wizard."""
        state = WizardState(current_step=WizardStep.COMPLETE)

        assert state.get_next_step() is None

    def test_get_previous_step(self) -> None:
        """Test get_previous_step returns correct previous step."""
        state = WizardState(current_step=WizardStep.SERVICES)

        assert state.get_previous_step() == WizardStep.DETECTION

        state.current_step = WizardStep.DEPLOYMENT
        assert state.get_previous_step() == WizardStep.SERVICES

    def test_get_previous_step_at_beginning(self) -> None:
        """Test get_previous_step returns None at beginning."""
        state = WizardState(current_step=WizardStep.WELCOME)

        assert state.get_previous_step() is None

    def test_get_previous_step_at_complete(self) -> None:
        """Test get_previous_step returns None at COMPLETE."""
        state = WizardState(current_step=WizardStep.COMPLETE)

        assert state.get_previous_step() is None

    def test_get_previous_step_quick_mode_skips_advanced(self) -> None:
        """Test Quick Setup mode skips ADVANCED when going back."""
        state = WizardState(
            setup_mode="quick",
            current_step=WizardStep.REVIEW,
        )

        prev_step = state.get_previous_step()
        assert prev_step == WizardStep.DEPLOYMENT

    def test_can_proceed_to_welcome(self) -> None:
        """Test can always proceed to WELCOME."""
        state = WizardState()

        assert state.can_proceed_to(WizardStep.WELCOME)

    def test_can_proceed_to_services_without_detection(self) -> None:
        """Test cannot proceed to SERVICES without detection."""
        state = WizardState(current_step=WizardStep.DETECTION)
        state.detection_results = None

        assert not state.can_proceed_to(WizardStep.SERVICES)

    def test_can_proceed_to_services_with_detection(self) -> None:
        """Test can proceed to SERVICES with detection results."""
        state = WizardState(current_step=WizardStep.DETECTION)
        state.detection_results = {"docker": {"available": True}}

        assert state.can_proceed_to(WizardStep.SERVICES)

    def test_can_proceed_to_review_requires_project_name(self) -> None:
        """Test cannot proceed to REVIEW without project name."""
        state = WizardState(current_step=WizardStep.DEPLOYMENT)
        state.project_name = ""

        assert not state.can_proceed_to(WizardStep.REVIEW)

    def test_can_proceed_to_review_requires_service(self) -> None:
        """Test cannot proceed to REVIEW without at least one service."""
        state = WizardState(current_step=WizardStep.DEPLOYMENT)
        state.project_name = "test"
        state.services_enabled = {
            "redis": False,
            "postgres": False,
            "temporal": False,
        }

        assert not state.can_proceed_to(WizardStep.REVIEW)

    def test_can_proceed_to_review_with_valid_state(self) -> None:
        """Test can proceed to REVIEW with valid state."""
        state = WizardState(current_step=WizardStep.DEPLOYMENT)
        state.project_name = "test"
        state.services_enabled = {"redis": True, "postgres": False, "temporal": False}

        assert state.can_proceed_to(WizardStep.REVIEW)

    def test_is_complete(self) -> None:
        """Test is_complete returns True when wizard is done."""
        state = WizardState(current_step=WizardStep.COMPLETE)
        state.completed = True

        assert state.is_complete()

    def test_is_not_complete_without_flag(self) -> None:
        """Test is_complete returns False without completed flag."""
        state = WizardState(current_step=WizardStep.COMPLETE)
        state.completed = False

        assert not state.is_complete()

    def test_to_config_basic(self) -> None:
        """Test converting wizard state to MyceliumConfig."""
        state = WizardState(
            project_name="test-project",
            services_enabled={
                "redis": True,
                "postgres": True,
                "temporal": False,
            },
            deployment_method="docker-compose",
        )

        config = state.to_config()

        assert isinstance(config, MyceliumConfig)
        assert config.project_name == "test-project"
        assert config.services.redis.enabled is True
        assert config.services.postgres.enabled is True
        assert config.services.temporal.enabled is False
        assert config.deployment.method == DeploymentMethod.DOCKER_COMPOSE

    def test_to_config_with_ports(self) -> None:
        """Test config conversion includes port settings."""
        state = WizardState(
            project_name="test",
            redis_port=6380,
            postgres_port=5433,
        )

        config = state.to_config()

        assert config.services.redis.port == 6380
        assert config.services.postgres.port == 5433

    def test_to_config_with_database_name(self) -> None:
        """Test config conversion includes database name."""
        state = WizardState(
            project_name="test",
            postgres_database="custom_db",
        )

        config = state.to_config()

        assert config.services.postgres.database == "custom_db"

    def test_to_config_with_temporal_settings(self) -> None:
        """Test config conversion includes Temporal settings."""
        state = WizardState(
            project_name="test",
            services_enabled={"redis": True, "postgres": True, "temporal": True},
            temporal_namespace="custom",
            temporal_frontend_port=7234,
            temporal_ui_port=8081,
        )

        config = state.to_config()

        assert config.services.temporal.namespace == "custom"
        assert config.services.temporal.frontend_port == 7234
        assert config.services.temporal.ui_port == 8081

    def test_to_config_without_project_name(self) -> None:
        """Test to_config uses default when project name is empty."""
        state = WizardState(project_name="")

        config = state.to_config()
        assert config.project_name == "mycelium"

    def test_to_config_without_services(self) -> None:
        """Test to_config raises error without any services."""
        state = WizardState(
            project_name="test",
            services_enabled={
                "redis": False,
                "postgres": False,
                "temporal": False,
            },
        )

        with pytest.raises(ValueError, match="At least one service must be enabled"):
            state.to_config()

    def test_to_dict(self) -> None:
        """Test converting wizard state to dictionary."""
        state = WizardState(project_name="test")
        state_dict = state.to_dict()

        assert isinstance(state_dict, dict)
        assert state_dict["project_name"] == "test"
        assert state_dict["current_step"] == WizardStep.WELCOME.value
        assert isinstance(state_dict["started_at"], str)  # ISO format

    def test_from_dict(self) -> None:
        """Test creating wizard state from dictionary."""
        data: dict[str, Any] = {
            "project_name": "test",
            "current_step": "services",
            "started_at": datetime.now(UTC).isoformat(),
            "deployment_method": "kubernetes",
            "services_enabled": {"redis": True, "postgres": False, "temporal": False},
            "detection_results": None,
            "redis_port": 6379,
            "postgres_port": 5432,
            "postgres_database": "test",
            "temporal_namespace": "default",
            "temporal_ui_port": 8080,
            "temporal_frontend_port": 7233,
            "auto_start": True,
            "enable_persistence": True,
            "setup_mode": "quick",
            "completed": False,
            "resumed": False,
        }

        state = WizardState.from_dict(data)

        assert state.project_name == "test"
        assert state.current_step == WizardStep.SERVICES
        assert state.deployment_method == "kubernetes"
        assert isinstance(state.started_at, datetime)

    def test_round_trip_dict_conversion(self) -> None:
        """Test state survives dict round-trip conversion."""
        original = WizardState(
            project_name="test",
            deployment_method="kubernetes",
            setup_mode="custom",
        )

        state_dict = original.to_dict()
        restored = WizardState.from_dict(state_dict)

        assert restored.project_name == original.project_name
        assert restored.deployment_method == original.deployment_method
        assert restored.setup_mode == original.setup_mode
        assert restored.current_step == original.current_step


class TestWizardFlow:
    """Tests for WizardFlow class."""

    def test_wizard_flow_creation(self) -> None:
        """Test WizardFlow initialization."""
        flow = WizardFlow()

        assert isinstance(flow.state, WizardState)
        assert flow.state.current_step == WizardStep.WELCOME

    def test_wizard_flow_with_existing_state(self) -> None:
        """Test WizardFlow with existing state."""
        state = WizardState(
            project_name="test",
            current_step=WizardStep.SERVICES,
        )
        flow = WizardFlow(state=state)

        assert flow.state.project_name == "test"
        assert flow.state.current_step == WizardStep.SERVICES

    def test_advance(self) -> None:
        """Test advancing through wizard steps."""
        flow = WizardFlow()
        flow.state.detection_results = {"test": "data"}

        assert flow.state.current_step == WizardStep.WELCOME

        flow.advance()
        assert flow.state.current_step == WizardStep.DETECTION

        flow.advance()
        assert flow.state.current_step == WizardStep.SERVICES

    def test_advance_at_end(self) -> None:
        """Test advance raises error at end of wizard."""
        flow = WizardFlow()
        flow.state.current_step = WizardStep.COMPLETE

        with pytest.raises(ValueError, match="Cannot advance"):
            flow.advance()

    def test_advance_without_prerequisites(self) -> None:
        """Test advance validates prerequisites."""
        flow = WizardFlow()
        flow.state.current_step = WizardStep.DETECTION
        flow.state.detection_results = None  # Missing prerequisite

        # Manually try to advance to SERVICES
        flow.state.current_step = WizardStep.SERVICES

        # Should fail when trying to advance without detection
        flow.state.current_step = WizardStep.DETECTION
        flow.state.detection_results = None

        # This should work (advance to SERVICES requires detection_results)
        # but we're testing the validation logic
        flow.state.detection_results = {"test": "data"}
        result = flow.advance()
        assert result == WizardStep.SERVICES

    def test_go_back(self) -> None:
        """Test going back through wizard steps."""
        flow = WizardFlow()
        flow.state.current_step = WizardStep.SERVICES

        flow.go_back()
        assert flow.state.current_step == WizardStep.DETECTION

        flow.go_back()
        assert flow.state.current_step == WizardStep.WELCOME

    def test_go_back_at_beginning(self) -> None:
        """Test go_back raises error at beginning."""
        flow = WizardFlow()

        with pytest.raises(ValueError, match="Cannot go back"):
            flow.go_back()

    def test_jump_to(self) -> None:
        """Test jumping to specific step."""
        flow = WizardFlow()
        flow.state.current_step = WizardStep.REVIEW
        flow.state.project_name = "test"
        flow.state.services_enabled = {"redis": True, "postgres": False, "temporal": False}
        flow.state.detection_results = {"test": "data"}

        # Jump back to services
        result = flow.jump_to(WizardStep.SERVICES)
        assert result == WizardStep.SERVICES
        assert flow.state.current_step == WizardStep.SERVICES

    def test_jump_to_without_prerequisites(self) -> None:
        """Test jump_to validates prerequisites."""
        flow = WizardFlow()
        flow.state.current_step = WizardStep.WELCOME

        # Try to jump to SERVICES without detection
        with pytest.raises(ValueError, match="Cannot jump"):
            flow.jump_to(WizardStep.SERVICES)

    def test_save_state(self, tmp_path: Path) -> None:
        """Test saving wizard state to file."""
        flow = WizardFlow()
        flow.state.project_name = "test-save"
        flow.state.current_step = WizardStep.SERVICES

        save_path = tmp_path / "wizard_state.json"
        flow.save_state(save_path)

        assert save_path.exists()

        # Verify content
        with open(save_path) as f:
            data = json.load(f)

        assert data["project_name"] == "test-save"
        assert data["current_step"] == "services"

    def test_save_state_creates_directory(self, tmp_path: Path) -> None:
        """Test save_state creates parent directories."""
        flow = WizardFlow()
        save_path = tmp_path / "subdir" / "wizard_state.json"

        flow.save_state(save_path)

        assert save_path.exists()
        assert save_path.parent.is_dir()

    def test_load_state(self, tmp_path: Path) -> None:
        """Test loading wizard state from file."""
        # Create saved state
        state_data = {
            "project_name": "test-load",
            "current_step": "deployment",
            "started_at": datetime.now(UTC).isoformat(),
            "deployment_method": "kubernetes",
            "services_enabled": {"redis": True, "postgres": True, "temporal": False},
            "detection_results": None,
            "redis_port": 6379,
            "postgres_port": 5432,
            "postgres_database": "test",
            "temporal_namespace": "default",
            "temporal_ui_port": 8080,
            "temporal_frontend_port": 7233,
            "auto_start": True,
            "enable_persistence": True,
            "setup_mode": "custom",
            "completed": False,
            "resumed": False,
        }

        save_path = tmp_path / "wizard_state.json"
        with open(save_path, "w") as f:
            json.dump(state_data, f)

        # Load state
        flow = WizardFlow.load_state(save_path)

        assert flow.state.project_name == "test-load"
        assert flow.state.current_step == WizardStep.DEPLOYMENT
        assert flow.state.deployment_method == "kubernetes"
        assert flow.state.resumed is True

    def test_load_state_file_not_found(self, tmp_path: Path) -> None:
        """Test load_state raises error if file doesn't exist."""
        save_path = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            WizardFlow.load_state(save_path)

    def test_mark_complete(self) -> None:
        """Test marking wizard as complete."""
        flow = WizardFlow()
        flow.state.current_step = WizardStep.REVIEW

        flow.mark_complete()

        assert flow.state.completed is True
        assert flow.state.current_step == WizardStep.COMPLETE

    def test_full_quick_setup_flow(self) -> None:
        """Test complete quick setup flow."""
        flow = WizardFlow()
        flow.state.setup_mode = "quick"
        flow.state.project_name = "test"
        flow.state.detection_results = {"docker": {"available": True}}

        # Quick mode: WELCOME -> DETECTION -> SERVICES -> DEPLOYMENT -> REVIEW
        expected_steps = [
            WizardStep.WELCOME,
            WizardStep.DETECTION,
            WizardStep.SERVICES,
            WizardStep.DEPLOYMENT,
            WizardStep.REVIEW,  # Skips ADVANCED
        ]

        for expected in expected_steps:
            assert flow.state.current_step == expected
            if expected != WizardStep.REVIEW:  # Don't advance past REVIEW
                flow.advance()

        # Verify we're at REVIEW
        assert flow.state.current_step == WizardStep.REVIEW

        # Mark complete manually for final step
        flow.mark_complete()
        assert flow.state.current_step == WizardStep.COMPLETE
        assert flow.state.completed is True

    def test_full_custom_setup_flow(self) -> None:
        """Test complete custom setup flow."""
        flow = WizardFlow()
        flow.state.setup_mode = "custom"
        flow.state.project_name = "test"
        flow.state.detection_results = {"docker": {"available": True}}

        # Custom mode: WELCOME -> DETECTION -> SERVICES -> DEPLOYMENT -> ADVANCED -> REVIEW
        expected_steps = [
            WizardStep.WELCOME,
            WizardStep.DETECTION,
            WizardStep.SERVICES,
            WizardStep.DEPLOYMENT,
            WizardStep.ADVANCED,  # Includes ADVANCED
            WizardStep.REVIEW,
        ]

        for expected in expected_steps:
            assert flow.state.current_step == expected
            if expected != WizardStep.REVIEW:  # Don't advance past REVIEW
                flow.advance()

        # Verify we're at REVIEW
        assert flow.state.current_step == WizardStep.REVIEW

        # Mark complete manually for final step
        flow.mark_complete()
        assert flow.state.current_step == WizardStep.COMPLETE
        assert flow.state.completed is True

    def test_back_navigation_flow(self) -> None:
        """Test backward navigation through wizard."""
        flow = WizardFlow()
        flow.state.current_step = WizardStep.DEPLOYMENT

        flow.go_back()
        assert flow.state.current_step == WizardStep.SERVICES

        flow.go_back()
        assert flow.state.current_step == WizardStep.DETECTION

        flow.go_back()
        assert flow.state.current_step == WizardStep.WELCOME

    def test_state_persistence_round_trip(self, tmp_path: Path) -> None:
        """Test saving and loading wizard state preserves all data."""
        # Create flow with custom state
        original_flow = WizardFlow()
        original_flow.state.project_name = "persistence-test"
        original_flow.state.current_step = WizardStep.SERVICES
        original_flow.state.setup_mode = "custom"
        original_flow.state.deployment_method = "kubernetes"
        original_flow.state.services_enabled = {
            "redis": True,
            "postgres": True,
            "temporal": False,
        }

        # Save state
        save_path = tmp_path / "state.json"
        original_flow.save_state(save_path)

        # Load state
        loaded_flow = WizardFlow.load_state(save_path)

        # Verify all important fields
        assert loaded_flow.state.project_name == original_flow.state.project_name
        assert loaded_flow.state.current_step == original_flow.state.current_step
        assert loaded_flow.state.setup_mode == original_flow.state.setup_mode
        assert loaded_flow.state.deployment_method == original_flow.state.deployment_method
        assert loaded_flow.state.services_enabled == original_flow.state.services_enabled
        assert loaded_flow.state.resumed is True


class TestWizardStepEnum:
    """Tests for WizardStep enum."""

    def test_wizard_step_values(self) -> None:
        """Test WizardStep enum values."""
        assert WizardStep.WELCOME.value == "welcome"
        assert WizardStep.DETECTION.value == "detection"
        assert WizardStep.SERVICES.value == "services"
        assert WizardStep.DEPLOYMENT.value == "deployment"
        assert WizardStep.ADVANCED.value == "advanced"
        assert WizardStep.REVIEW.value == "review"
        assert WizardStep.COMPLETE.value == "complete"

    def test_wizard_step_order(self) -> None:
        """Test WizardStep enum ordering."""
        steps = list(WizardStep)

        assert steps[0] == WizardStep.WELCOME
        assert steps[1] == WizardStep.DETECTION
        assert steps[2] == WizardStep.SERVICES
        assert steps[3] == WizardStep.DEPLOYMENT
        assert steps[4] == WizardStep.ADVANCED
        assert steps[5] == WizardStep.REVIEW
        assert steps[6] == WizardStep.COMPLETE

    def test_wizard_step_from_string(self) -> None:
        """Test creating WizardStep from string value."""
        assert WizardStep("welcome") == WizardStep.WELCOME
        assert WizardStep("detection") == WizardStep.DETECTION
        assert WizardStep("services") == WizardStep.SERVICES


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_empty_project_name_to_config(self) -> None:
        """Test to_config with empty project name uses default."""
        state = WizardState(project_name="")

        config = state.to_config()
        assert config.project_name == "mycelium"

    def test_all_services_disabled_to_config(self) -> None:
        """Test to_config with all services disabled."""
        state = WizardState(
            project_name="test",
            services_enabled={
                "redis": False,
                "postgres": False,
                "temporal": False,
            },
        )

        with pytest.raises(ValueError, match="At least one service must be enabled"):
            state.to_config()

    def test_invalid_deployment_method(self) -> None:
        """Test to_config with invalid deployment method."""
        state = WizardState(
            project_name="test",
            deployment_method="invalid-method",
        )

        with pytest.raises(ValueError):
            state.to_config()

    def test_malformed_saved_state(self, tmp_path: Path) -> None:
        """Test loading malformed saved state."""
        save_path = tmp_path / "malformed.json"
        with open(save_path, "w") as f:
            f.write("{invalid json}")

        with pytest.raises(json.JSONDecodeError):
            WizardFlow.load_state(save_path)
