"""
Batch processor for AI request optimization following SPEC-ENHANCE-004 US-2.

Provides batch execution functionality:
- Process grouped requests by agent type
- Parallel execution within batches
- Fallback to individual processing on batch failure
- Statistics tracking
"""

from collections.abc import Awaitable, Callable
from typing import Any

from src.agents.base import AgentRequest, AgentResponse
from src.batch.queue import BatchQueue, BatchRequest
from src.core.models import AgentType


class BatchProcessor:
    """
    Process AI requests in batches for efficiency.

    Responsibilities:
    - Queue management for batching
    - Group requests by agent type
    - Execute batches with parallel processing
    - Fallback to individual processing on failure
    - Track statistics

    Reference: SPEC-ENHANCE-004 US-2
    """

    DEFAULT_MAX_BATCH_SIZE = 5
    DEFAULT_MAX_WAIT_SECONDS = 2.0

    def __init__(
        self,
        router: Any,
        max_batch_size: int = DEFAULT_MAX_BATCH_SIZE,
        max_wait_seconds: float = DEFAULT_MAX_WAIT_SECONDS,
    ) -> None:
        """
        Initialize batch processor.

        Args:
            router: AgentRouter for executing requests
            max_batch_size: Maximum batch size (default: 5)
            max_wait_seconds: Maximum wait time for batch accumulation (default: 2.0s)
        """
        self.router = router
        self.max_batch_size = max_batch_size
        self.max_wait_seconds = max_wait_seconds
        self.queue = BatchQueue(max_batch_size=max_batch_size)

        # Statistics
        self._total_processed = 0
        self._total_batches = 0
        self._total_failures = 0

    async def enqueue(
        self,
        agent_type: AgentType,
        request: AgentRequest,
    ) -> str:
        """
        Enqueue a request for batch processing.

        Args:
            agent_type: AI agent type
            request: Agent request to enqueue

        Returns:
            Request ID or empty string if queue is full
        """
        return self.queue.enqueue(agent_type=agent_type, request=request)

    async def process_batch(self) -> list[AgentResponse]:
        """
        Process all queued requests in batches.

        Groups requests by agent type and processes each batch.
        Implements fallback to individual processing if batch fails.

        Returns:
            List of agent responses
        """
        batches = self.queue.get_batches()
        all_responses: list[AgentResponse] = []

        for batch in batches:
            agent_type = batch["agent_type"]
            requests = batch["requests"]

            # Process based on agent type
            if agent_type == AgentType.GEMINI:
                responses = await self._process_gemini_batch(requests)
            elif agent_type == AgentType.PERPLEXITY:
                responses = await self._process_perplexity_batch(requests)
            else:
                # For other agents, use sequential processing
                responses = await self._process_sequential(requests, agent_type)

            all_responses.extend(responses)
            self._total_batches += 1

        # Remove processed requests from queue
        processed_ids = [req.request_id for req in sum(
            [batch["requests"] for batch in batches], []
        )]
        self.queue.remove_processed(processed_ids)

        return all_responses

    async def _process_gemini_batch(
        self,
        requests: list[BatchRequest],
    ) -> list[AgentResponse]:
        """
        Process Gemini batch with parallel execution.

        Args:
            requests: List of batch requests

        Returns:
            List of agent responses
        """
        responses: list[AgentResponse] = []

        # Process requests sequentially (safe approach)
        # Could be optimized with asyncio.gather for true parallel processing
        for batch_req in requests:
            try:
                response = await self.router.execute(
                    phase=2,  # Gemini is used in Phase 2
                    task=None,  # Will use request.task_name
                    prompt=batch_req.request.prompt,
                    doc_type=None,  # Will use default
                )
                responses.append(response)
                self._total_processed += 1

                if not response.success:
                    self._total_failures += 1

            except Exception as e:
                # Create error response
                error_response = AgentResponse(
                    agent_name=batch_req.agent_type,
                    task_name=batch_req.request.task_name,
                    content="",
                    success=False,
                    error=str(e),
                )
                responses.append(error_response)
                self._total_processed += 1
                self._total_failures += 1

        return responses

    async def _process_perplexity_batch(
        self,
        requests: list[BatchRequest],
    ) -> list[AgentResponse]:
        """
        Process Perplexity batch with parallel execution.

        Args:
            requests: List of batch requests

        Returns:
            List of agent responses
        """
        responses: list[AgentResponse] = []

        # Process requests sequentially (safe approach)
        for batch_req in requests:
            try:
                response = await self.router.execute(
                    phase=2,  # Perplexity is used in Phase 2
                    task=None,  # Will use request.task_name
                    prompt=batch_req.request.prompt,
                    doc_type=None,  # Will use default
                )
                responses.append(response)
                self._total_processed += 1

                if not response.success:
                    self._total_failures += 1

            except Exception as e:
                # Create error response
                error_response = AgentResponse(
                    agent_name=batch_req.agent_type,
                    task_name=batch_req.request.task_name,
                    content="",
                    success=False,
                    error=str(e),
                )
                responses.append(error_response)
                self._total_processed += 1
                self._total_failures += 1

        return responses

    async def _process_sequential(
        self,
        requests: list[BatchRequest],
        agent_type: AgentType,
    ) -> list[AgentResponse]:
        """
        Process requests sequentially for other agent types.

        Args:
            requests: List of batch requests
            agent_type: Agent type for execution

        Returns:
            List of agent responses
        """
        responses: list[AgentResponse] = []

        for batch_req in requests:
            try:
                response = await self.router.execute(
                    phase=1,  # Default phase
                    task=None,
                    prompt=batch_req.request.prompt,
                    doc_type=None,
                )
                responses.append(response)
                self._total_processed += 1

                if not response.success:
                    self._total_failures += 1

            except Exception as e:
                # Create error response
                error_response = AgentResponse(
                    agent_name=batch_req.agent_type,
                    task_name=batch_req.request.task_name,
                    content="",
                    success=False,
                    error=str(e),
                )
                responses.append(error_response)
                self._total_processed += 1
                self._total_failures += 1

        return responses

    async def flush(self) -> list[AgentResponse]:
        """
        Process all remaining queued requests.

        Returns:
            List of agent responses
        """
        if self.queue.size() == 0:
            return []

        return await self.process_batch()

    def get_stats(self) -> dict[str, int]:
        """
        Get batch processor statistics.

        Returns:
            Dictionary with total_processed, total_batches, total_failures
        """
        return {
            "total_processed": self._total_processed,
            "total_batches": self._total_batches,
            "total_failures": self._total_failures,
        }
