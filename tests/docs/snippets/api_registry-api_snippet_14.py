# Source: api/registry-api.md
# Line: 293
# Valid syntax: False
# Has imports: False
# Has assignments: False

# Syntax error: expected ':' (<unknown>, line 5)

async def list_agents(
    category: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Dict[str, Any]]