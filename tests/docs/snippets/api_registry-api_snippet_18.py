# Source: api/registry-api.md
# Line: 357
# Valid syntax: False
# Has imports: False
# Has assignments: False

# Syntax error: expected ':' (<unknown>, line 5)

async def similarity_search(
    embedding: List[float],
    limit: int = 10,
    threshold: float = 0.5,
) -> List[Tuple[Dict[str, Any], float]]