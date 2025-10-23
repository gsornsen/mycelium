# Source: wizard-reference.md
# Line: 78
# Valid syntax: True
# Has imports: False
# Has assignments: True

@dataclass
class WizardState:
    """Complete wizard state with user selections."""

    # Step tracking
    current_step: WizardStep = WizardStep.WELCOME
    started_at: datetime = field(default_factory=datetime.now)

    # Detection results (from M03)
    detection_results: dict[str, Any] | None = None

    # User selections
    project_name: str = ""
    services_enabled: dict[str, bool] = field(default_factory=dict)
    deployment_method: str = "docker-compose"

    # Service-specific settings
    redis_port: int = 6379
    postgres_port: int = 5432
    postgres_database: str = ""
    temporal_namespace: str = "default"
    temporal_ui_port: int = 8080
    temporal_frontend_port: int = 7233

    # Advanced settings
    auto_start: bool = True
    enable_persistence: bool = True

    # Wizard metadata
    setup_mode: str = "quick"  # "quick" or "custom"
    completed: bool = False
    resumed: bool = False