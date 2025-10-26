"""Middleware for rate limiting and request validation."""

import time
from collections import defaultdict
from collections.abc import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using token bucket algorithm.

    Implements per-IP rate limiting with configurable requests per minute.
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = 100,
        burst_size: int = 10,
    ):
        """Initialize rate limiter.

        Args:
            app: FastAPI application
            requests_per_minute: Maximum requests allowed per minute per IP
            burst_size: Maximum burst size allowed
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.rate_per_second = requests_per_minute / 60.0

        # Store token buckets per IP: {ip: (tokens, last_update_time)}
        self._buckets: dict[str, tuple[float, float]] = defaultdict(
            lambda: (float(burst_size), time.time())
        )

        # Cleanup old entries periodically
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 minutes

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request.

        Args:
            request: FastAPI request object

        Returns:
            Client IP address
        """
        # Check for forwarded IP (behind proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # Check for real IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct client
        if request.client:
            return request.client.host

        return "unknown"

    def _cleanup_old_buckets(self) -> None:
        """Remove old bucket entries to prevent memory growth."""
        current_time = time.time()

        if current_time - self._last_cleanup > self._cleanup_interval:
            # Remove buckets not updated in last 10 minutes
            cutoff_time = current_time - 600

            old_ips = [
                ip
                for ip, (_, last_update) in self._buckets.items()
                if last_update < cutoff_time
            ]

            for ip in old_ips:
                del self._buckets[ip]

            self._last_cleanup = current_time

    def _check_rate_limit(self, client_ip: str) -> tuple[bool, dict[str, str]]:
        """Check if request should be rate limited.

        Args:
            client_ip: Client IP address

        Returns:
            Tuple of (allowed, headers) where headers contain rate limit info
        """
        current_time = time.time()

        # Get or initialize bucket
        tokens, last_update = self._buckets[client_ip]

        # Add tokens based on time passed
        time_passed = current_time - last_update
        tokens = min(self.burst_size, tokens + (time_passed * self.rate_per_second))

        # Check if we have tokens available
        if tokens >= 1.0:
            # Consume one token
            tokens -= 1.0
            allowed = True
        else:
            allowed = False

        # Update bucket
        self._buckets[client_ip] = (tokens, current_time)

        # Calculate headers
        remaining = int(tokens)
        reset_time = int(current_time + ((1.0 - tokens % 1.0) / self.rate_per_second))

        headers = {
            "X-RateLimit-Limit": str(self.requests_per_minute),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time),
        }

        if not allowed:
            retry_after = int((1.0 - tokens) / self.rate_per_second) + 1
            headers["Retry-After"] = str(retry_after)

        return allowed, headers

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting.

        Args:
            request: Incoming request
            call_next: Next middleware/endpoint handler

        Returns:
            Response with rate limit headers
        """
        # Cleanup old buckets periodically
        self._cleanup_old_buckets()

        # Get client IP
        client_ip = self._get_client_ip(request)

        # Check rate limit
        allowed, headers = self._check_rate_limit(client_ip)

        if not allowed:
            # Return 429 Too Many Requests
            return JSONResponse(
                status_code=429,
                content={
                    "error": "RateLimitExceeded",
                    "message": f"Rate limit exceeded. Maximum {self.requests_per_minute} requests per minute allowed.",
                    "details": {
                        "limit": self.requests_per_minute,
                        "retry_after": headers.get("Retry-After"),
                    },
                },
                headers=headers,
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        for key, value in headers.items():
            response.headers[key] = value

        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for additional request validation and security."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with validation.

        Args:
            request: Incoming request
            call_next: Next middleware/endpoint handler

        Returns:
            Response or error response
        """
        # Validate content type for POST requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")

            if not content_type.startswith("application/json"):
                return JSONResponse(
                    status_code=415,
                    content={
                        "error": "UnsupportedMediaType",
                        "message": "Content-Type must be application/json",
                        "details": {"received": content_type},
                    },
                )

        # Add request ID for tracing
        request.state.request_id = f"{int(time.time() * 1000)}-{id(request)}"

        # Process request
        response = await call_next(request)

        # Add request ID to response
        response.headers["X-Request-ID"] = request.state.request_id

        return response


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for monitoring request performance."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with timing.

        Args:
            request: Incoming request
            call_next: Next middleware/endpoint handler

        Returns:
            Response with timing header
        """
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # Convert to ms

        # Add timing header
        response.headers["X-Processing-Time-Ms"] = f"{processing_time:.2f}"

        return response
