# Source: skills/S1-agent-discovery-fastmcp.md
# Line: 883
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_analytics import TelemetryCollector


class InstrumentedDiscoveryService(AgentDiscoveryService):
    """Discovery service with telemetry."""

    def __init__(self):
        super().__init__()
        self.telemetry = TelemetryCollector()

    async def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Search with telemetry."""
        import time

        start = time.perf_counter()

        try:
            results = await super().search(query, **kwargs)

            # Record success metrics
            self.telemetry.record_event(
                event_type="discovery_search",
                data={
                    "query": query,
                    "results_count": len(results),
                    "latency_ms": (time.perf_counter() - start) * 1000,
                    "success": True
                }
            )

            return results

        except Exception as e:
            # Record failure metrics
            self.telemetry.record_event(
                event_type="discovery_search",
                data={
                    "query": query,
                    "latency_ms": (time.perf_counter() - start) * 1000,
                    "success": False,
                    "error": str(e)
                }
            )
            raise
