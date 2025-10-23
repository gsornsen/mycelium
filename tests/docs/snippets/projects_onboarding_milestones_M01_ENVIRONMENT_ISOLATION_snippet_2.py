# Source: projects/onboarding/milestones/M01_ENVIRONMENT_ISOLATION.md
# Line: 220
# Valid syntax: True
# Has imports: True
# Has assignments: True

# tests/test_xdg_dirs.py
import pytest
from pathlib import Path
import os

def test_get_config_dir_default(monkeypatch, tmp_path):
    """Test default config dir when XDG_CONFIG_HOME not set."""
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))

    config_dir = get_config_dir()

    assert config_dir == tmp_path / ".config" / "mycelium"
    assert config_dir.exists()


def test_get_config_dir_custom(monkeypatch, tmp_path):
    """Test custom config dir via XDG_CONFIG_HOME."""
    custom_config = tmp_path / "custom_config"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(custom_config))

    config_dir = get_config_dir()

    assert config_dir == custom_config / "mycelium"
    assert config_dir.exists()


def test_ensure_all_dirs(tmp_path, monkeypatch):
    """Test that all directories are created."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("MYCELIUM_ROOT", str(tmp_path / "project"))

    dirs = ensure_all_dirs()

    assert all(path.exists() for path in dirs.values())
    assert "config" in dirs
    assert "data" in dirs
    assert "cache" in dirs
    assert "state" in dirs
    assert "project" in dirs