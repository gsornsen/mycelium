# Source: detection-reference.md
# Line: 22
# Valid syntax: True
# Has imports: True
# Has assignments: False

from mycelium_onboarding.detection import (
    detect_all,
    detect_all_async,
    DetectionSummary,
    generate_detection_report,
    update_config_from_detection,
)

from mycelium_onboarding.detection.docker_detector import detect_docker
from mycelium_onboarding.detection.redis_detector import detect_redis, scan_common_redis_ports
from mycelium_onboarding.detection.postgres_detector import detect_postgres, scan_common_postgres_ports
from mycelium_onboarding.detection.temporal_detector import detect_temporal
from mycelium_onboarding.detection.gpu_detector import detect_gpus