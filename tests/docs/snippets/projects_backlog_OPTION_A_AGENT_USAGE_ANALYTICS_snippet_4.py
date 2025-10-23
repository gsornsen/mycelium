# Source: projects/backlog/OPTION_A_AGENT_USAGE_ANALYTICS.md
# Line: 793
# Valid syntax: True
# Has imports: True
# Has assignments: True

class AgentDiscovery:
    """Existing class - add usage tracking to get_agent()."""

    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent details (lazy load content).

        MODIFIED: Now tracks usage via telemetry.
        """
        start_time = time.perf_counter()
        self._stats['total_lookups'] += 1

        # ... existing cache check code ...

        # NEW: Track usage event (if telemetry available)
        if self.telemetry and agent_full:
            # Generate session ID (use thread ID for now)
            import threading
            session_id = f"session-{threading.get_ident()}"

            self.telemetry.record_agent_usage(
                agent_id=agent_id,
                session_id=session_id,
                context_type="manual",  # Assume manual for now
                invocation_method="direct",  # Direct get_agent() call
                category=agent_meta.get("category", "unknown"),
                keywords=agent_meta.get("keywords", []),
            )

        return agent_full