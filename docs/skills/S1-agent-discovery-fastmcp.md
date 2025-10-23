# S1: Agent Discovery - FastMCP 2.0 Implementation Guide

## FastMCP 2.0 Integration

This guide shows how to implement Agent Discovery using FastMCP 2.0 with Pydantic models and modern MCP patterns.

**Prerequisites:**
- FastMCP 2.0+ installed
- Pydantic 2.0+ installed
- M01 Tasks 1.1-1.3 completed

---

## Pydantic Models

### Request Models

```python
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from enum import Enum

class AgentCategory(str, Enum):
    """Agent categories for filtering."""
    CORE = "core"
    SPECIALIZED = "specialized"
    INFRASTRUCTURE = "infrastructure"
    ANALYSIS = "analysis"
    SECURITY = "security"
    TESTING = "testing"


class DiscoverAgentsRequest(BaseModel):
    """Request model for discover_agents tool."""

    query: str = Field(
        ...,
        description="Natural language description of desired capabilities",
        min_length=1,
        max_length=500,
        examples=["Python backend development", "database optimization"]
    )

    limit: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of agents to return"
    )

    threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold (0.0-1.0)"
    )

    category_filter: Optional[AgentCategory] = Field(
        default=None,
        description="Optional category filter"
    )

    @field_validator('query')
    @classmethod
    def query_not_empty(cls, v: str) -> str:
        """Ensure query is not just whitespace."""
        if not v.strip():
            raise ValueError('Query cannot be empty or whitespace')
        return v.strip()


class GetAgentDetailsRequest(BaseModel):
    """Request model for get_agent_details tool."""

    agent_id: str = Field(
        ...,
        description="Agent ID or agent type",
        min_length=1,
        examples=["backend-developer", "python-pro", "01-core-backend-developer"]
    )

    @field_validator('agent_id')
    @classmethod
    def agent_id_valid(cls, v: str) -> str:
        """Validate agent_id format."""
        if not v.strip():
            raise ValueError('agent_id cannot be empty')
        return v.strip()
```

### Response Models

```python
from datetime import datetime
from typing import List, Optional, Dict, Any


class AgentMatch(BaseModel):
    """Single agent match result."""

    id: str = Field(..., description="Agent identifier")
    type: str = Field(..., description="Agent type")
    name: str = Field(..., description="Agent display name")
    display_name: str = Field(..., description="Formatted display name")
    category: AgentCategory = Field(..., description="Agent category")
    description: str = Field(..., description="Agent description")

    capabilities: List[str] = Field(
        default_factory=list,
        description="Agent capabilities"
    )

    tools: List[str] = Field(
        default_factory=list,
        description="Tools the agent uses"
    )

    keywords: List[str] = Field(
        default_factory=list,
        description="Keywords for matching"
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Match confidence score"
    )

    match_reason: str = Field(
        ...,
        description="Explanation of why agent matched"
    )

    estimated_tokens: int = Field(
        default=0,
        ge=0,
        description="Estimated token count for agent"
    )

    avg_response_time_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Average response time in milliseconds"
    )


class DiscoverAgentsResponse(BaseModel):
    """Response model for discover_agents tool."""

    success: bool = Field(default=True, description="Request success status")
    query: str = Field(..., description="Original query")

    agents: List[AgentMatch] = Field(
        default_factory=list,
        description="Matching agents"
    )

    total_count: int = Field(
        ...,
        ge=0,
        description="Total number of matches"
    )

    processing_time_ms: float = Field(
        ...,
        ge=0.0,
        description="Processing time in milliseconds"
    )


class AgentDetailsMetadata(BaseModel):
    """Agent metadata."""

    dependencies: List[str] = Field(
        default_factory=list,
        description="Agent dependencies"
    )

    examples: List[str] = Field(
        default_factory=list,
        description="Example use cases"
    )

    tags: List[str] = Field(
        default_factory=list,
        description="Additional tags"
    )


class AgentDetails(BaseModel):
    """Detailed agent information."""

    id: str
    type: str
    name: str
    display_name: str
    category: AgentCategory
    description: str
    capabilities: List[str]
    tools: List[str]
    keywords: List[str]

    file_path: str = Field(..., description="Path to agent definition file")
    estimated_tokens: int
    avg_response_time_ms: float

    success_rate: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Historical success rate"
    )

    usage_count: int = Field(
        default=0,
        ge=0,
        description="Number of times agent has been used"
    )

    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Agent creation timestamp"
    )

    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Last update timestamp"
    )

    last_used_at: Optional[datetime] = Field(
        default=None,
        description="Last usage timestamp"
    )


class GetAgentDetailsResponse(BaseModel):
    """Response model for get_agent_details tool."""

    success: bool = Field(default=True)
    agent: AgentDetails = Field(..., description="Agent details")
    metadata: AgentDetailsMetadata = Field(
        default_factory=AgentDetailsMetadata,
        description="Additional metadata"
    )
```

---

## FastMCP Tool Implementation

### Tool Definition

```python
from fastmcp import FastMCP
from fastmcp.tools import Tool

# Initialize FastMCP server
mcp = FastMCP("Mycelium Agent Discovery")


@mcp.tool()
async def discover_agents(
    request: DiscoverAgentsRequest
) -> DiscoverAgentsResponse:
    """
    Discover agents using natural language query.

    This tool enables Claude Code to find appropriate agents based on
    task descriptions, capabilities, or domain expertise.

    Args:
        request: Discovery request with query and filters

    Returns:
        Matching agents with confidence scores

    Example:
        >>> request = DiscoverAgentsRequest(
        ...     query="Python backend development",
        ...     limit=5,
        ...     threshold=0.7
        ... )
        >>> response = await discover_agents(request)
        >>> print(response.agents[0].name)
        "Backend Developer"
    """
    import time
    from mycelium_core.agent_discovery import AgentDiscoveryService

    start_time = time.perf_counter()

    # Initialize discovery service
    service = AgentDiscoveryService()

    # Execute search
    matches = await service.search(
        query=request.query,
        limit=request.limit,
        threshold=request.threshold,
        category_filter=request.category_filter.value if request.category_filter else None
    )

    # Convert to response model
    agents = [
        AgentMatch(
            id=match["id"],
            type=match["type"],
            name=match["name"],
            display_name=match["display_name"],
            category=match["category"],
            description=match["description"],
            capabilities=match.get("capabilities", []),
            tools=match.get("tools", []),
            keywords=match.get("keywords", []),
            confidence=match["confidence"],
            match_reason=match["match_reason"],
            estimated_tokens=match.get("estimated_tokens", 0),
            avg_response_time_ms=match.get("avg_response_time_ms", 0.0)
        )
        for match in matches
    ]

    processing_time_ms = (time.perf_counter() - start_time) * 1000

    return DiscoverAgentsResponse(
        success=True,
        query=request.query,
        agents=agents,
        total_count=len(agents),
        processing_time_ms=processing_time_ms
    )


@mcp.tool()
async def get_agent_details(
    request: GetAgentDetailsRequest
) -> GetAgentDetailsResponse:
    """
    Get detailed information about a specific agent.

    This tool retrieves comprehensive metadata about an agent including
    capabilities, performance metrics, and usage statistics.

    Args:
        request: Request with agent_id

    Returns:
        Detailed agent information

    Example:
        >>> request = GetAgentDetailsRequest(agent_id="backend-developer")
        >>> response = await get_agent_details(request)
        >>> print(response.agent.description)
        "Expert in full-stack backend development..."
    """
    from mycelium_core.agent_discovery import AgentDiscoveryService

    service = AgentDiscoveryService()

    # Fetch agent details
    details = await service.get_details(request.agent_id)

    if not details:
        raise ValueError(f"Agent not found: {request.agent_id}")

    # Convert to response model
    agent = AgentDetails(
        id=details["id"],
        type=details["type"],
        name=details["name"],
        display_name=details["display_name"],
        category=details["category"],
        description=details["description"],
        capabilities=details.get("capabilities", []),
        tools=details.get("tools", []),
        keywords=details.get("keywords", []),
        file_path=details["file_path"],
        estimated_tokens=details.get("estimated_tokens", 0),
        avg_response_time_ms=details.get("avg_response_time_ms", 0.0),
        success_rate=details.get("success_rate", 0.95),
        usage_count=details.get("usage_count", 0),
        created_at=details.get("created_at", datetime.now(UTC)),
        updated_at=details.get("updated_at", datetime.now(UTC)),
        last_used_at=details.get("last_used_at")
    )

    metadata = AgentDetailsMetadata(
        dependencies=details.get("dependencies", []),
        examples=details.get("examples", []),
        tags=details.get("tags", [])
    )

    return GetAgentDetailsResponse(
        success=True,
        agent=agent,
        metadata=metadata
    )


# Error handling middleware
@mcp.error_handler()
async def handle_discovery_error(error: Exception) -> Dict[str, Any]:
    """Handle discovery errors gracefully."""
    import logging

    logger = logging.getLogger("mycelium.discovery")
    logger.error(f"Discovery error: {error}", exc_info=True)

    return {
        "success": False,
        "error": str(error),
        "error_type": type(error).__name__
    }
```

---

## Service Implementation

### Agent Discovery Service

```python
from typing import List, Dict, Any, Optional
from mycelium_core.registry import AgentRegistry
from mycelium_core.matching import NLPMatcher


class AgentDiscoveryService:
    """Agent discovery service with NLP matching."""

    def __init__(self):
        """Initialize discovery service."""
        self.registry = AgentRegistry()
        self.matcher = NLPMatcher()

    async def search(
        self,
        query: str,
        limit: int = 5,
        threshold: float = 0.6,
        category_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for agents matching query.

        Args:
            query: Search query
            limit: Maximum results
            threshold: Minimum confidence
            category_filter: Optional category

        Returns:
            List of matching agents with scores
        """
        # Get all agents from registry
        agents = await self.registry.get_all_agents()

        # Filter by category if specified
        if category_filter:
            agents = [a for a in agents if a.get("category") == category_filter]

        # Generate embeddings and compute similarity
        matches = await self.matcher.match(
            query=query,
            candidates=agents,
            threshold=threshold
        )

        # Sort by confidence and limit results
        matches.sort(key=lambda m: m["confidence"], reverse=True)
        matches = matches[:limit]

        return matches

    async def get_details(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed agent information.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent details or None if not found
        """
        return await self.registry.get_agent(agent_id)
```

### NLP Matcher

```python
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class NLPMatcher:
    """NLP-based agent matching using sentence embeddings."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize matcher with sentence transformer.

        Args:
            model_name: HuggingFace model name
        """
        self.model = SentenceTransformer(model_name)
        self.agent_embeddings = {}

    async def match(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        threshold: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        Match query against candidate agents.

        Args:
            query: Search query
            candidates: Agent candidates
            threshold: Minimum confidence

        Returns:
            Matched agents with confidence scores
        """
        # Generate query embedding
        query_embedding = self.model.encode([query])[0]

        matches = []
        for agent in candidates:
            # Generate or retrieve agent embedding
            agent_key = agent["id"]
            if agent_key not in self.agent_embeddings:
                agent_text = self._prepare_agent_text(agent)
                agent_embedding = self.model.encode([agent_text])[0]
                self.agent_embeddings[agent_key] = agent_embedding
            else:
                agent_embedding = self.agent_embeddings[agent_key]

            # Compute similarity
            similarity = cosine_similarity(
                [query_embedding],
                [agent_embedding]
            )[0][0]

            # Apply threshold
            if similarity >= threshold:
                matches.append({
                    **agent,
                    "confidence": float(similarity),
                    "match_reason": self._explain_match(query, agent, similarity)
                })

        return matches

    def _prepare_agent_text(self, agent: Dict[str, Any]) -> str:
        """
        Prepare agent text for embedding.

        Args:
            agent: Agent metadata

        Returns:
            Combined text representation
        """
        parts = [
            agent.get("name", ""),
            agent.get("description", ""),
            " ".join(agent.get("capabilities", [])),
            " ".join(agent.get("keywords", []))
        ]
        return " ".join(filter(None, parts))

    def _explain_match(
        self,
        query: str,
        agent: Dict[str, Any],
        score: float
    ) -> str:
        """
        Generate match explanation.

        Args:
            query: Search query
            agent: Agent metadata
            score: Similarity score

        Returns:
            Human-readable explanation
        """
        query_words = set(query.lower().split())
        agent_keywords = set(agent.get("keywords", []))

        matches = query_words.intersection(agent_keywords)

        if matches:
            return f"Matches keywords: {', '.join(matches)}"
        else:
            return agent.get("description", "")[:100]
```

---

## Usage Examples

### Basic Discovery

```python
from mycelium_core.mcp.tools.discovery_tools import discover_agents, DiscoverAgentsRequest

# Create request
request = DiscoverAgentsRequest(
    query="Python backend API development",
    limit=5,
    threshold=0.7
)

# Execute discovery
response = await discover_agents(request)

# Process results
print(f"Found {response.total_count} agents in {response.processing_time_ms}ms")
for agent in response.agents:
    print(f"{agent.name} (confidence: {agent.confidence:.2f})")
    print(f"  Reason: {agent.match_reason}")
```

### Type-Safe Discovery

```python
from typing import List

async def find_best_agent(task: str) -> Optional[AgentMatch]:
    """Find best agent for task with type safety."""
    request = DiscoverAgentsRequest(
        query=task,
        limit=1,
        threshold=0.8
    )

    response: DiscoverAgentsResponse = await discover_agents(request)

    if response.agents:
        return response.agents[0]
    else:
        return None

# Usage
best_agent = await find_best_agent("database performance optimization")
if best_agent:
    print(f"Using: {best_agent.name}")
```

### Category Filtering

```python
async def find_security_agents(task: str) -> List[AgentMatch]:
    """Find security-focused agents."""
    request = DiscoverAgentsRequest(
        query=task,
        limit=5,
        threshold=0.6,
        category_filter=AgentCategory.SECURITY
    )

    response = await discover_agents(request)
    return response.agents

# Usage
security_experts = await find_security_agents("authentication audit")
```

---

## Testing with Pydantic

### Request Validation Tests

```python
import pytest
from pydantic import ValidationError


def test_discover_agents_request_validation():
    """Test request model validation."""

    # Valid request
    request = DiscoverAgentsRequest(
        query="Python development",
        limit=5
    )
    assert request.query == "Python development"
    assert request.limit == 5
    assert request.threshold == 0.6  # default

    # Invalid: empty query
    with pytest.raises(ValidationError):
        DiscoverAgentsRequest(query="")

    # Invalid: limit out of range
    with pytest.raises(ValidationError):
        DiscoverAgentsRequest(query="test", limit=0)

    with pytest.raises(ValidationError):
        DiscoverAgentsRequest(query="test", limit=100)

    # Invalid: threshold out of range
    with pytest.raises(ValidationError):
        DiscoverAgentsRequest(query="test", threshold=1.5)


def test_get_agent_details_request_validation():
    """Test agent details request validation."""

    # Valid request
    request = GetAgentDetailsRequest(agent_id="backend-developer")
    assert request.agent_id == "backend-developer"

    # Invalid: empty agent_id
    with pytest.raises(ValidationError):
        GetAgentDetailsRequest(agent_id="")
```

### Response Model Tests

```python
def test_agent_match_model():
    """Test agent match model."""
    match = AgentMatch(
        id="test-agent",
        type="test",
        name="Test Agent",
        display_name="Test Agent",
        category=AgentCategory.CORE,
        description="Test description",
        confidence=0.95,
        match_reason="Test match"
    )

    assert match.id == "test-agent"
    assert match.confidence == 0.95
    assert 0.0 <= match.confidence <= 1.0


def test_discover_agents_response_serialization():
    """Test response serialization."""
    response = DiscoverAgentsResponse(
        success=True,
        query="test",
        agents=[],
        total_count=0,
        processing_time_ms=10.5
    )

    # Serialize to dict
    data = response.model_dump()
    assert data["success"] is True
    assert data["query"] == "test"

    # Serialize to JSON
    json_str = response.model_dump_json()
    assert "test" in json_str
```

---

## Configuration

### FastMCP Server Configuration

```python
# config/fastmcp.yaml
server:
  name: "Mycelium Agent Discovery"
  version: "1.0.0"
  description: "Agent discovery with NLP matching"

tools:
  discover_agents:
    enabled: true
    timeout_seconds: 30
    rate_limit: 100  # requests per minute

  get_agent_details:
    enabled: true
    timeout_seconds: 10
    rate_limit: 200

registry:
  database_url: "postgresql://localhost:5432/mycelium_registry"
  cache_ttl_seconds: 3600
  embeddings_cache_size: 1000

nlp:
  model: "all-MiniLM-L6-v2"
  batch_size: 32
  device: "cpu"  # or "cuda"
```

### Environment Variables

```bash
# .env
DISCOVERY_API_URL=http://localhost:8000
DISCOVERY_TIMEOUT_SECONDS=30
DISCOVERY_CACHE_SIZE=100

# NLP Configuration
NLP_MODEL_NAME=all-MiniLM-L6-v2
NLP_DEVICE=cpu
NLP_BATCH_SIZE=32

# Database
DATABASE_URL=postgresql://localhost:5432/mycelium_registry
```

---

## Performance Optimization

### Caching Strategy

```python
from functools import lru_cache
from typing import Dict, Any

class CachedNLPMatcher(NLPMatcher):
    """NLP matcher with LRU caching."""

    @lru_cache(maxsize=1000)
    def _get_query_embedding(self, query: str) -> np.ndarray:
        """Cache query embeddings."""
        return self.model.encode([query])[0]

    async def match(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        threshold: float = 0.6
    ) -> List[Dict[str, Any]]:
        """Match with cached embeddings."""
        # Use cached query embedding
        query_embedding = self._get_query_embedding(query)

        # Rest of matching logic...
```

### Batch Processing

```python
async def batch_discover(
    queries: List[str],
    limit: int = 5
) -> List[DiscoverAgentsResponse]:
    """Batch process multiple discovery queries."""
    import asyncio

    requests = [
        DiscoverAgentsRequest(query=q, limit=limit)
        for q in queries
    ]

    # Process in parallel
    responses = await asyncio.gather(*[
        discover_agents(req) for req in requests
    ])

    return responses

# Usage
queries = ["Python dev", "database optimization", "security audit"]
results = await batch_discover(queries)
```

---

## Monitoring and Telemetry

### Metrics Collection

```python
from mycelium_analytics import TelemetryCollector

class InstrumentedDiscoveryService(AgentDiscoveryService):
    """Discovery service with telemetry."""

    def __init__(self):
        super().__init__()
        self.telemetry = TelemetryCollector()

    async def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Search with telemetry."""
        import time

        start = time.perf_counter()

        try:
            results = await super().search(query, **kwargs)

            # Record success metrics
            self.telemetry.record_event(
                event_type="discovery_search",
                data={
                    "query": query,
                    "results_count": len(results),
                    "latency_ms": (time.perf_counter() - start) * 1000,
                    "success": True
                }
            )

            return results

        except Exception as e:
            # Record failure metrics
            self.telemetry.record_event(
                event_type="discovery_search",
                data={
                    "query": query,
                    "latency_ms": (time.perf_counter() - start) * 1000,
                    "success": False,
                    "error": str(e)
                }
            )
            raise
```

---

## Migration Guide

### From Legacy to FastMCP

```python
# Before (Legacy)
from scripts.agent_discovery import AgentDiscovery

discovery = AgentDiscovery()
results = discovery.search("Python development")

# After (FastMCP)
from mycelium_core.mcp.tools.discovery_tools import discover_agents, DiscoverAgentsRequest

request = DiscoverAgentsRequest(query="Python development")
response = await discover_agents(request)
results = [agent.model_dump() for agent in response.agents]
```

---

## References

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [S1 Agent Discovery](/home/gerald/git/mycelium/docs/skills/S1-agent-discovery.md)
- [M01 Milestone](/home/gerald/git/mycelium/docs/projects/claude-code-skills/milestones/M01_AGENT_DISCOVERY_SKILLS.md)

---

**Last Updated:** 2025-10-21
**FastMCP Version:** 2.0+
**Pydantic Version:** 2.0+
