"""Temporal version detection from Python project files.

This module provides robust detection of Temporal SDK versions from various
Python dependency specification files, including pyproject.toml, requirements.txt,
poetry.lock, setup.py, and setup.cfg.
"""

from __future__ import annotations

import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, parse

# Use tomllib for Python 3.11+, fallback to toml for earlier versions
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


@dataclass
class TemporalVersion:
    """Temporal SDK version information extracted from project files.

    Attributes:
        version: Detected version string (e.g., "1.5.0")
        source_file: Path to the file where version was detected
        is_exact: True if version is pinned (==), False if range/wildcard
        raw_spec: Original requirement specification string
        min_version: Minimum version if using range specifier
        max_version: Maximum version if using range specifier
    """

    version: str
    source_file: Path
    is_exact: bool
    raw_spec: str
    min_version: str | None = None
    max_version: str | None = None

    def __str__(self) -> str:
        """Return human-readable representation."""
        exactness = "pinned" if self.is_exact else "range"
        return f"Temporal {self.version} ({exactness}) from {self.source_file.name}"


class TemporalDetectionError(Exception):
    """Base exception for Temporal version detection errors."""

    pass


class NoTemporalDependencyError(TemporalDetectionError):
    """Raised when no Temporal dependency is found in project."""

    pass


class VersionParseError(TemporalDetectionError):
    """Raised when version string cannot be parsed."""

    pass


def detect_temporal_version(project_dir: Path) -> TemporalVersion | None:
    """Detect Temporal SDK version from project dependency files.

    Searches for Temporal dependency in order of preference:
    1. pyproject.toml (PEP 621 or Poetry format)
    2. requirements.txt
    3. poetry.lock
    4. setup.py
    5. setup.cfg

    Args:
        project_dir: Path to project root directory

    Returns:
        TemporalVersion object if detected, None if not found

    Raises:
        TemporalDetectionError: If detection fails due to file parsing errors
    """
    if not project_dir.is_dir():
        logger.error(f"Project directory does not exist: {project_dir}")
        return None

    # Define detection strategies in order of preference
    detection_strategies = [
        (_detect_from_pyproject_toml, "pyproject.toml"),
        (_detect_from_requirements_txt, "requirements.txt"),
        (_detect_from_poetry_lock, "poetry.lock"),
        (_detect_from_setup_py, "setup.py"),
        (_detect_from_setup_cfg, "setup.cfg"),
    ]

    for detector_func, filename in detection_strategies:
        file_path = project_dir / filename
        if file_path.exists():
            logger.debug(f"Attempting to detect Temporal version from {file_path}")
            try:
                version = detector_func(file_path)
                if version:
                    logger.info(f"Detected Temporal version: {version}")
                    return version
            except Exception as e:
                logger.warning(f"Error parsing {filename}: {e}")
                continue

    logger.info("No Temporal dependency found in project")
    return None


def _detect_from_pyproject_toml(file_path: Path) -> TemporalVersion | None:
    """Detect Temporal version from pyproject.toml.

    Supports both PEP 621 format and Poetry format:
    - [project.dependencies]
    - [tool.poetry.dependencies]

    Args:
        file_path: Path to pyproject.toml

    Returns:
        TemporalVersion if found, None otherwise
    """
    if tomllib is None:
        logger.warning("tomllib/tomli not available, cannot parse pyproject.toml")
        return None

    try:
        with open(file_path, "rb") as f:
            data = tomllib.load(f)
    except Exception as e:
        raise TemporalDetectionError(f"Failed to parse pyproject.toml: {e}") from e

    # Try PEP 621 format first
    if "project" in data and "dependencies" in data["project"]:
        for dep in data["project"]["dependencies"]:
            if isinstance(dep, str) and dep.strip().lower().startswith("temporalio"):
                return _parse_requirement_string(dep, file_path)

    # Try Poetry format
    if "tool" in data and "poetry" in data["tool"] and "dependencies" in data["tool"]["poetry"]:
        poetry_deps = data["tool"]["poetry"]["dependencies"]
        if "temporalio" in poetry_deps:
            version_spec = poetry_deps["temporalio"]
            if isinstance(version_spec, str):
                # Poetry uses caret (^) and tilde (~) notation
                raw_spec = (
                    f"temporalio{version_spec}"
                    if not version_spec.startswith("^~")
                    else f"temporalio>={version_spec[1:]}"
                )
                return _parse_requirement_string(raw_spec, file_path)
            if isinstance(version_spec, dict):
                # Poetry dict format: {version = "^1.5.0", extras = ["opentelemetry"]}
                if "version" in version_spec:
                    version_str = version_spec["version"]
                    raw_spec = (
                        f"temporalio{version_str}"
                        if not version_str.startswith("^~")
                        else f"temporalio>={version_str[1:]}"
                    )
                    return _parse_requirement_string(raw_spec, file_path)

    return None


def _detect_from_requirements_txt(file_path: Path) -> TemporalVersion | None:
    """Detect Temporal version from requirements.txt.

    Handles various requirement formats:
    - temporalio==1.5.0
    - temporalio>=1.4.0,<2.0.0
    - temporalio~=1.5
    - temporalio @ git+https://...

    Args:
        file_path: Path to requirements.txt

    Returns:
        TemporalVersion if found, None otherwise
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        raise TemporalDetectionError(f"Failed to read requirements.txt: {e}") from e

    for line in content.splitlines():
        line = line.strip()
        # Skip comments and empty lines
        if not line or line.startswith("#"):
            continue
        # Skip -r/-e flags
        if line.startswith("-r ") or line.startswith("-e "):
            continue

        if line.lower().startswith("temporalio"):
            return _parse_requirement_string(line, file_path)

    return None


def _detect_from_poetry_lock(file_path: Path) -> TemporalVersion | None:
    """Detect Temporal version from poetry.lock.

    Poetry lock files contain exact installed versions.

    Args:
        file_path: Path to poetry.lock

    Returns:
        TemporalVersion if found, None otherwise
    """
    if tomllib is None:
        logger.warning("tomllib/tomli not available, cannot parse poetry.lock")
        return None

    try:
        with open(file_path, "rb") as f:
            data = tomllib.load(f)
    except Exception as e:
        raise TemporalDetectionError(f"Failed to parse poetry.lock: {e}") from e

    # Find temporalio package in lock file
    if "package" in data:
        for package in data["package"]:
            if isinstance(package, dict) and package.get("name", "").lower() == "temporalio":
                version = package.get("version", "")
                if version:
                    return TemporalVersion(
                        version=version,
                        source_file=file_path,
                        is_exact=True,
                        raw_spec=f"temporalio=={version}",
                        min_version=version,
                        max_version=version,
                    )

    return None


def _detect_from_setup_py(file_path: Path) -> TemporalVersion | None:
    """Detect Temporal version from setup.py.

    Attempts to extract install_requires or setup_requires.
    Note: This is basic regex-based extraction, not AST parsing.

    Args:
        file_path: Path to setup.py

    Returns:
        TemporalVersion if found, None otherwise
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        raise TemporalDetectionError(f"Failed to read setup.py: {e}") from e

    # Look for install_requires or setup_requires with temporalio
    # Match patterns like: "temporalio>=1.5.0" or 'temporalio==1.5.0'
    pattern = r'["\']temporalio[^"\']*["\']'
    matches = re.findall(pattern, content, re.IGNORECASE)

    for match in matches:
        # Remove quotes
        requirement = match.strip('"').strip("'")
        if requirement.lower().startswith("temporalio"):
            return _parse_requirement_string(requirement, file_path)

    return None


def _detect_from_setup_cfg(file_path: Path) -> TemporalVersion | None:
    """Detect Temporal version from setup.cfg.

    Parses setup.cfg INI format for install_requires.

    Args:
        file_path: Path to setup.cfg

    Returns:
        TemporalVersion if found, None otherwise
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        raise TemporalDetectionError(f"Failed to read setup.cfg: {e}") from e

    # Simple INI parsing for install_requires section
    # BUG FIX: Don't strip lines before checking indentation
    in_install_requires = False
    for line in content.splitlines():
        # Check if we're entering install_requires section
        if line.strip().startswith("install_requires"):
            in_install_requires = True
            continue

        # Check if we've left install_requires section
        # A new section starts with a non-indented line containing '='
        if in_install_requires and line and not line.startswith((" ", "\t")) and "=" in line:
            in_install_requires = False

        # Parse requirement lines in install_requires
        # Strip AFTER determining if we're in the right section
        stripped_line = line.strip()
        if in_install_requires and stripped_line and not stripped_line.startswith("#"):
            if stripped_line.lower().startswith("temporalio"):
                return _parse_requirement_string(stripped_line, file_path)

    return None


def _parse_requirement_string(requirement: str, source_file: Path) -> TemporalVersion | None:
    """Parse a requirement string to extract version information.

    Handles various formats:
    - temporalio==1.5.0 (exact)
    - temporalio>=1.4.0,<2.0.0 (range)
    - temporalio~=1.5 (compatible release)
    - temporalio^1.5.0 (Poetry caret)
    - temporalio @ git+https://... (git dependency)

    Args:
        requirement: Requirement string (e.g., "temporalio>=1.5.0")
        source_file: Path to source file for context

    Returns:
        TemporalVersion if parseable, None otherwise
    """
    requirement = requirement.strip()

    # Handle git dependencies
    if " @ git+" in requirement or "@git+" in requirement:
        # Extract version from git URL if present (e.g., @v1.5.0)
        git_version_match = re.search(r"@v?(\d+\.\d+(?:\.\d+)?)", requirement)
        if git_version_match:
            version = git_version_match.group(1)
            return TemporalVersion(
                version=version,
                source_file=source_file,
                is_exact=False,
                raw_spec=requirement,
                min_version=version,
                max_version=None,
            )
        # Cannot determine version from git URL
        logger.warning(f"Cannot extract version from git dependency: {requirement}")
        return None

    # Extract package name and version specifier
    # Handle extras: temporalio[opentelemetry]>=1.5.0
    match = re.match(r"^(temporalio)(?:\[[^\]]+\])?(.*)", requirement, re.IGNORECASE)
    if not match:
        return None

    package_name, version_spec = match.groups()
    version_spec = version_spec.strip()

    if not version_spec:
        # No version specified
        logger.warning(f"No version specifier found in: {requirement}")
        return None

    # BUG FIX: Check for PEP 440 compatible release (~=) BEFORE Poetry tilde (~)
    # Handle Poetry caret (^) and tilde (~) notation
    if version_spec.startswith("^"):
        # ^1.5.0 means >=1.5.0,<2.0.0
        base_version = version_spec[1:].strip()
        return _create_version_from_poetry_caret(base_version, requirement, source_file)
    if version_spec.startswith("~") and not version_spec.startswith("~="):
        # ~1.5 means >=1.5,<1.6 (Poetry tilde notation, NOT PEP 440 ~=)
        base_version = version_spec[1:].strip()
        return _create_version_from_poetry_tilde(base_version, requirement, source_file)

    # Parse using packaging library (handles ~= and other PEP 440 operators)
    try:
        specifier_set = SpecifierSet(version_spec)
    except InvalidSpecifier as e:
        logger.error(f"Invalid version specifier '{version_spec}': {e}")
        return None

    # Determine if exact version
    is_exact = "==" in version_spec and "!=" not in version_spec

    # Extract version for display
    if is_exact:
        # Extract exact version
        version_str = version_spec.replace("==", "").strip()
        min_ver = max_ver = version_str
    else:
        # Extract minimum version from range
        min_ver = get_min_version(specifier_set)
        max_ver = get_max_version(specifier_set)
        version_str = min_ver if min_ver else "unknown"

    return TemporalVersion(
        version=version_str,
        source_file=source_file,
        is_exact=is_exact,
        raw_spec=requirement,
        min_version=min_ver,
        max_version=max_ver,
    )


def _create_version_from_poetry_caret(base_version: str, raw_spec: str, source_file: Path) -> TemporalVersion | None:
    """Create TemporalVersion from Poetry caret (^) notation.

    ^1.5.0 means >=1.5.0,<2.0.0
    ^0.5.0 means >=0.5.0,<0.6.0

    Args:
        base_version: Base version string
        raw_spec: Original requirement specification
        source_file: Source file path

    Returns:
        TemporalVersion object
    """
    try:
        parsed = parse(base_version)
        parts = str(parsed).split(".")

        # Determine upper bound based on first non-zero component
        if int(parts[0]) > 0:
            # Major version is non-zero: bump major version
            upper_major = int(parts[0]) + 1
            max_version = f"{upper_major}.0.0"
        else:
            # Major version is 0: bump minor version
            upper_minor = int(parts[1]) + 1 if len(parts) > 1 else 1
            max_version = f"0.{upper_minor}.0"

        return TemporalVersion(
            version=base_version,
            source_file=source_file,
            is_exact=False,
            raw_spec=raw_spec,
            min_version=base_version,
            max_version=max_version,
        )
    except Exception as e:
        logger.error(f"Failed to parse Poetry caret version '{base_version}': {e}")
        return None


def _create_version_from_poetry_tilde(base_version: str, raw_spec: str, source_file: Path) -> TemporalVersion | None:
    """Create TemporalVersion from Poetry tilde (~) notation.

    ~1.5 means >=1.5,<1.6
    ~1.5.0 means >=1.5.0,<1.6.0

    Args:
        base_version: Base version string
        raw_spec: Original requirement specification
        source_file: Source file path

    Returns:
        TemporalVersion object
    """
    try:
        parsed = parse(base_version)
        parts = str(parsed).split(".")

        # Bump the last specified component
        if len(parts) == 1:
            # ~1 means >=1,<2
            max_version = f"{int(parts[0]) + 1}.0.0"
        elif len(parts) == 2:
            # ~1.5 means >=1.5,<1.6
            max_version = f"{parts[0]}.{int(parts[1]) + 1}.0"
        else:
            # ~1.5.0 means >=1.5.0,<1.6.0
            max_version = f"{parts[0]}.{int(parts[1]) + 1}.0"

        return TemporalVersion(
            version=base_version,
            source_file=source_file,
            is_exact=False,
            raw_spec=raw_spec,
            min_version=base_version,
            max_version=max_version,
        )
    except Exception as e:
        logger.error(f"Failed to parse Poetry tilde version '{base_version}': {e}")
        return None


def parse_version_spec(version_spec: str) -> SpecifierSet:
    """Parse a version specification string.

    Args:
        version_spec: Version specification (e.g., ">=1.4.0,<2.0.0")

    Returns:
        SpecifierSet object

    Raises:
        InvalidSpecifier: If version spec is invalid
    """
    return SpecifierSet(version_spec)


def normalize_version(version: str) -> str:
    """Normalize version string to semver format.

    Args:
        version: Version string (e.g., "1.5", "1.5.0", "v1.5.0")

    Returns:
        Normalized version string (e.g., "1.5.0")

    Raises:
        InvalidVersion: If version cannot be parsed
    """
    # Remove 'v' prefix if present
    version = version.strip().lstrip("v")

    try:
        parsed = parse(version)
        # Convert to standard format (major.minor.patch)
        version_str = str(parsed)

        # Ensure we have major.minor.patch
        parts = version_str.split(".")
        if len(parts) == 1:
            return f"{parts[0]}.0.0"
        if len(parts) == 2:
            return f"{parts[0]}.{parts[1]}.0"
        return ".".join(parts[:3])
    except InvalidVersion as e:
        raise VersionParseError(f"Cannot normalize version '{version}': {e}") from e


def get_min_version(specifier_set: SpecifierSet) -> str | None:
    """Extract minimum version from specifier set.

    Args:
        specifier_set: SpecifierSet to analyze

    Returns:
        Minimum version string or None if unbounded
    """
    min_version = None

    for spec in specifier_set:
        operator = spec.operator
        version = str(spec.version)

        if operator in (">=", ">", "==", "~="):
            if min_version is None:
                min_version = version
            else:
                # Keep the higher minimum
                try:
                    if parse(version) > parse(min_version):
                        min_version = version
                except InvalidVersion:
                    continue

    return min_version


def get_max_version(specifier_set: SpecifierSet) -> str | None:
    """Extract maximum version from specifier set.

    Args:
        specifier_set: SpecifierSet to analyze

    Returns:
        Maximum version string or None if unbounded
    """
    max_version = None

    for spec in specifier_set:
        operator = spec.operator
        version = str(spec.version)

        if operator in ("<=", "<", "=="):
            if max_version is None:
                max_version = version
            else:
                # Keep the lower maximum
                try:
                    if parse(version) < parse(max_version):
                        max_version = version
                except InvalidVersion:
                    continue

    return max_version


def is_compatible(version: str, specifier: str) -> bool:
    """Check if a version satisfies a version specifier.

    Args:
        version: Version string to check (e.g., "1.5.0")
        specifier: Version specifier (e.g., ">=1.4.0,<2.0.0")

    Returns:
        True if version satisfies specifier, False otherwise

    Raises:
        InvalidVersion: If version string is invalid
        InvalidSpecifier: If specifier string is invalid
    """
    try:
        parsed_version = parse(version)
        specifier_set = SpecifierSet(specifier)
        return parsed_version in specifier_set
    except (InvalidVersion, InvalidSpecifier) as e:
        logger.error(f"Error checking compatibility: {e}")
        return False


def get_version_info(version: str) -> dict[str, Any]:
    """Get detailed information about a version string.

    Args:
        version: Version string (e.g., "1.5.0")

    Returns:
        Dictionary with version components and metadata

    Raises:
        InvalidVersion: If version cannot be parsed
    """
    parsed = parse(version)

    # Parse into components
    version_str = str(parsed)
    parts = version_str.split(".")

    major = int(parts[0]) if len(parts) > 0 else 0
    minor = int(parts[1]) if len(parts) > 1 else 0
    patch = int(parts[2]) if len(parts) > 2 else 0

    return {
        "version": version_str,
        "major": major,
        "minor": minor,
        "patch": patch,
        "is_prerelease": parsed.is_prerelease,
        "is_postrelease": parsed.is_postrelease,
        "is_devrelease": parsed.is_devrelease,
        "base_version": parsed.base_version,
    }
