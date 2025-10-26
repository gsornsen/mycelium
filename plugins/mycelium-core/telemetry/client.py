"""Telemetry client for sending anonymized events.

This module provides the main telemetry client that handles event collection,
batching, and transmission. All operations are non-blocking and gracefully
handle failures.
"""

import atexit
import json
import logging
import queue
import threading
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .anonymization import DataAnonymizer
from .config import TelemetryConfig

logger = logging.getLogger(__name__)


class TelemetryClient:
    """Client for sending anonymized telemetry events.

    This client operates in the background and batches events for efficiency.
    All operations are non-blocking - failures are logged but don't impact
    the main application.

    When telemetry is disabled, all methods become no-ops with zero overhead.
    """

    def __init__(self, config: TelemetryConfig | None = None) -> None:
        """Initialize telemetry client.

        Args:
            config: Telemetry configuration (loads from env if not provided)
        """
        self.config = config or TelemetryConfig.from_env()
        self.anonymizer = DataAnonymizer(self.config.salt)
        self._event_queue: queue.Queue[dict[str, Any]] = queue.Queue(
            maxsize=self.config.batch_size * 2
        )
        self._worker_thread: threading.Thread | None = None
        self._shutdown = threading.Event()
        self._enabled = self.config.is_enabled()

        # Only start background thread if enabled
        if self._enabled:
            self._start_worker()
            # Register cleanup on exit
            atexit.register(self.shutdown)

    def _start_worker(self) -> None:
        """Start background worker thread for processing events."""
        self._worker_thread = threading.Thread(
            target=self._worker_loop, name="telemetry-worker", daemon=True
        )
        self._worker_thread.start()
        logger.debug("Telemetry worker thread started")

    def _worker_loop(self) -> None:
        """Background worker loop that processes and sends events."""
        batch: list[dict[str, Any]] = []
        last_send = time.time()
        batch_timeout = 30.0  # Send batch every 30 seconds even if not full

        while not self._shutdown.is_set():
            try:
                # Wait for events with timeout to allow periodic batch sends
                timeout = max(0.1, batch_timeout - (time.time() - last_send))
                event = self._event_queue.get(timeout=timeout)
                batch.append(event)

                # Send batch if full or timeout reached
                should_send = (
                    len(batch) >= self.config.batch_size
                    or time.time() - last_send >= batch_timeout
                )

                if should_send and batch:
                    self._send_batch(batch)
                    batch = []
                    last_send = time.time()

            except queue.Empty:
                # Timeout - send any pending events
                if batch:
                    self._send_batch(batch)
                    batch = []
                    last_send = time.time()
            except Exception as e:
                logger.debug(f"Error in telemetry worker: {e}")
                # Don't let worker crash - just log and continue
                batch = []

        # Send any remaining events on shutdown
        if batch:
            self._send_batch(batch)

    def _send_batch(self, events: list[dict[str, Any]]) -> None:
        """Send a batch of events to the telemetry endpoint.

        Args:
            events: List of events to send
        """
        if not events:
            return

        payload = {
            "events": events,
            "version": "1.0",
            "timestamp": time.time(),
        }

        attempt = 0
        backoff = 1.0

        while attempt <= self.config.retry_attempts:
            try:
                data = json.dumps(payload).encode("utf-8")
                request = Request(
                    str(self.config.endpoint),
                    data=data,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "Mycelium-Telemetry/1.0",
                    },
                    method="POST",
                )

                with urlopen(request, timeout=self.config.timeout) as response:
                    if response.status == 200:
                        logger.debug(
                            f"Successfully sent {len(events)} telemetry events"
                        )
                        return
                    logger.debug(
                        f"Telemetry endpoint returned status {response.status}"
                    )

            except HTTPError as e:
                logger.debug(f"HTTP error sending telemetry: {e.code}")
                if e.code >= 500:
                    # Server error - retry with backoff
                    attempt += 1
                    if attempt <= self.config.retry_attempts:
                        time.sleep(backoff)
                        backoff *= self.config.retry_backoff
                else:
                    # Client error - don't retry
                    break
            except URLError as e:
                logger.debug(f"Network error sending telemetry: {e.reason}")
                attempt += 1
                if attempt <= self.config.retry_attempts:
                    time.sleep(backoff)
                    backoff *= self.config.retry_backoff
            except Exception as e:
                logger.debug(f"Unexpected error sending telemetry: {e}")
                break

        # Failed to send after retries - log and discard
        logger.debug(f"Failed to send {len(events)} telemetry events after retries")

    def _enqueue_event(self, event: dict[str, Any]) -> None:
        """Enqueue an event for sending.

        Args:
            event: Event data to enqueue
        """
        if not self._enabled:
            return  # No-op if disabled

        event["timestamp"] = time.time()

        try:
            self._event_queue.put_nowait(event)
        except queue.Full:
            logger.debug("Telemetry queue full - dropping event")

    def track_agent_usage(
        self, agent_id: str, operation: str, metadata: dict[str, Any] | None = None
    ) -> None:
        """Track agent usage event.

        Args:
            agent_id: Agent identifier (will be hashed)
            operation: Operation performed (e.g., 'discover', 'coordinate')
            metadata: Optional metadata (will be filtered for sensitive data)
        """
        if not self._enabled:
            return

        event = self.anonymizer.anonymize_agent_usage(agent_id, operation, metadata)
        event["event_type"] = "agent_usage"
        self._enqueue_event(event)

    def track_performance(
        self,
        metric_name: str,
        value: float,
        unit: str = "ms",
        tags: dict[str, str] | None = None,
    ) -> None:
        """Track performance metric.

        Args:
            metric_name: Name of the metric (e.g., 'discovery_latency')
            value: Metric value
            unit: Unit of measurement (default: 'ms')
            tags: Optional tags for the metric
        """
        if not self._enabled:
            return

        event = self.anonymizer.anonymize_performance_metric(
            metric_name, value, unit, tags
        )
        event["event_type"] = "performance"
        self._enqueue_event(event)

    def track_error(
        self,
        error_type: str,
        error_message: str,
        stack_trace: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Track error event.

        Args:
            error_type: Type of error (e.g., 'ValueError')
            error_message: Error message (will be anonymized)
            stack_trace: Optional stack trace (will be anonymized)
            context: Optional context (will be filtered for sensitive data)
        """
        if not self._enabled:
            return

        event = self.anonymizer.anonymize_error(error_type, error_message, stack_trace)
        event["event_type"] = "error"

        if context:
            safe_context = self.anonymizer._filter_safe_metadata(context)
            if safe_context:
                event["context"] = safe_context

        self._enqueue_event(event)

    def track_system_info(self) -> None:
        """Track system information (OS, Python version, etc.).

        This is called once on startup to collect non-sensitive system metadata.
        """
        if not self._enabled:
            return

        import platform

        event = {
            "event_type": "system_info",
            "platform": platform.system(),
            "platform_version": platform.release(),
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            # Mycelium version would be added here when available
        }

        self._enqueue_event(event)

    def shutdown(self) -> None:
        """Shutdown the telemetry client gracefully.

        Sends any remaining events and stops the worker thread.
        """
        if not self._enabled or self._shutdown.is_set():
            return

        logger.debug("Shutting down telemetry client...")
        self._shutdown.set()

        # Wait for worker to finish (with timeout)
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=5.0)

        logger.debug("Telemetry client shutdown complete")

    def is_enabled(self) -> bool:
        """Check if telemetry is enabled.

        Returns:
            True if telemetry is enabled, False otherwise
        """
        return self._enabled

    def __enter__(self) -> "TelemetryClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.shutdown()


# Global telemetry client instance
_global_client: TelemetryClient | None = None
_client_lock = threading.Lock()


def get_telemetry_client() -> TelemetryClient:
    """Get the global telemetry client instance.

    Returns:
        Global TelemetryClient instance
    """
    global _global_client

    if _global_client is None:
        with _client_lock:
            if _global_client is None:
                _global_client = TelemetryClient()

    return _global_client
