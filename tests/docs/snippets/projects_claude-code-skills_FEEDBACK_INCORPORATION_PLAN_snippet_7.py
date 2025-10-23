# Source: projects/claude-code-skills/FEEDBACK_INCORPORATION_PLAN.md
# Line: 1433
# Valid syntax: True
# Has imports: False
# Has assignments: True

class TokenBudgetCalculator:
    """Calculate token budgets with advisory warnings (no enforcement by default)."""

    def __init__(self, policy_config: Dict[str, Any]):
        self.policy = PolicyManager(policy_config)
        self.predictor = MLTokenPredictor()  # From historical data

    def calculate_budget(
        self,
        workflow: Workflow,
        context: Dict[str, Any]
    ) -> BudgetRecommendation:
        """Calculate budget recommendation for workflow.

        Returns advisory budget with warnings, not hard limits.
        """
        # Predict token consumption
        estimated = self.predictor.predict(workflow, context)

        # Apply buffer
        buffer = self.policy.get_buffer_percentage()
        recommended = estimated * (1 + buffer / 100)

        # Generate recommendation
        return BudgetRecommendation(
            estimated_tokens=estimated,
            recommended_budget=recommended,
            confidence=self.predictor.confidence_score(),
            mode=self.policy.get_mode(),  # "warn" | "limit" | "off"
            warnings=self._generate_warnings(estimated, recommended),
            enforcement_enabled=self.policy.hard_limits_enabled()
        )

    def check_budget_status(
        self,
        consumed: int,
        budget: BudgetRecommendation
    ) -> BudgetStatus:
        """Check budget status and generate warnings if needed."""
        percentage = consumed / budget.recommended_budget

        status = BudgetStatus(
            consumed=consumed,
            recommended=budget.recommended_budget,
            percentage=percentage,
            warnings=[]
        )

        # Generate warnings based on policy
        if budget.mode == "warn" and percentage > self.policy.warn_threshold:
            status.warnings.append(
                f"⚠️ Token consumption at {percentage*100:.1f}% of recommended budget. "
                f"Consider optimizing or allocating more resources."
            )

        # Hard limit check (only if enabled)
        if budget.mode == "limit" and percentage > 1.0:
            if budget.enforcement_enabled:
                raise BudgetExceededError(
                    f"Hard budget limit exceeded: {consumed} > {budget.recommended_budget}"
                )
            status.warnings.append(
                "🚨 Budget exceeded but enforcement disabled. "
                "Enable hard limits if cost control is required."
            )

        return status
