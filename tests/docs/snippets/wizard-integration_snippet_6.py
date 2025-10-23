# Source: wizard-integration.md
# Line: 419
# Valid syntax: True
# Has imports: True
# Has assignments: True

import pickle

import redis

from mycelium_onboarding.wizard.flow import WizardState
from mycelium_onboarding.wizard.persistence import WizardStatePersistence


class RedisWizardPersistence(WizardStatePersistence):
    """Persist wizard state in Redis."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize Redis persistence."""
        self.redis_client = redis.from_url(redis_url)
        self.state_key = "mycelium:wizard:state"

    def save(self, state: WizardState) -> None:
        """Save state to Redis."""
        state_bytes = pickle.dumps(state)
        self.redis_client.set(self.state_key, state_bytes)
        # Set TTL: expire after 24 hours
        self.redis_client.expire(self.state_key, 86400)

    def load(self) -> WizardState | None:
        """Load state from Redis."""
        state_bytes = self.redis_client.get(self.state_key)
        if state_bytes:
            return pickle.loads(state_bytes)
        return None

    def clear(self) -> None:
        """Clear state from Redis."""
        self.redis_client.delete(self.state_key)

    def exists(self) -> bool:
        """Check if state exists in Redis."""
        return self.redis_client.exists(self.state_key) > 0

# Usage
persistence = RedisWizardPersistence()
state = WizardState()
persistence.save(state)
