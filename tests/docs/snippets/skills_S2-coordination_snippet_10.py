# Source: skills/S2-coordination.md
# Line: 412
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Process multiple data sources in parallel
workflow = await coordinate_workflow(
    steps=[
        {
            "agent": "data-engineer",
            "task": "Clean and validate customer data",
            "params": {"dataset": "customers.csv", "validations": ["email", "phone"]}
        },
        {
            "agent": "data-engineer",
            "task": "Clean and validate order data",
            "params": {"dataset": "orders.csv", "validations": ["amounts", "dates"]}
        },
        {
            "agent": "data-engineer",
            "task": "Clean and validate product data",
            "params": {"dataset": "products.csv", "validations": ["prices", "stock"]}
        },
        {
            "agent": "analytics-expert",
            "task": "Generate insights from cleaned data",
            "depends_on": ["step-0", "step-1", "step-2"],
            "params": {"analysis_types": ["trends", "correlations", "anomalies"]}
        }
    ],
    execution_mode="parallel"  # Steps 0-2 run in parallel
)

print(f"Processed data in {workflow['total_duration_ms']}ms")
print(f"Parallelization saved {workflow['metadata']['time_saved_ms']}ms")