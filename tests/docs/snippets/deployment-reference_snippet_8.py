# Source: deployment-reference.md
# Line: 127
# Valid syntax: True
# Has imports: False
# Has assignments: True

@dataclass
class GenerationResult:
    success: bool
    method: DeploymentMethod
    output_dir: Path
    files_generated: list[Path]
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)