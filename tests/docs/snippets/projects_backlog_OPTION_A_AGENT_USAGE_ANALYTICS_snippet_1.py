# Source: projects/backlog/OPTION_A_AGENT_USAGE_ANALYTICS.md
# Line: 117
# Valid syntax: True
# Has imports: True
# Has assignments: True

class TelemetryCollector:
    """Existing class - add new methods."""

    def record_agent_usage(
        self,
        agent_id: str,
        session_id: str,
        context_type: str,
        invocation_method: str,
        category: str,
        keywords: list[str],
        session_duration_seconds: float | None = None,
        tasks_completed: int | None = None,
        effectiveness_score: float | None = None,
    ) -> None:
        """Track agent usage patterns.

        Args:
            agent_id: Agent identifier (e.g., "01-core-api-designer")
            session_id: Unique session identifier
            context_type: How agent was invoked:
                - "manual": User explicitly invoked
                - "suggested": System suggested, user accepted
                - "auto": Automatically invoked by orchestrator
            invocation_method: Discovery method:
                - "direct": User typed agent name
                - "search": Found via search()
                - "category_filter": Found via list_agents(category=...)
            category: Agent category (from index.json)
            keywords: Agent keywords (from index.json)
            session_duration_seconds: How long agent was active
            tasks_completed: Number of tasks completed (if trackable)
            effectiveness_score: User feedback score (1-5, optional)

        Example:
            >>> collector = TelemetryCollector(EventStorage())
            >>> collector.record_agent_usage(
            ...     agent_id="01-core-api-designer",
            ...     session_id="session-abc123",
            ...     context_type="manual",
            ...     invocation_method="search",
            ...     category="core-development",
            ...     keywords=["api", "design", "rest"],
            ...     session_duration_seconds=1200,
            ...     tasks_completed=3,
            ...     effectiveness_score=4.5
            ... )
        """
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "agent_usage",
            "agent_id_hash": self._hash_agent_id(agent_id),
            "session_id_hash": self._hash_session_id(session_id),
            "context_type": context_type,
            "invocation_method": invocation_method,
            "category": category,
            "keywords": keywords,
        }

        # Add optional fields if provided
        if session_duration_seconds is not None:
            event["session_duration_seconds"] = session_duration_seconds
        if tasks_completed is not None:
            event["tasks_completed"] = tasks_completed
        if effectiveness_score is not None:
            event["effectiveness_score"] = effectiveness_score

        self._record_event(event)

    def record_agent_effectiveness(
        self,
        agent_id: str,
        session_id: str,
        rating: int,
        feedback_type: str,
        task_success: bool,
    ) -> None:
        """Track user feedback on agent effectiveness.

        Args:
            agent_id: Agent identifier
            session_id: Session identifier
            rating: User rating (1-5 scale)
            feedback_type: Type of feedback:
                - "helpful": Agent was helpful
                - "unhelpful": Agent was not helpful
                - "suggested_improvement": User has suggestions
            task_success: Whether task was successfully completed

        Example:
            >>> collector.record_agent_effectiveness(
            ...     agent_id="01-core-api-designer",
            ...     session_id="session-abc123",
            ...     rating=5,
            ...     feedback_type="helpful",
            ...     task_success=True
            ... )
        """
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "agent_effectiveness",
            "agent_id_hash": self._hash_agent_id(agent_id),
            "session_id_hash": self._hash_session_id(session_id),
            "rating": rating,
            "feedback_type": feedback_type,
            "task_success": task_success,
        }
        self._record_event(event)

    @staticmethod
    def _hash_session_id(session_id: str) -> str:
        """Hash session ID for privacy (internal).

        Args:
            session_id: Session identifier

        Returns:
            Hashed session ID (first 8 chars of hex hash)
        """
        import hashlib
        return hashlib.sha256(session_id.encode()).hexdigest()[:8]
