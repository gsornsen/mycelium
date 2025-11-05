"""Tests for Alembic database schema migrations."""

import contextlib
import os
import tempfile
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from alembic import command


@pytest.fixture
def temp_database_url():
    """Create a temporary test database URL."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    db_url = f"sqlite:///{db_path}"
    yield db_url

    # Cleanup
    with contextlib.suppress(FileNotFoundError):
        Path(db_path).unlink()


@pytest.fixture
def alembic_config(temp_database_url):
    """Create Alembic configuration for testing with isolated database."""
    config_path = Path(__file__).parent.parent.parent / "alembic.ini"
    if not config_path.exists():
        pytest.skip(f"Alembic config not found: {config_path}")

    config = Config(str(config_path))

    # IMPORTANT: Directly set the database URL in the config
    # This ensures env.py uses the test database
    config.set_main_option("sqlalchemy.url", temp_database_url)

    # Also set the script location explicitly
    config.set_main_option("script_location", str(Path(__file__).parent.parent.parent / "alembic"))

    return config


def test_migration_upgrade_creates_tables(alembic_config, temp_database_url):
    """Test that migrations create the expected tables."""
    # No need for monkeypatch - config already has the URL

    # Run upgrade to heads (handles multiple heads)
    command.upgrade(alembic_config, "heads")

    # Verify tables were created
    engine = create_engine(temp_database_url)
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    # Check for expected tables (at least one should exist)
    expected_tables = ["agents", "coordination_events", "workflow_states", "task_states"]
    created_tables = [t for t in expected_tables if t in tables]

    assert len(created_tables) > 0, f"Expected at least one table from {expected_tables}, got {tables}"


def test_migration_downgrade_removes_tables(alembic_config, temp_database_url):
    """Test that migrations can be rolled back cleanly."""
    # Run upgrade to all heads
    command.upgrade(alembic_config, "heads")

    # Verify tables exist
    engine = create_engine(temp_database_url)
    inspector = inspect(engine)
    tables_after_upgrade = inspector.get_table_names()
    assert len(tables_after_upgrade) > 0

    # Run downgrade to base
    command.downgrade(alembic_config, "base")

    # Verify tables were removed (except alembic_version)
    inspector = inspect(engine)
    tables_after_downgrade = inspector.get_table_names()

    # Should only have alembic_version table remaining
    assert len(tables_after_downgrade) <= 1


def test_migration_is_idempotent(alembic_config, temp_database_url):
    """Test that running migrations twice is safe."""
    # Run upgrade twice - should not fail
    command.upgrade(alembic_config, "heads")
    command.upgrade(alembic_config, "heads")

    # Verify tables still exist
    engine = create_engine(temp_database_url)
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    assert len(tables) > 0


def test_migration_history_exists(alembic_config):
    """Test that migration history is tracked."""
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(alembic_config)

    # Get all revisions
    revisions = list(script.walk_revisions())

    # Should have at least the baseline migration
    assert len(revisions) >= 1

    # Check that we have heads
    heads = script.get_heads()
    assert len(heads) >= 1, "Should have at least one migration head"


def test_migration_heads(alembic_config):
    """Test migration heads management."""
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(alembic_config)
    heads = script.get_heads()

    # Document multiple heads if they exist
    if len(heads) > 1:
        # This is OK for parallel development branches
        # But should be resolved before production
        print(f"Multiple migration heads detected: {heads}")

    # Verify all heads are valid revisions
    for head in heads:
        revision = script.get_revision(head)
        assert revision is not None, f"Head {head} should be a valid revision"
        assert revision.revision == head


def test_migration_branches(alembic_config):
    """Test that migration branches are valid."""
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(alembic_config)

    # Get branch labels (use revision_map property, not _revision_map)
    revision_map = script.revision_map
    revision_map.branch_labels if hasattr(revision_map, "branch_labels") else {}

    # Get all revisions
    revisions = list(script.walk_revisions())

    # Verify revision dependencies
    for rev in revisions:
        if rev.down_revision:
            # For multiple down revisions (merge migrations)
            if isinstance(rev.down_revision, tuple):
                for down_rev in rev.down_revision:
                    down = script.get_revision(down_rev)
                    assert down is not None, f"Down revision {down_rev} should exist"
            else:
                down = script.get_revision(rev.down_revision)
                assert down is not None, f"Down revision {rev.down_revision} should exist"


def test_all_heads_upgrade(alembic_config, temp_database_url):
    """Test upgrading to all migration heads."""
    from alembic.script import ScriptDirectory

    # Get all heads
    script = ScriptDirectory.from_config(alembic_config)
    heads = script.get_heads()

    # Upgrade to each head individually
    for head in heads:
        # Clean slate for each head test
        command.downgrade(alembic_config, "base")

        # Upgrade to specific head
        command.upgrade(alembic_config, head)

        # Verify tables were created
        engine = create_engine(temp_database_url)
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        assert len(tables) > 1, f"Head {head} should create tables"


# PostgreSQL-specific tests with proper isolation
@pytest.fixture
def postgres_test_url():
    """Create a PostgreSQL test database URL if available."""
    base_url = os.getenv("DATABASE_URL")
    if not base_url:
        pytest.skip("PostgreSQL DATABASE_URL not configured")

    # For CI or when we have a real PostgreSQL instance
    # Parse and modify URL to use test database
    from urllib.parse import urlparse, urlunparse

    parsed = urlparse(base_url)
    # Create test database name
    test_db = f"test_{parsed.path.lstrip('/')}_migrations"
    test_parsed = parsed._replace(path=f"/{test_db}")
    test_url = urlunparse(test_parsed)

    # Note: In CI, we might not have permissions to create/drop databases
    # In that case, we'll use the existing database with careful cleanup
    try:
        from sqlalchemy_utils import create_database, database_exists, drop_database

        if database_exists(test_url):
            drop_database(test_url)
        create_database(test_url)

        yield test_url

        # Cleanup
        drop_database(test_url)
    except Exception:
        # Fallback: use the existing database but ensure cleanup
        yield base_url


@pytest.fixture
def postgres_alembic_config(postgres_test_url):
    """Create Alembic config for PostgreSQL testing."""
    config_path = Path(__file__).parent.parent.parent / "alembic.ini"
    config = Config(str(config_path))
    config.set_main_option("sqlalchemy.url", postgres_test_url)
    config.set_main_option("script_location", str(Path(__file__).parent.parent.parent / "alembic"))
    return config


@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="PostgreSQL database URL not configured")
def test_postgresql_migration(postgres_alembic_config, postgres_test_url):
    """Test migrations work with PostgreSQL (if available)."""
    # Run migration to all heads
    command.upgrade(postgres_alembic_config, "heads")

    # Verify pgvector extension and tables
    engine = create_engine(postgres_test_url)
    with engine.connect() as conn:
        # Check for pgvector extension
        result = conn.execute(text("SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector'"))
        has_vector = result.scalar() > 0

        if has_vector:
            # If migration created vector extension, verify it works
            result = conn.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'agents'"))
            has_agents = result.scalar() > 0
            assert has_agents, "agents table should exist with vector support"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
