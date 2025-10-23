# Source: projects/claude-code-skills/FEEDBACK_INCORPORATION_PLAN.md
# Line: 455
# Valid syntax: True
# Has imports: False
# Has assignments: False

class BudgetAwareSkill(BaseSkill):
    """Extended base class for budget-aware skills."""

    def estimate_tokens(self, params: Dict[str, Any]) -> int:
        """Estimate token consumption for this execution.

        Used by budget allocator to provide warnings.

        Args:
            params: Skill execution parameters

        Returns:
            Estimated token count
        """
        return 1000  # Override with actual estimation

    def on_budget_warning(self, estimated: int, allocated: int):
        """Callback when budget warning is triggered.

        Default behavior: log warning and continue.
        Override to customize behavior.

        Args:
            estimated: Estimated token consumption
            allocated: Allocated budget (if limits enabled)
        """
        logger.warning(
            f"Budget warning: estimated {estimated} tokens, "
            f"allocated {allocated} tokens"
        )

    def on_budget_exceeded(self, estimated: int, allocated: int) -> bool:
        """Callback when hard budget limit exceeded.

        Only called if hard limits are enabled.

        Args:
            estimated: Estimated token consumption
            allocated: Allocated budget

        Returns:
            True to proceed anyway, False to abort
        """
        return False  # Default: respect hard limits
