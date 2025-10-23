# Source: api/registry-api.md
# Line: 100
# Valid syntax: False
# Has imports: False
# Has assignments: False

# Syntax error: expected ':' (<unknown>, line 15)

async def create_agent(
    agent_id: str,
    agent_type: str,
    name: str,
    display_name: str,
    category: str,
    description: str,
    file_path: str,
    capabilities: Optional[List[str]] = None,
    tools: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
    embedding: Optional[List[float]] = None,
    estimated_tokens: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> UUID