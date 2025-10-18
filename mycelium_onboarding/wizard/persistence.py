"""Wizard state persistence for resume functionality.

This module handles saving and loading wizard state to disk, enabling users
to resume the onboarding wizard if it's interrupted. Uses atomic writes to
prevent state corruption.
"""

from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from mycelium_onboarding.xdg_dirs import get_state_dir

if TYPE_CHECKING:
    from mycelium_onboarding.wizard.flow import WizardState

__all__ = [
    "WizardStatePersistence",
    "PersistenceError",
]

# Module logger
logger = logging.getLogger(__name__)


class PersistenceError(Exception):
    """Raised when state persistence operations fail."""

    pass


class WizardStatePersistence:
    """Manages saving and loading wizard state.

    This class provides atomic save/load operations for wizard state,
    enabling resume functionality. State is stored in XDG_STATE_HOME
    following the XDG Base Directory Specification.

    Attributes:
        state_dir: Directory where state files are stored
        state_file: Path to the wizard state file

    Example:
        >>> from mycelium_onboarding.wizard.flow import WizardState
        >>> persistence = WizardStatePersistence()
        >>> state = WizardState()
        >>> persistence.save(state)
        >>> loaded = persistence.load()
        >>> assert loaded is not None
    """

    def __init__(self, state_dir: Path | None = None) -> None:
        """Initialize persistence manager.

        Args:
            state_dir: Optional state directory (uses XDG_STATE_HOME if None)
        """
        self.state_dir = state_dir or get_state_dir()
        self.state_file = self.state_dir / "wizard_state.json"

    def save(self, state: WizardState) -> None:
        """Save wizard state to disk.

        Uses atomic write (write to temp file, then rename) to prevent
        corruption if the process is interrupted.

        Args:
            state: Wizard state to save

        Raises:
            PersistenceError: If save operation fails
        """
        try:
            # Ensure state directory exists
            self.state_dir.mkdir(parents=True, exist_ok=True)

            # Serialize state to dict
            state_dict = self._serialize_state(state)

            # Write atomically using temp file
            temp_file = self.state_file.with_suffix(".tmp")
            with open(temp_file, "w") as f:
                json.dump(state_dict, f, indent=2)

            # Atomic rename
            temp_file.rename(self.state_file)
            logger.info("Wizard state saved to %s", self.state_file)

        except (OSError, TypeError, ValueError) as e:
            logger.error("Failed to save wizard state: %s", e, exc_info=True)
            raise PersistenceError(f"Failed to save wizard state: {e}") from e

    def load(self) -> WizardState | None:
        """Load wizard state from disk.

        Returns:
            Loaded wizard state, or None if no saved state exists or
            if the state file is corrupted

        Example:
            >>> persistence = WizardStatePersistence()
            >>> state = persistence.load()
            >>> if state:
            ...     print(f"Resuming from step: {state.current_step}")
        """
        if not self.state_file.exists():
            logger.debug("No saved wizard state found")
            return None

        try:
            with open(self.state_file) as f:
                state_dict: dict[str, Any] = json.load(f)

            # Deserialize dict to WizardState
            state = self._deserialize_state(state_dict)
            logger.info("Wizard state loaded from %s", self.state_file)
            return state

        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
            logger.warning("Corrupted wizard state file: %s", e)
            return None

    def clear(self) -> None:
        """Clear saved wizard state.

        Removes the state file if it exists. Safe to call even if no
        state file exists.

        Example:
            >>> persistence = WizardStatePersistence()
            >>> persistence.clear()
            >>> assert not persistence.exists()
        """
        if self.state_file.exists():
            try:
                self.state_file.unlink()
                logger.info("Wizard state cleared: %s", self.state_file)
            except OSError as e:
                logger.error("Failed to clear wizard state: %s", e)
                raise PersistenceError(f"Failed to clear wizard state: {e}") from e

    def exists(self) -> bool:
        """Check if saved state exists.

        Returns:
            True if state file exists, False otherwise
        """
        return self.state_file.exists()

    def get_state_path(self) -> Path:
        """Get path to state file.

        Returns:
            Path to the wizard state file
        """
        return self.state_file

    def _serialize_state(self, state: WizardState) -> dict[str, Any]:
        """Serialize wizard state to dictionary.

        Args:
            state: Wizard state to serialize

        Returns:
            Dictionary representation of state
        """
        return {
            "current_step": state.current_step.value,
            "started_at": state.started_at.isoformat(),
            "project_name": state.project_name,
            "services_enabled": state.services_enabled,
            "deployment_method": state.deployment_method,
            "redis_port": state.redis_port,
            "postgres_port": state.postgres_port,
            "postgres_database": state.postgres_database,
            "temporal_namespace": state.temporal_namespace,
            "temporal_ui_port": state.temporal_ui_port,
            "temporal_frontend_port": state.temporal_frontend_port,
            "auto_start": state.auto_start,
            "enable_persistence": state.enable_persistence,
            "setup_mode": state.setup_mode,
            "completed": state.completed,
            "resumed": state.resumed,
            # Note: detection_results not persisted (should re-run on resume)
        }

    def _deserialize_state(self, state_dict: dict[str, Any]) -> WizardState:
        """Deserialize wizard state from dictionary.

        Args:
            state_dict: Dictionary containing state data

        Returns:
            Deserialized wizard state

        Raises:
            ValueError: If state data is invalid
        """
        # Import here to avoid circular dependency
        from mycelium_onboarding.wizard.flow import WizardState, WizardStep

        # Validate required fields
        if "current_step" not in state_dict:
            raise ValueError("Missing required field: current_step")

        try:
            # Extract and validate services_enabled
            services_raw = state_dict.get("services_enabled", {})
            if not isinstance(services_raw, dict):
                raise ValueError("services_enabled must be a dictionary")
            services_enabled = cast(dict[str, bool], services_raw)

            # Build WizardState with type-safe conversions
            state = WizardState(
                current_step=WizardStep(str(state_dict["current_step"])),
                started_at=datetime.fromisoformat(
                    str(state_dict.get("started_at", datetime.now().isoformat()))
                ),
                project_name=str(state_dict.get("project_name", "")),
                services_enabled=services_enabled,
                deployment_method=str(
                    state_dict.get("deployment_method", "docker-compose")
                ),
                redis_port=int(state_dict.get("redis_port", 6379) or 6379),
                postgres_port=int(state_dict.get("postgres_port", 5432) or 5432),
                postgres_database=str(state_dict.get("postgres_database", "")),
                temporal_namespace=str(
                    state_dict.get("temporal_namespace", "default")
                ),
                temporal_ui_port=int(state_dict.get("temporal_ui_port", 8080) or 8080),
                temporal_frontend_port=int(
                    state_dict.get("temporal_frontend_port", 7233) or 7233
                ),
                auto_start=bool(state_dict.get("auto_start", True)),
                enable_persistence=bool(state_dict.get("enable_persistence", True)),
                setup_mode=str(state_dict.get("setup_mode", "quick")),
                completed=bool(state_dict.get("completed", False)),
                resumed=True,  # Mark as resumed
            )
            return state

        except (ValueError, TypeError, KeyError) as e:
            raise ValueError(f"Invalid state data: {e}") from e

    def backup(self) -> Path | None:
        """Create a backup of current state.

        Returns:
            Path to backup file, or None if no state exists

        Raises:
            PersistenceError: If backup operation fails
        """
        if not self.exists():
            return None

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.state_dir / f"wizard_state_backup_{timestamp}.json"

            # Copy current state to backup
            shutil.copy2(self.state_file, backup_file)
            logger.info("Wizard state backed up to %s", backup_file)
            return backup_file

        except OSError as e:
            logger.error("Failed to backup wizard state: %s", e)
            raise PersistenceError(f"Failed to backup wizard state: {e}") from e

    def restore_from_backup(self, backup_path: Path) -> None:
        """Restore state from a backup file.

        Args:
            backup_path: Path to backup file

        Raises:
            PersistenceError: If restore operation fails
            FileNotFoundError: If backup file doesn't exist
        """
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        try:
            # Ensure state directory exists
            self.state_dir.mkdir(parents=True, exist_ok=True)

            # Copy backup to state file
            shutil.copy2(backup_path, self.state_file)
            logger.info("Wizard state restored from %s", backup_path)

        except OSError as e:
            logger.error("Failed to restore wizard state: %s", e)
            raise PersistenceError(f"Failed to restore wizard state: {e}") from e
