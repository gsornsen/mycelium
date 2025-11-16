"""Service detection module for smart deployment.

This module implements intelligent service detection, identifying existing
services that can be reused and determining deployment requirements.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import logging
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class ServiceType(str, Enum):
    """Types of services that can be detected."""

    POSTGRESQL = "postgresql"
    REDIS = "redis"
    RABBITMQ = "rabbitmq"
    ELASTICSEARCH = "elasticsearch"
    MONGODB = "mongodb"
    MYSQL = "mysql"
    KAFKA = "kafka"
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    CUSTOM = "custom"


class ServiceStatus(str, Enum):
    """Status of a detected service."""

    RUNNING = "running"
    STOPPED = "stopped"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"
    NOT_INSTALLED = "not_installed"


@dataclass
class ServiceFingerprint:
    """Fingerprint of a detected service for identification."""

    service_type: ServiceType
    version: str
    port: int
    host: str
    config_path: Path | None = None
    data_path: Path | None = None
    fingerprint_hash: str | None = None

    def __post_init__(self) -> None:
        """Generate fingerprint hash after initialization."""
        if not self.fingerprint_hash:
            self.fingerprint_hash = self._generate_hash()

    def _generate_hash(self) -> str:
        """Generate unique hash for service fingerprint."""
        data = {
            "type": self.service_type.value,
            "version": self.version,
            "port": self.port,
            "host": self.host,
            "config": str(self.config_path) if self.config_path else None,
            "data": str(self.data_path) if self.data_path else None,
        }
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()[:16]


class DetectedService(BaseModel):
    """Represents a detected service with its properties."""

    name: str = Field(description="Service name")
    service_type: ServiceType = Field(description="Type of service")
    status: ServiceStatus = Field(description="Current service status")
    version: str = Field(description="Service version")
    host: str = Field(default="localhost", description="Service host")
    port: int = Field(description="Service port")
    pid: int | None = Field(default=None, description="Process ID if running")
    config_path: Path | None = Field(default=None, description="Configuration file path")
    data_path: Path | None = Field(default=None, description="Data directory path")
    fingerprint: ServiceFingerprint | None = Field(default=None, description="Service fingerprint")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    capabilities: dict[str, Any] | None = Field(default=None, description="Service capabilities")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ServiceDetector:
    """Intelligent service detection system."""

    def __init__(self, scan_system: bool = True, scan_docker: bool = True):
        """Initialize service detector.

        Args:
            scan_system: Whether to scan system services
            scan_docker: Whether to scan Docker containers
        """
        self.scan_system = scan_system
        self.scan_docker = scan_docker
        self._detected_services: list[DetectedService] = []
        self._fingerprint_cache: dict[str, ServiceFingerprint] = {}

    def detect_all_services(self) -> list[DetectedService]:
        """Detect all available services.

        Returns:
            List of detected services
        """
        services: list[DetectedService] = []

        if self.scan_system:
            services.extend(self._detect_system_services())

        if self.scan_docker:
            services.extend(self._detect_docker_services())

        self._detected_services = services
        return services

    def detect_service(self, service_type: ServiceType) -> DetectedService | None:
        """Detect a specific service type.

        Args:
            service_type: Type of service to detect

        Returns:
            Detected service or None if not found
        """
        if service_type == ServiceType.POSTGRESQL:
            return self._detect_postgresql()
        if service_type == ServiceType.REDIS:
            return self._detect_redis()
        if service_type == ServiceType.DOCKER:
            return self._detect_docker()
        logger.warning(f"Detection not implemented for {service_type}")
        return None

    def _detect_system_services(self) -> list[DetectedService]:
        """Detect services running on the system."""
        services: list[DetectedService] = []

        # Detect PostgreSQL
        pg_service = self._detect_postgresql()
        if pg_service:
            services.append(pg_service)

        # Detect Redis
        redis_service = self._detect_redis()
        if redis_service:
            services.append(redis_service)

        return services

    def _detect_postgresql(self) -> DetectedService | None:
        """Detect PostgreSQL service."""
        try:
            # Check if PostgreSQL is installed
            result = subprocess.run(["which", "psql"], capture_output=True, text=True, check=False)

            if result.returncode != 0:
                return None

            # Get version
            version_result = subprocess.run(["psql", "--version"], capture_output=True, text=True, check=False)
            version = "unknown"
            if version_result.returncode == 0:
                # Parse version from output like "psql (PostgreSQL) 14.5"
                parts = version_result.stdout.strip().split()
                if len(parts) >= 3:
                    version = parts[2]

            # Check if service is running
            status = ServiceStatus.NOT_INSTALLED
            port = 5432  # Default PostgreSQL port
            pid = None

            # Try to check service status
            status_result = subprocess.run(["pg_isready"], capture_output=True, text=True, check=False)

            if status_result.returncode == 0:
                status = ServiceStatus.RUNNING
                # Try to get PID
                pid_result = subprocess.run(["pgrep", "-f", "postgres"], capture_output=True, text=True, check=False)
                if pid_result.returncode == 0 and pid_result.stdout:
                    pid = int(pid_result.stdout.strip().split()[0])
            else:
                status = ServiceStatus.STOPPED

            # Find config and data paths (with permission-safe approach)
            config_path = None
            data_path = None

            # Common PostgreSQL config locations
            config_locations = [
                "/etc/postgresql/*/main/postgresql.conf",
                "/usr/local/pgsql/data/postgresql.conf",
                "/var/lib/pgsql/data/postgresql.conf",
            ]

            for pattern in config_locations:
                try:
                    paths = list(Path("/").glob(pattern.lstrip("/")))
                    if paths:
                        # Check if we can actually read the file
                        test_path = paths[0]
                        if test_path.exists():
                            try:
                                # Test read access without actually reading
                                test_path.stat()
                                config_path = test_path
                                data_path = test_path.parent
                                break
                            except (PermissionError, OSError) as e:
                                logger.debug(f"Cannot access PostgreSQL config at {test_path}: {e}")
                                continue
                except Exception as e:
                    logger.debug(f"Error checking PostgreSQL config pattern {pattern}: {e}")
                    continue

            # Create fingerprint
            fingerprint = ServiceFingerprint(
                service_type=ServiceType.POSTGRESQL,
                version=version,
                port=port,
                host="localhost",
                config_path=config_path,
                data_path=data_path,
            )

            return DetectedService(
                name="postgresql",
                service_type=ServiceType.POSTGRESQL,
                status=status,
                version=version,
                host="localhost",
                port=port,
                pid=pid,
                config_path=config_path,
                data_path=data_path,
                fingerprint=fingerprint,
                metadata={"detection_method": "system", "executable": result.stdout.strip()},
            )

        except Exception as e:
            logger.error(f"Error detecting PostgreSQL: {e}")
            return None

    def _detect_redis(self) -> DetectedService | None:
        """Detect Redis service.

        Uses a defensive approach that separates critical detection
        (version, status) from optional metadata (config paths).
        """
        try:
            # Check if Redis is installed
            result = subprocess.run(["which", "redis-cli"], capture_output=True, text=True, check=False)

            if result.returncode != 0:
                return None

            # Get version
            version_result = subprocess.run(["redis-cli", "--version"], capture_output=True, text=True, check=False)
            version = "unknown"
            if version_result.returncode == 0:
                # Parse version from output like "redis-cli 6.2.6"
                parts = version_result.stdout.strip().split()
                if len(parts) >= 2:
                    version = parts[1]

            # Check if service is running
            status = ServiceStatus.NOT_INSTALLED
            port = 6379  # Default Redis port
            pid = None

            # Try to ping Redis
            ping_result = subprocess.run(["redis-cli", "ping"], capture_output=True, text=True, check=False)

            if ping_result.returncode == 0 and "PONG" in ping_result.stdout:
                status = ServiceStatus.RUNNING
                # Try to get PID
                pid_result = subprocess.run(
                    ["pgrep", "-f", "redis-server"], capture_output=True, text=True, check=False
                )
                if pid_result.returncode == 0 and pid_result.stdout:
                    pid = int(pid_result.stdout.strip().split()[0])
            else:
                status = ServiceStatus.STOPPED

            # Find config path (defensive: don't fail detection if this fails)
            config_path = None
            config_locations = [
                "/etc/redis/redis.conf",
                "/usr/local/etc/redis.conf",
                "/etc/redis.conf",
            ]

            for path_str in config_locations:
                try:
                    path = Path(path_str)
                    if path.exists():
                        # Test read access before committing to this path
                        try:
                            path.stat()  # This will raise PermissionError if no access
                            config_path = path
                            break
                        except PermissionError as e:
                            logger.debug(f"Cannot access Redis config at {path}: {e}")
                            # Continue checking other locations
                            continue
                except Exception as e:
                    logger.debug(f"Error checking Redis config path {path_str}: {e}")
                    continue

            # Determine data path (best effort, permission-safe)
            data_path = None
            try:
                redis_data = Path("/var/lib/redis")
                if redis_data.exists():
                    try:
                        redis_data.stat()
                        data_path = redis_data
                    except (PermissionError, OSError):
                        logger.debug(f"Cannot access Redis data directory: {redis_data}")
            except Exception as e:
                logger.debug(f"Error checking Redis data path: {e}")

            # Detect Redis capabilities if running
            capabilities = None
            if status == ServiceStatus.RUNNING:
                capabilities = self.detect_redis_capabilities("localhost", port)

            # Create fingerprint (config_path and data_path can be None)
            fingerprint = ServiceFingerprint(
                service_type=ServiceType.REDIS,
                version=version,
                port=port,
                host="localhost",
                config_path=config_path,
                data_path=data_path,
            )

            # Always return a DetectedService if we got this far
            # Config paths are optional metadata, not required for detection
            detected = DetectedService(
                name="redis",
                service_type=ServiceType.REDIS,
                status=status,
                version=version,
                host="localhost",
                port=port,
                pid=pid,
                config_path=config_path,
                fingerprint=fingerprint,
                capabilities=capabilities,
                metadata={
                    "detection_method": "system",
                    "executable": result.stdout.strip(),
                    "config_accessible": config_path is not None,
                },
            )

            logger.info(
                f"Detected Redis: status={status.value}, version={version}, port={port}, "
                f"config_found={config_path is not None}, "
                f"has_json={capabilities.get('has_json_module', False) if capabilities else 'unknown'}"
            )
            return detected

        except Exception as e:
            # Only fail if critical detection failed, not metadata collection
            logger.error(f"Critical error detecting Redis: {e}")
            return None

    def detect_redis_capabilities(self, host: str, port: int) -> dict[str, Any]:
        """Detect Redis version and available modules (especially RedisJSON).

        Args:
            host: Redis host address
            port: Redis port number

        Returns:
            Dict containing version, modules, and recommendations
        """
        try:
            import redis
        except ImportError:
            logger.warning("redis-py not installed, cannot detect Redis capabilities")
            return {
                "host": host,
                "port": port,
                "status": "unknown",
                "error": "redis-py module not installed",
            }

        try:
            client = redis.Redis(host=host, port=port, decode_responses=True, socket_timeout=5)

            # Test connection
            client.ping()

            # Get version
            info = client.info()
            version = info.get("redis_version", "unknown")

            # Check loaded modules
            modules = []
            has_json = False

            try:
                module_list = client.execute_command("MODULE", "LIST")
                for module_info in module_list:
                    if isinstance(module_info, (list, tuple)) and len(module_info) >= 2:
                        module_name = (
                            module_info[1].decode() if isinstance(module_info[1], bytes) else str(module_info[1])
                        )
                        modules.append(module_name)
                        if "ReJSON" in module_name or "json" in module_name.lower():
                            has_json = True
            except redis.exceptions.ResponseError:
                # MODULE LIST not available or no modules loaded
                pass

            return {
                "host": host,
                "port": port,
                "version": version,
                "modules": modules,
                "has_json_module": has_json,
                "status": "compatible" if has_json else "limited",
                "recommendation": None if has_json else "Upgrade to Redis Stack for full coordination support",
            }

        except redis.exceptions.ConnectionError as e:
            return {"host": host, "port": port, "status": "unreachable", "error": str(e)}
        except Exception as e:
            return {"host": host, "port": port, "status": "error", "error": str(e)}

    def _detect_docker_services(self) -> list[DetectedService]:
        """Detect services running in Docker containers."""
        services: list[DetectedService] = []

        try:
            # Check if Docker is available
            result = subprocess.run(["docker", "ps", "--format", "json"], capture_output=True, text=True, check=False)

            if result.returncode != 0:
                return services

            # Parse Docker containers
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                try:
                    container = json.loads(line)
                    # Analyze container to detect service type
                    service = self._analyze_docker_container(container)
                    if service:
                        services.append(service)
                except json.JSONDecodeError:
                    continue

        except Exception as e:
            logger.error(f"Error detecting Docker services: {e}")

        return services

    def _analyze_docker_container(self, container: dict[str, Any]) -> DetectedService | None:
        """Analyze a Docker container to detect service type.

        Uses multiple detection strategies:
        1. Image name (postgres, redis, etc.)
        2. Container name (mycelium-postgres, etc.)
        3. Port mapping (5432 for postgres, 6379 for redis)
        """
        image = container.get("Image", "").lower()
        names = container.get("Names", "").lower()
        ports = container.get("Ports", "")

        # Detect PostgreSQL container (multiple strategies)
        if (
            "postgres" in image
            or "postgresql" in image
            or "pgvector" in image  # Popular PostgreSQL extension image
            or "postgres" in names  # Check container name too
            or "postgresql" in names
            or (":5432->" in ports or "5432/tcp" in ports)  # Port-based detection
        ):
            return self._create_docker_service(container, ServiceType.POSTGRESQL, default_port=5432)

        # Detect Redis container (multiple strategies)
        if "redis" in image or "redis" in names or (":6379->" in ports or "6379/tcp" in ports):
            return self._create_docker_service(container, ServiceType.REDIS, default_port=6379)

        # Add more service detection patterns as needed

        return None

    def _create_docker_service(
        self, container: dict[str, Any], service_type: ServiceType, default_port: int
    ) -> DetectedService:
        """Create a DetectedService from Docker container info."""
        # Extract version from image tag
        image = container.get("Image", "")
        version = "latest"
        if ":" in image:
            version = image.split(":")[-1]

        # Parse ports
        port = default_port
        ports_str = container.get("Ports", "")
        if ports_str and "->" in ports_str:
            # Parse port mapping like "0.0.0.0:5432->5432/tcp"
            parts = ports_str.split("->")[0].split(":")
            if len(parts) > 1:
                # Attempt to parse port, ignore if invalid
                with contextlib.suppress(ValueError):
                    port = int(parts[-1])
                    pass

        # Create fingerprint
        fingerprint = ServiceFingerprint(service_type=service_type, version=version, port=port, host="localhost")

        return DetectedService(
            name=container.get("Names", f"{service_type.value}-docker"),
            service_type=service_type,
            status=ServiceStatus.RUNNING if container.get("State") == "running" else ServiceStatus.STOPPED,
            version=version,
            host="localhost",
            port=port,
            fingerprint=fingerprint,
            metadata={
                "detection_method": "docker",
                "container_id": container.get("ID", ""),
                "image": image,
                "created": container.get("CreatedAt", ""),
            },
        )

    def _detect_docker(self) -> DetectedService | None:
        """Detect Docker itself as a service."""
        try:
            # Check if Docker is installed
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True, check=False)

            if result.returncode != 0:
                return None

            # Parse version
            version = "unknown"
            if result.stdout:
                # Parse from "Docker version 20.10.17, build 100c701"
                parts = result.stdout.strip().split()
                if len(parts) >= 3:
                    version = parts[2].rstrip(",")

            # Check if Docker daemon is running
            status = ServiceStatus.STOPPED
            info_result = subprocess.run(["docker", "info"], capture_output=True, text=True, check=False)

            if info_result.returncode == 0:
                status = ServiceStatus.RUNNING

            return DetectedService(
                name="docker",
                service_type=ServiceType.DOCKER,
                status=status,
                version=version,
                host="localhost",
                port=2375,  # Default Docker API port
                metadata={"detection_method": "system", "daemon_running": status == ServiceStatus.RUNNING},
            )

        except Exception as e:
            logger.error(f"Error detecting Docker: {e}")
            return None

    def get_service_by_type(self, service_type: ServiceType) -> DetectedService | None:
        """Get a detected service by type.

        Args:
            service_type: Type of service to find

        Returns:
            First matching service or None
        """
        for service in self._detected_services:
            if service.service_type == service_type:
                return service
        return None

    def get_reusable_services(self) -> list[DetectedService]:
        """Get list of services that can be reused.

        Returns:
            List of running services that can be reused
        """
        return [service for service in self._detected_services if service.status == ServiceStatus.RUNNING]

    def generate_deployment_report(self) -> dict[str, Any]:
        """Generate a deployment readiness report.

        Returns:
            Report with service detection results and recommendations
        """
        return {
            "detected_services": len(self._detected_services),
            "running_services": len([s for s in self._detected_services if s.status == ServiceStatus.RUNNING]),
            "reusable_services": len(self.get_reusable_services()),
            "services": [
                {
                    "name": s.name,
                    "type": s.service_type.value,
                    "status": s.status.value,
                    "version": s.version,
                    "port": s.port,
                    "reusable": s.status == ServiceStatus.RUNNING,
                }
                for s in self._detected_services
            ],
            "recommendations": self._generate_recommendations(),
        }

    def _generate_recommendations(self) -> list[str]:
        """Generate deployment recommendations based on detected services."""
        recommendations = []

        # Check for PostgreSQL
        pg = self.get_service_by_type(ServiceType.POSTGRESQL)
        if pg:
            if pg.status == ServiceStatus.RUNNING:
                recommendations.append(f"PostgreSQL {pg.version} is running and can be reused")
            else:
                recommendations.append("PostgreSQL is installed but not running - consider starting it")
        else:
            recommendations.append("PostgreSQL not detected - will need to install or use Docker")

        # Check for Docker
        docker = self.get_service_by_type(ServiceType.DOCKER)
        if docker and docker.status == ServiceStatus.RUNNING:
            recommendations.append("Docker is available for containerized deployments")
        else:
            recommendations.append("Docker not available - system services will be used")

        return recommendations
