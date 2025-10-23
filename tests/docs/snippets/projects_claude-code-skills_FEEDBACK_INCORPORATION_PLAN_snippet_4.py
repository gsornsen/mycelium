# Source: projects/claude-code-skills/FEEDBACK_INCORPORATION_PLAN.md
# Line: 787
# Valid syntax: True
# Has imports: True
# Has assignments: True

# plugins/mycelium-core/skills/database.py
import os
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from pgvector.psycopg2 import register_vector

class DatabaseManager:
    """Manages PostgreSQL connections for skills infrastructure."""

    def __init__(self):
        self.pool = SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            host=os.getenv('PGHOST', 'localhost'),
            database=os.getenv('PGDATABASE', 'mycelium_skills'),
            user=os.getenv('PGUSER', os.getenv('USER')),
            password=os.getenv('PGPASSWORD', '')
        )

    def get_connection(self):
        """Get connection from pool."""
        conn = self.pool.getconn()
        register_vector(conn)  # Enable pgvector support
        return conn

    def return_connection(self, conn):
        """Return connection to pool."""
        self.pool.putconn(conn)