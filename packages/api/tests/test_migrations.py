"""Tests for database migrations."""
import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, text

def test_migration_heads():
    """Verify there's only one migration head."""
    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)
    
    # Ensure there's only one head
    heads = script.get_heads()
    assert len(heads) == 1, f"Expected 1 migration head, found {len(heads)}: {heads}"

@pytest.mark.skip(reason="Only run this test manually or in isolated CI environment")
def test_migrations_apply_cleanly():
    """Test all migrations apply cleanly to an empty database."""
    # Create a temporary test database
    engine = create_engine("postgresql://test:test@localhost/eudi_connect_test_migrations")
    
    try:
        # Drop and recreate the test database
        with engine.connect() as conn:
            conn.execution_options(isolation_level="AUTOCOMMIT")
            conn.execute(text("DROP DATABASE IF EXISTS eudi_connect_test_migrations"))
            conn.execute(text("CREATE DATABASE eudi_connect_test_migrations"))
        
        # Apply migrations
        from alembic import command
        config = Config("alembic.ini")
        command.upgrade(config, "head")
        
        # Verify database has the expected tables
        with engine.connect() as conn:
            tables = conn.execute(text(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            )).fetchall()
            table_names = [table[0] for table in tables]
            
            # Check for some key tables
            assert "merchant" in table_names
            assert "credentialtype" in table_names
            assert "walletsession" in table_names
            
    finally:
        # Clean up
        with engine.connect() as conn:
            conn.execution_options(isolation_level="AUTOCOMMIT")
            conn.execute(text("DROP DATABASE IF EXISTS eudi_connect_test_migrations"))
