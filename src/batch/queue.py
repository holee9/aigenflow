"""
Batch queue for AI request optimization following SPEC-ENHANCE-004 FR-3.

Provides request queuing and batching functionality:
- Request enqueue with agent type grouping
- Configurable max batch size (default: 5)
- Batch grouping by agent type
- Queue management (clear, size)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from agents.base import AgentRequest
from core.models import AgentType


@dataclass
class BatchRequest:
    """
    A queued request for batch processing.

    Attributes:
        request_id: Unique identifier for this request
        agent_type: AI agent type (Gemini, Perplexity, etc.)
        request: Original agent request
        created_at: Timestamp when request was enqueued
    """

    request_id: str
    agent_type: AgentType
    request: AgentRequest
    created_at: datetime = field(default_factory=datetime.now)


class BatchQueue:
    """
    Queue for batching AI requests by agent type.

    Responsibilities:
    - Enqueue requests with agent type
    - Group requests by agent type for batch processing
    - Enforce maximum batch size
    - Provide queue management operations

    Reference: SPEC-ENHANCE-004 FR-3
    """

    DEFAULT_MAX_BATCH_SIZE = 5

    def __init__(self, max_batch_size: int = DEFAULT_MAX_BATCH_SIZE) -> None:
        """
        Initialize batch queue.

        Args:
            max_batch_size: Maximum number of requests per batch (default: 5)
        """
        self.max_batch_size = max_batch_size
        self._queue: list[BatchRequest] = []

    def enqueue(
        self,
        agent_type: AgentType,
        request: AgentRequest,
    ) -> str:
        """
        Enqueue a request for batch processing.

        Args:
            agent_type: AI agent type
            request: Agent request to batch

        Returns:
            Request ID for tracking
        """
        # Check if adding would exceed max size
        if len(self._queue) >= self.max_batch_size:
            # Queue is full, return None to indicate rejection
            return ""

        # Create batch request
        batch_req = BatchRequest(
            request_id=str(uuid4()),
            agent_type=agent_type,
            request=request,
        )

        self._queue.append(batch_req)
        return batch_req.request_id

    def get_batches(self) -> list[dict[str, Any]]:
        """
        Get grouped batches ready for processing.

        Returns:
            List of batch dictionaries grouped by agent_type
            Format: [{"agent_type": AgentType, "requests": [BatchRequest, ...]}]
        """
        # Group by agent type
        batches: dict[AgentType, list[BatchRequest]] = {}

        for req in self._queue:
            if req.agent_type not in batches:
                batches[req.agent_type] = []
            batches[req.agent_type].append(req)

        # Convert to list format
        return [
            {"agent_type": agent_type, "requests": requests}
            for agent_type, requests in batches.items()
        ]

    def clear(self) -> None:
        """Clear all queued requests."""
        self._queue.clear()

    def size(self) -> int:
        """
        Get current queue size.

        Returns:
            Number of queued requests
        """
        return len(self._queue)

    def remove_processed(self, request_ids: list[str]) -> None:
        """
        Remove processed requests from queue.

        Args:
            request_ids: List of request IDs to remove
        """
        ids_set = set(request_ids)
        self._queue = [req for req in self._queue if req.request_id not in ids_set]
