# Source: detection-integration.md
# Line: 722
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.detection import detect_all
import redis
import psycopg2

def connect_to_services():
    """Connect to detected services."""
    summary = detect_all()
    connections = {}

    # Connect to Redis
    if summary.has_redis:
        redis_instance = summary.redis[0]
        connections["redis"] = redis.Redis(
            host=redis_instance.host,
            port=redis_instance.port,
            decode_responses=True
        )
        print(f"Connected to Redis on port {redis_instance.port}")

    # Connect to PostgreSQL
    if summary.has_postgres:
        pg_instance = summary.postgres[0]
        connections["postgres"] = psycopg2.connect(
            host=pg_instance.host,
            port=pg_instance.port,
            dbname="postgres",
            user="postgres"
        )
        print(f"Connected to PostgreSQL on port {pg_instance.port}")

    return connections

connections = connect_to_services()