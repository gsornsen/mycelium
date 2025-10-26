"""Wizard flow state machine for interactive onboarding.

This module implements the state machine for the Mycelium interactive wizard,
managing the flow between screens and maintaining user selections throughout
the onboarding process.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from mycelium_onboarding.config.schema import (
    DeploymentConfig,
    DeploymentMethod,
    MyceliumConfig,
    PostgresConfig,
    RedisConfig,
    ServicesConfig,
    TemporalConfig,
)

__all__ = [
    "WizardStep",
    "WizardState",
    "WizardFlow",
]


class WizardStep(str, Enum):
    """Wizard steps in order.

    The wizard follows a linear flow with optional skipping of ADVANCED
    step for Quick Setup mode.
    """

    WELCOME = "welcome"
    DETECTION = "detection"
    SERVICES = "services"
    DEPLOYMENT = "deployment"
    ADVANCED = "advanced"
    REVIEW = "review"
    COMPLETE = "complete"


@dataclass
class WizardState:
    """Complete wizard state with user selections.

    This dataclass maintains all state throughout the wizard flow, including
    detection results, user selections, and service-specific settings.

    Attributes:
        current_step: Current wizard step
        started_at: Timestamp when wizard was started
        detection_results: Results from M03 detection orchestrator
        project_name: User-specified project identifier
        services_enabled: Dict mapping service names to enabled status
        deployment_method: Chosen deployment method
        redis_port: Redis port configuration
        postgres_port: PostgreSQL port configuration
        postgres_database: PostgreSQL database name
        temporal_namespace: Temporal namespace configuration
        temporal_ui_port: Temporal UI port
        temporal_frontend_port: Temporal frontend/gRPC port
        auto_start: Whether to auto-start services
        enable_persistence: Whether to enable data persistence
        setup_mode: Quick or custom setup mode
        completed: Whether wizard is fully completed
        resumed: Whether this wizard was resumed from saved state
    """

    current_step: WizardStep = WizardStep.WELCOME
    started_at: datetime = field(default_factory=datetime.now)

    # Detection results (from M03)
    detection_results: dict[str, Any] | None = None

    # User selections
    project_name: str = ""
    services_enabled: dict[str, bool] = field(default_factory=dict)
    deployment_method: str = "docker-compose"

    # Service-specific settings
    redis_port: int = 6379
    postgres_port: int = 5432
    postgres_database: str = ""
    temporal_namespace: str = "default"
    temporal_ui_port: int = 8080
    temporal_frontend_port: int = 7233

    # Advanced settings
    auto_start: bool = True
    enable_persistence: bool = True

    # Wizard metadata
    setup_mode: str = "quick"  # "quick" or "custom"
    completed: bool = False
    resumed: bool = False

    def __post_init__(self) -> None:
        """Initialize default values after dataclass construction."""
        if not self.services_enabled:
            self.services_enabled = {
                "redis": True,
                "postgres": True,
                "temporal": True,
            }
        # Only set default project name if it's truly empty (not user-set)
        # This will be handled by the wizard screens instead
        if not self.postgres_database:
            self.postgres_database = self.project_name or "mycelium"

    def can_proceed_to(self, step: WizardStep) -> bool:
        """Check if can proceed to given step.

        Args:
            step: Target wizard step

        Returns:
            True if prerequisites are met, False otherwise
        """
        # Can always go to WELCOME
        if step == WizardStep.WELCOME:
            return True

        # DETECTION requires no special prerequisites
        if step == WizardStep.DETECTION:
            return True

        # SERVICES requires detection to have been run
        if step == WizardStep.SERVICES:
            return self.detection_results is not None

        # DEPLOYMENT requires project name and at least one service
        # but we're more lenient during navigation
        if step == WizardStep.DEPLOYMENT:
            return self.detection_results is not None

        # ADVANCED is same as DEPLOYMENT
        if step == WizardStep.ADVANCED:
            return self.detection_results is not None

        # REVIEW requires project name and at least one service
        if step == WizardStep.REVIEW:
            return bool(self.project_name) and any(self.services_enabled.values())

        # COMPLETE requires everything
        if step == WizardStep.COMPLETE:
            return self.completed

        # All other steps have no special requirements
        return True  # type: ignore[unreachable]

    def get_next_step(self) -> WizardStep | None:
        """Get next step in wizard flow.

        Returns:
            Next WizardStep, or None if at end
        """
        step_order = list(WizardStep)
        current_index = step_order.index(self.current_step)

        # Already at end
        if self.current_step == WizardStep.COMPLETE:
            return None

        next_index = current_index + 1

        # Skip ADVANCED step if in quick setup mode
        if self.setup_mode == "quick" and self.current_step == WizardStep.DEPLOYMENT:
            # Jump from DEPLOYMENT to REVIEW
            return WizardStep.REVIEW

        if next_index < len(step_order):
            return step_order[next_index]

        return None

    def get_previous_step(self) -> WizardStep | None:
        """Get previous step for back navigation.

        Returns:
            Previous WizardStep, or None if at beginning
        """
        # Cannot go back from WELCOME or COMPLETE
        if self.current_step in (WizardStep.WELCOME, WizardStep.COMPLETE):
            return None

        step_order = list(WizardStep)
        current_index = step_order.index(self.current_step)

        # Handle quick mode - skip ADVANCED when going back from REVIEW
        if self.setup_mode == "quick" and self.current_step == WizardStep.REVIEW:
            # Jump from REVIEW to DEPLOYMENT
            return WizardStep.DEPLOYMENT

        if current_index > 0:
            return step_order[current_index - 1]

        return None

    def is_complete(self) -> bool:
        """Check if wizard is complete.

        Returns:
            True if wizard has reached COMPLETE step and is marked completed
        """
        return self.current_step == WizardStep.COMPLETE and self.completed

    def _sanitize_db_name(self, name: str) -> str:
        """Sanitize a name for use as a PostgreSQL database name.

        Args:
            name: Name to sanitize

        Returns:
            Valid PostgreSQL database name
        """
        # Replace hyphens with underscores, remove invalid chars
        sanitized = name.replace("-", "_")
        # Remove any characters that aren't alphanumeric or underscore
        sanitized = "".join(c for c in sanitized if c.isalnum() or c == "_")
        # Ensure it starts with a letter
        if sanitized and not sanitized[0].isalpha():
            sanitized = "db_" + sanitized
        return sanitized or "mycelium"

    def to_config(self) -> MyceliumConfig:
        """Convert wizard state to MyceliumConfig.

        Returns:
            MyceliumConfig instance built from wizard state

        Raises:
            ValueError: If required fields are missing
        """
        # Use default if project name is still empty
        project_name = self.project_name or "mycelium"

        if not any(self.services_enabled.values()):
            raise ValueError("At least one service must be enabled")

        # Sanitize database name (PostgreSQL doesn't allow hyphens)
        db_name = self.postgres_database or project_name
        db_name = self._sanitize_db_name(db_name)

        # Build services configuration
        redis_config = RedisConfig(
            enabled=self.services_enabled.get("redis", False),
            port=self.redis_port,
            persistence=self.enable_persistence,
        )

        postgres_config = PostgresConfig(
            enabled=self.services_enabled.get("postgres", False),
            port=self.postgres_port,
            database=db_name,
        )

        temporal_config = TemporalConfig(
            enabled=self.services_enabled.get("temporal", False),
            ui_port=self.temporal_ui_port,
            frontend_port=self.temporal_frontend_port,
            namespace=self.temporal_namespace,
        )

        services = ServicesConfig(
            redis=redis_config,
            postgres=postgres_config,
            temporal=temporal_config,
        )

        # Build deployment configuration
        deployment = DeploymentConfig(
            method=DeploymentMethod(self.deployment_method),
            auto_start=self.auto_start,
        )

        # Create and return config
        return MyceliumConfig(
            project_name=project_name,
            services=services,
            deployment=deployment,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert wizard state to dictionary for serialization.

        Returns:
            Dictionary representation of wizard state
        """
        state_dict = asdict(self)
        # Convert datetime to ISO format string
        state_dict["started_at"] = self.started_at.isoformat()
        # Convert enums to values
        state_dict["current_step"] = self.current_step.value
        return state_dict

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WizardState:
        """Create wizard state from dictionary.

        Args:
            data: Dictionary containing wizard state data

        Returns:
            WizardState instance
        """
        # Convert ISO format string to datetime
        if isinstance(data.get("started_at"), str):
            data["started_at"] = datetime.fromisoformat(data["started_at"])

        # Convert string to enum
        if isinstance(data.get("current_step"), str):
            data["current_step"] = WizardStep(data["current_step"])

        return cls(**data)


class WizardFlow:
    """Manages wizard flow logic.

    This class orchestrates the wizard flow, handling step transitions,
    state persistence, and validation.

    Attributes:
        state: Current wizard state
    """

    def __init__(self, state: WizardState | None = None) -> None:
        """Initialize wizard flow.

        Args:
            state: Optional existing wizard state (creates new if None)
        """
        self.state = state or WizardState()

    def advance(self) -> WizardStep:
        """Advance to next step.

        Returns:
            Current step after advancement

        Raises:
            ValueError: If cannot advance (at end or prerequisites not met)
        """
        next_step = self.state.get_next_step()
        if next_step is None:
            raise ValueError("Cannot advance: already at final step")

        if not self.state.can_proceed_to(next_step):
            raise ValueError(f"Cannot advance: prerequisites not met for {next_step}")

        self.state.current_step = next_step
        return self.state.current_step

    def go_back(self) -> WizardStep:
        """Go back to previous step.

        Returns:
            Current step after going back

        Raises:
            ValueError: If cannot go back (at beginning)
        """
        prev_step = self.state.get_previous_step()
        if prev_step is None:
            raise ValueError("Cannot go back: at beginning of wizard")

        self.state.current_step = prev_step
        return self.state.current_step

    def jump_to(self, step: WizardStep) -> WizardStep:
        """Jump to a specific step.

        This is primarily used for navigation from the review screen.

        Args:
            step: Target step to jump to

        Returns:
            Current step after jump

        Raises:
            ValueError: If cannot jump to step
        """
        if not self.state.can_proceed_to(step):
            raise ValueError(f"Cannot jump to {step}: prerequisites not met")

        self.state.current_step = step
        return self.state.current_step

    def save_state(self, path: str | Path) -> None:
        """Save wizard state for resume capability.

        Args:
            path: File path to save state to
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        state_dict = self.state.to_dict()
        with path.open("w") as f:
            json.dump(state_dict, f, indent=2)

    @classmethod
    def load_state(cls, path: str | Path) -> WizardFlow:
        """Load saved wizard state.

        Args:
            path: File path to load state from

        Returns:
            WizardFlow instance with loaded state

        Raises:
            FileNotFoundError: If state file doesn't exist
            ValueError: If state file is invalid
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Wizard state file not found: {path}")

        with path.open() as f:
            state_dict = json.load(f)

        state = WizardState.from_dict(state_dict)
        state.resumed = True

        return cls(state=state)

    def mark_complete(self) -> None:
        """Mark wizard as completed.

        This should be called when the user confirms completion.
        """
        self.state.completed = True
        self.state.current_step = WizardStep.COMPLETE
