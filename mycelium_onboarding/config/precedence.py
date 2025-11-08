"""Configuration precedence and deep merge utilities.

This module provides utilities for deep merging configuration dictionaries
with proper precedence handling. Supports the 3-tier configuration system:
defaults → global → project.

The deep merge algorithm handles:
- Nested dictionaries (merged recursively)
- Lists (replaced, not merged)
- Primitive values (higher precedence wins)
- None values (treated as "not set", lower precedence wins)

Example:
    >>> from mycelium_onboarding.config.precedence import deep_merge
    >>> base = {"a": 1, "b": {"c": 2, "d": 3}}
    >>> overlay = {"b": {"d": 4, "e": 5}, "f": 6}
    >>> result = deep_merge(base, overlay)
    >>> result
    {'a': 1, 'b': {'c': 2, 'd': 4, 'e': 5}, 'f': 6}
"""

from __future__ import annotations

import copy
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Module exports
__all__ = [
    "deep_merge",
    "deep_merge_configs",
    "merge_with_precedence",
    "MergeStrategy",
]


class MergeStrategy:
    """Configuration merge strategies.

    Attributes:
        REPLACE: Replace entire value (for lists and primitives)
        RECURSIVE: Recursively merge nested dictionaries
        PREFER_OVERLAY: Use overlay value if not None, else base value
    """

    REPLACE = "replace"
    RECURSIVE = "recursive"
    PREFER_OVERLAY = "prefer_overlay"


def deep_merge(
    base: dict[str, Any],
    overlay: dict[str, Any],
    *,
    merge_lists: bool = False,
) -> dict[str, Any]:
    """Deep merge two dictionaries with overlay taking precedence.

    Performs a recursive merge where:
    - Nested dicts are merged recursively
    - Lists are replaced by default (use merge_lists=True to concatenate)
    - Primitive values from overlay override base values
    - None values in overlay are treated as "not set" (base value wins)

    Args:
        base: Base dictionary (lower precedence)
        overlay: Overlay dictionary (higher precedence)
        merge_lists: If True, concatenate lists instead of replacing

    Returns:
        New dictionary with merged values

    Example:
        >>> base = {"a": 1, "b": {"c": 2}}
        >>> overlay = {"b": {"d": 3}}
        >>> deep_merge(base, overlay)
        {'a': 1, 'b': {'c': 2, 'd': 3}}

    Note:
        This function does not modify the input dictionaries.
    """
    # Create a deep copy of base to avoid mutation
    result = copy.deepcopy(base)

    for key, overlay_value in overlay.items():
        # If key doesn't exist in base, just add it
        if key not in result:
            result[key] = copy.deepcopy(overlay_value)
            continue

        base_value = result[key]

        # If overlay value is None, treat as "not set" - keep base value
        if overlay_value is None:
            continue

        # If both are dicts, merge recursively
        if isinstance(base_value, dict) and isinstance(overlay_value, dict):
            result[key] = deep_merge(base_value, overlay_value, merge_lists=merge_lists)
        # If both are lists and merge_lists is True, concatenate
        elif merge_lists and isinstance(base_value, list) and isinstance(overlay_value, list):
            result[key] = base_value + overlay_value
        # Otherwise, overlay value replaces base value
        else:
            result[key] = copy.deepcopy(overlay_value)

    return result


def deep_merge_configs(
    *configs: dict[str, Any],
    merge_lists: bool = False,
) -> dict[str, Any]:
    """Deep merge multiple configuration dictionaries in order.

    Merges configurations from left to right, with rightmost configs
    having highest precedence.

    Args:
        *configs: Variable number of configuration dictionaries to merge
        merge_lists: If True, concatenate lists instead of replacing

    Returns:
        Merged configuration dictionary

    Example:
        >>> defaults = {"port": 8080, "host": "localhost"}
        >>> global_cfg = {"port": 9000}
        >>> project_cfg = {"host": "0.0.0.0"}
        >>> deep_merge_configs(defaults, global_cfg, project_cfg)
        {'port': 9000, 'host': '0.0.0.0'}

    Note:
        Empty dictionaries are skipped. Returns empty dict if all configs are empty.
    """
    if not configs:
        return {}

    # Filter out None and empty dicts
    valid_configs = [c for c in configs if c]

    if not valid_configs:
        return {}

    # Start with first config as base
    result = copy.deepcopy(valid_configs[0])

    # Merge each subsequent config
    for config in valid_configs[1:]:
        result = deep_merge(result, config, merge_lists=merge_lists)

    return result


def merge_with_precedence(
    defaults: dict[str, Any],
    global_config: dict[str, Any] | None,
    project_config: dict[str, Any] | None,
    *,
    merge_lists: bool = False,
) -> dict[str, Any]:
    """Merge configurations following 3-tier precedence.

    Applies the precedence order: defaults → global → project
    (rightmost has highest precedence)

    Args:
        defaults: Default configuration values (lowest precedence)
        global_config: User-global configuration (medium precedence)
        project_config: Project-local configuration (highest precedence)
        merge_lists: If True, concatenate lists instead of replacing

    Returns:
        Merged configuration dictionary

    Example:
        >>> defaults = {"version": "1.0", "services": {"redis": {"port": 6379}}}
        >>> global_cfg = {"services": {"redis": {"port": 6380}}}
        >>> project_cfg = {"project_name": "my-project"}
        >>> result = merge_with_precedence(defaults, global_cfg, project_cfg)
        >>> result['services']['redis']['port']
        6380
        >>> result['project_name']
        'my-project'
    """
    logger.debug(
        "Merging configs with precedence: defaults=%s, global=%s, project=%s",
        bool(defaults),
        bool(global_config),
        bool(project_config),
    )

    # Build list of configs in precedence order (lowest to highest)
    configs_to_merge: list[dict[str, Any]] = [defaults]

    if global_config:
        configs_to_merge.append(global_config)

    if project_config:
        configs_to_merge.append(project_config)

    result = deep_merge_configs(*configs_to_merge, merge_lists=merge_lists)

    logger.info(
        "Configuration merge completed with %d layers",
        len(configs_to_merge),
    )

    return result


def get_effective_value(
    key: str,
    *configs: dict[str, Any],
) -> Any:
    """Get the effective value for a key across multiple configs.

    Searches configs from right to left (highest to lowest precedence)
    and returns the first non-None value found.

    Args:
        key: Configuration key to look up (supports dot notation)
        *configs: Configuration dictionaries in precedence order (lowest to highest)

    Returns:
        The effective value for the key, or None if not found

    Example:
        >>> defaults = {"port": 8080}
        >>> global_cfg = {"port": None}
        >>> project_cfg = {}
        >>> get_effective_value("port", defaults, global_cfg, project_cfg)
        8080
    """
    # Search from right to left (highest precedence first)
    for config in reversed(configs):
        if not config:
            continue

        # Handle dot notation for nested keys
        value = _get_nested_value(config, key)
        if value is not None:
            return value

    return None


def _get_nested_value(config: dict[str, Any], key: str) -> Any:
    """Get value from nested dictionary using dot notation.

    Args:
        config: Configuration dictionary
        key: Key in dot notation (e.g., "services.redis.port")

    Returns:
        Value at the nested key, or None if not found

    Example:
        >>> config = {"services": {"redis": {"port": 6379}}}
        >>> _get_nested_value(config, "services.redis.port")
        6379
    """
    keys = key.split(".")
    value: Any = config

    for k in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(k)
        if value is None:
            return None

    return value
