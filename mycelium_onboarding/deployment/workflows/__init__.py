"""Temporal workflow testing module for deployment validation.

This module provides Temporal workflows and activities for testing deployed
Temporal + PostgreSQL infrastructure. It validates connection, execution,
state persistence, and error handling capabilities.

Key Components:
    - TestWorkflow: Main validation workflow with 5 stages
    - TestRunner: Workflow execution and result collection
    - Activities: Connection, execution, and persistence validation

Example:
    >>> from mycelium_onboarding.deployment.workflows import TestRunner
    >>> runner = TestRunner(temporal_host="localhost", temporal_port=7233)
    >>> result = await runner.run_validation()
    >>> if result.success:
    ...     print("Deployment validated successfully!")
"""

from mycelium_onboarding.deployment.workflows.test_runner import (
    TestRunner,
    ValidationResult,
)
from mycelium_onboarding.deployment.workflows.test_workflow import (
    TestWorkflow,
    ValidationStage,
    ValidationStatus,
)

__all__ = [
    "TestWorkflow",
    "TestRunner",
    "ValidationResult",
    "ValidationStage",
    "ValidationStatus",
]
