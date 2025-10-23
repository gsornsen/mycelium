# Source: projects/onboarding/milestones/M03_SERVICE_DETECTION.md
# Line: 255
# Valid syntax: True
# Has imports: True
# Has assignments: True

# tests/test_docker_detection.py
from mycelium_onboarding.detection.docker import detect_docker


def test_detect_docker_available(monkeypatch):
    """Test detection when Docker is available."""
    # Mock docker command
    def mock_run(*args, **kwargs):
        command = args[0]
        if "--version" in command:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="Docker version 24.0.6, build ed223bc\n"
            )
        if "ps" in command:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout=""
            )
        return subprocess.CompletedProcess(args=command, returncode=1)

    monkeypatch.setattr("subprocess.run", mock_run)
    monkeypatch.setattr("shutil.which", lambda x: "/usr/bin/docker" if x == "docker" else None)

    info = detect_docker()

    assert info.available
    assert info.version == "24.0.6"
    assert info.running


def test_detect_docker_not_installed(monkeypatch):
    """Test detection when Docker is not installed."""
    monkeypatch.setattr("shutil.which", lambda x: None)

    info = detect_docker()

    assert not info.available
    assert "not found" in info.error.lower()
