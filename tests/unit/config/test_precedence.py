"""Unit tests for configuration precedence and deep merge logic."""

from mycelium_onboarding.config.precedence import (
    deep_merge,
    deep_merge_configs,
    get_effective_value,
    merge_with_precedence,
)


class TestDeepMerge:
    """Test deep_merge function."""

    def test_simple_merge(self) -> None:
        """Test merging simple dictionaries."""
        base = {"a": 1, "b": 2}
        overlay = {"b": 3, "c": 4}

        result = deep_merge(base, overlay)

        assert result == {"a": 1, "b": 3, "c": 4}

    def test_nested_merge(self) -> None:
        """Test merging nested dictionaries."""
        base = {"a": 1, "nested": {"x": 10, "y": 20}}
        overlay = {"nested": {"y": 30, "z": 40}}

        result = deep_merge(base, overlay)

        assert result == {"a": 1, "nested": {"x": 10, "y": 30, "z": 40}}

    def test_deeply_nested_merge(self) -> None:
        """Test merging deeply nested dictionaries."""
        base = {"a": {"b": {"c": {"d": 1, "e": 2}}}}
        overlay = {"a": {"b": {"c": {"e": 3, "f": 4}}}}

        result = deep_merge(base, overlay)

        assert result == {"a": {"b": {"c": {"d": 1, "e": 3, "f": 4}}}}

    def test_list_replacement(self) -> None:
        """Test that lists are replaced by default."""
        base = {"items": [1, 2, 3]}
        overlay = {"items": [4, 5]}

        result = deep_merge(base, overlay)

        assert result == {"items": [4, 5]}

    def test_list_concatenation(self) -> None:
        """Test list concatenation when merge_lists=True."""
        base = {"items": [1, 2, 3]}
        overlay = {"items": [4, 5]}

        result = deep_merge(base, overlay, merge_lists=True)

        assert result == {"items": [1, 2, 3, 4, 5]}

    def test_none_value_handling(self) -> None:
        """Test that None values in overlay are ignored."""
        base = {"a": 1, "b": 2}
        overlay = {"b": None, "c": 3}

        result = deep_merge(base, overlay)

        assert result == {"a": 1, "b": 2, "c": 3}

    def test_overlay_none_preserves_base(self) -> None:
        """Test that None overlay values preserve base values."""
        base = {"config": {"port": 8080, "host": "localhost"}}
        overlay = {"config": {"port": None, "timeout": 30}}

        result = deep_merge(base, overlay)

        assert result == {"config": {"port": 8080, "host": "localhost", "timeout": 30}}

    def test_type_replacement(self) -> None:
        """Test that different types replace each other."""
        base = {"value": {"nested": "dict"}}
        overlay = {"value": "string"}

        result = deep_merge(base, overlay)

        assert result == {"value": "string"}

    def test_empty_dicts(self) -> None:
        """Test merging with empty dictionaries."""
        base = {"a": 1}
        overlay: dict[str, int] = {}

        result = deep_merge(base, overlay)
        assert result == {"a": 1}

        result = deep_merge({}, base)
        assert result == {"a": 1}

    def test_no_mutation(self) -> None:
        """Test that input dictionaries are not mutated."""
        base = {"a": {"b": 1}}
        overlay = {"a": {"c": 2}}

        base_copy = base.copy()
        overlay_copy = overlay.copy()

        deep_merge(base, overlay)

        # Check that originals are unchanged (shallow comparison)
        assert base == base_copy
        assert overlay == overlay_copy


class TestDeepMergeConfigs:
    """Test deep_merge_configs function."""

    def test_merge_multiple_configs(self) -> None:
        """Test merging multiple configurations."""
        config1 = {"a": 1, "b": 2}
        config2 = {"b": 3, "c": 4}
        config3 = {"c": 5, "d": 6}

        result = deep_merge_configs(config1, config2, config3)

        assert result == {"a": 1, "b": 3, "c": 5, "d": 6}

    def test_merge_nested_configs(self) -> None:
        """Test merging multiple nested configurations."""
        config1 = {"services": {"redis": {"port": 6379}}}
        config2 = {"services": {"redis": {"timeout": 30}}}
        config3 = {"services": {"postgres": {"port": 5432}}}

        result = deep_merge_configs(config1, config2, config3)

        assert result == {
            "services": {
                "redis": {"port": 6379, "timeout": 30},
                "postgres": {"port": 5432},
            }
        }

    def test_empty_configs_list(self) -> None:
        """Test with no configurations."""
        result = deep_merge_configs()
        assert result == {}

    def test_single_config(self) -> None:
        """Test with single configuration."""
        config = {"a": 1, "b": 2}
        result = deep_merge_configs(config)
        assert result == {"a": 1, "b": 2}

    def test_filter_none_configs(self) -> None:
        """Test that None configs are filtered out."""
        config1 = {"a": 1}
        config2 = None
        config3 = {"b": 2}

        result = deep_merge_configs(config1, config2, config3)  # type: ignore
        assert result == {"a": 1, "b": 2}

    def test_filter_empty_configs(self) -> None:
        """Test that empty dicts are filtered out."""
        config1 = {"a": 1}
        config2 = {}
        config3 = {"b": 2}

        result = deep_merge_configs(config1, config2, config3)
        assert result == {"a": 1, "b": 2}


class TestMergeWithPrecedence:
    """Test merge_with_precedence function."""

    def test_three_tier_precedence(self) -> None:
        """Test 3-tier precedence: defaults → global → project."""
        defaults = {"port": 8080, "host": "localhost", "debug": False}
        global_config = {"port": 9000}
        project_config = {"debug": True}

        result = merge_with_precedence(defaults, global_config, project_config)

        assert result == {"port": 9000, "host": "localhost", "debug": True}

    def test_nested_precedence(self) -> None:
        """Test precedence with nested configurations."""
        defaults = {
            "services": {
                "redis": {"port": 6379, "persistence": True},
                "postgres": {"port": 5432},
            }
        }
        global_config = {"services": {"redis": {"port": 6380}}}
        project_config = {"services": {"postgres": {"port": 5433}}}

        result = merge_with_precedence(defaults, global_config, project_config)

        assert result == {
            "services": {
                "redis": {"port": 6380, "persistence": True},
                "postgres": {"port": 5433},
            }
        }

    def test_none_configs(self) -> None:
        """Test handling of None configurations."""
        defaults = {"a": 1, "b": 2}

        result = merge_with_precedence(defaults, None, None)
        assert result == {"a": 1, "b": 2}

        result = merge_with_precedence(defaults, {"a": 10}, None)
        assert result == {"a": 10, "b": 2}

        result = merge_with_precedence(defaults, None, {"b": 20})
        assert result == {"a": 1, "b": 20}

    def test_project_overrides_global(self) -> None:
        """Test that project config overrides global config."""
        defaults = {"value": 1}
        global_config = {"value": 2}
        project_config = {"value": 3}

        result = merge_with_precedence(defaults, global_config, project_config)
        assert result["value"] == 3

    def test_global_overrides_defaults(self) -> None:
        """Test that global config overrides defaults."""
        defaults = {"value": 1}
        global_config = {"value": 2}

        result = merge_with_precedence(defaults, global_config, None)
        assert result["value"] == 2

    def test_complex_merge(self) -> None:
        """Test complex real-world scenario."""
        defaults = {
            "version": "1.0",
            "project_name": "mycelium",
            "services": {
                "redis": {"port": 6379, "persistence": True, "max_memory": "256mb"},
                "postgres": {"port": 5432, "database": "mycelium"},
            },
            "deployment": {"method": "docker-compose", "auto_start": True},
        }

        global_config = {
            "services": {
                "redis": {"port": 6380},
                "postgres": {"database": "global_db"},
            }
        }

        project_config = {
            "project_name": "my-project",
            "services": {"redis": {"max_memory": "512mb"}},
            "deployment": {"auto_start": False},
        }

        result = merge_with_precedence(defaults, global_config, project_config)

        assert result["version"] == "1.0"
        assert result["project_name"] == "my-project"
        assert result["services"]["redis"]["port"] == 6380
        assert result["services"]["redis"]["persistence"] is True
        assert result["services"]["redis"]["max_memory"] == "512mb"
        assert result["services"]["postgres"]["port"] == 5432
        assert result["services"]["postgres"]["database"] == "global_db"
        assert result["deployment"]["method"] == "docker-compose"
        assert result["deployment"]["auto_start"] is False


class TestGetEffectiveValue:
    """Test get_effective_value function."""

    def test_simple_lookup(self) -> None:
        """Test simple key lookup."""
        config1 = {"port": 8080}
        config2 = {"port": 9000}

        value = get_effective_value("port", config1, config2)
        assert value == 9000

    def test_nested_lookup(self) -> None:
        """Test nested key lookup with dot notation."""
        config1 = {"services": {"redis": {"port": 6379}}}
        config2 = {"services": {"redis": {"port": 6380}}}

        value = get_effective_value("services.redis.port", config1, config2)
        assert value == 6380

    def test_precedence_order(self) -> None:
        """Test that rightmost config has highest precedence."""
        config1 = {"value": 1}
        config2 = {"value": 2}
        config3 = {"value": 3}

        value = get_effective_value("value", config1, config2, config3)
        assert value == 3

    def test_fallback_to_lower_precedence(self) -> None:
        """Test fallback when higher precedence has None."""
        config1 = {"value": 1}
        config2 = {"other": 2}

        value = get_effective_value("value", config1, config2)
        assert value == 1

    def test_missing_key(self) -> None:
        """Test lookup of missing key."""
        config1 = {"a": 1}
        config2 = {"b": 2}

        value = get_effective_value("c", config1, config2)
        assert value is None

    def test_nested_missing_key(self) -> None:
        """Test nested lookup with missing intermediate key."""
        config1 = {"services": {"redis": {"port": 6379}}}
        config2 = {"services": {"postgres": {"port": 5432}}}

        value = get_effective_value("services.redis.port", config1, config2)
        assert value == 6379

        value = get_effective_value("services.temporal.port", config1, config2)
        assert value is None

    def test_empty_configs(self) -> None:
        """Test with empty configurations."""
        value = get_effective_value("key")
        assert value is None

    def test_none_configs(self) -> None:
        """Test with None configurations."""
        config1 = {"a": 1}
        value = get_effective_value("a", config1, None, None)  # type: ignore
        assert value == 1
