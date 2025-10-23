# Source: api/registry-api.md
# Line: 443
# Valid syntax: False
# Has imports: False
# Has assignments: False

# Syntax error: expected ':' (<unknown>, line 4)

async def bulk_insert_agents(
    agents: List[Dict[str, Any]],
    batch_size: int = 100,
) -> int