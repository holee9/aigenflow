"""
Tests for batch processing module following SPEC-ENHANCE-004 Phase 2 requirements.

This module tests:
- FR-3: Batch queue management
- US-2: Batch processing for request grouping
- Phase 2 integration (Gemini + Perplexity parallel)
- Fallback mechanism
"""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.agents.base import AgentRequest, AgentResponse
from src.batch.processor import BatchProcessor
from src.batch.queue import BatchQueue, BatchRequest
from src.core.models import AgentType


class TestBatchRequest:
    """Test BatchRequest model."""

    def test_create_batch_request(self):
        """Test creating a batch request."""
        agent_request = AgentRequest(
            task_name="test_task",
            prompt="Test prompt",
            timeout=120,
        )

        batch_req = BatchRequest(
            request_id=str(uuid4()),
            agent_type=AgentType.GEMINI,
            request=agent_request,
        )

        assert batch_req.agent_type == AgentType.GEMINI
        assert batch_req.request.task_name == "test_task"
        assert batch_req.created_at is not None


class TestBatchQueue:
    """Test BatchQueue following FR-3 requirements."""

    def test_enqueue_request(self):
        """Test enqueuing a request."""
        queue = BatchQueue(max_batch_size=5)

        request = AgentRequest(
            task_name="test_task",
            prompt="Test prompt",
            timeout=120,
        )

        request_id = queue.enqueue(
            agent_type=AgentType.GEMINI,
            request=request,
        )

        assert request_id is not None
        assert len(queue._queue) == 1
        assert queue._queue[0].agent_type == AgentType.GEMINI

    def test_enqueue_multiple_requests(self):
        """Test enqueuing multiple requests."""
        queue = BatchQueue(max_batch_size=5)

        for i in range(3):
            request = AgentRequest(
                task_name=f"task_{i}",
                prompt=f"Prompt {i}",
                timeout=120,
            )
            queue.enqueue(agent_type=AgentType.GEMINI, request=request)

        assert len(queue._queue) == 3

    def test_max_batch_size_limit(self):
        """Test max batch size is enforced."""
        queue = BatchQueue(max_batch_size=3)

        # Enqueue more than max_batch_size
        for i in range(5):
            request = AgentRequest(
                task_name=f"task_{i}",
                prompt=f"Prompt {i}",
                timeout=120,
            )
            queue.enqueue(agent_type=AgentType.GEMINI, request=request)

        # Should only have max_batch_size items
        assert len(queue._queue) == 3

    def test_get_batch_returns_grouped_requests(self):
        """Test get_batch groups requests by agent type."""
        queue = BatchQueue(max_batch_size=10)

        # Enqueue Gemini requests
        for i in range(2):
            request = AgentRequest(
                task_name=f"gemini_task_{i}",
                prompt=f"Gemini prompt {i}",
                timeout=120,
            )
            queue.enqueue(agent_type=AgentType.GEMINI, request=request)

        # Enqueue Perplexity requests
        for i in range(2):
            request = AgentRequest(
                task_name=f"perplexity_task_{i}",
                prompt=f"Perplexity prompt {i}",
                timeout=120,
            )
            queue.enqueue(agent_type=AgentType.PERPLEXITY, request=request)

        batches = queue.get_batches()

        # Should have 2 batches (one per agent type)
        assert len(batches) == 2

        # Check Gemini batch
        gemini_batch = next((b for b in batches if b["agent_type"] == AgentType.GEMINI), None)
        assert gemini_batch is not None
        assert len(gemini_batch["requests"]) == 2

        # Check Perplexity batch
        perplexity_batch = next(
            (b for b in batches if b["agent_type"] == AgentType.PERPLEXITY), None
        )
        assert perplexity_batch is not None
        assert len(perplexity_batch["requests"]) == 2

    def test_clear_queue(self):
        """Test clearing the queue."""
        queue = BatchQueue(max_batch_size=5)

        # Enqueue some requests
        for i in range(3):
            request = AgentRequest(
                task_name=f"task_{i}",
                prompt=f"Prompt {i}",
                timeout=120,
            )
            queue.enqueue(agent_type=AgentType.GEMINI, request=request)

        assert len(queue._queue) == 3

        # Clear
        queue.clear()

        assert len(queue._queue) == 0

    def test_queue_size(self):
        """Test getting queue size."""
        queue = BatchQueue(max_batch_size=5)

        assert queue.size() == 0

        for i in range(3):
            request = AgentRequest(
                task_name=f"task_{i}",
                prompt=f"Prompt {i}",
                timeout=120,
            )
            queue.enqueue(agent_type=AgentType.GEMINI, request=request)

        assert queue.size() == 3


class TestBatchProcessor:
    """Test BatchProcessor following US-2 requirements."""

    @pytest.mark.asyncio
    async def test_process_batch_success(self):
        """Test successful batch processing."""
        # Mock agent router
        mock_router = AsyncMock()
        mock_response = AgentResponse(
            agent_name=AgentType.GEMINI,
            task_name="test_task",
            content="Test response",
            success=True,
        )
        mock_router.execute.return_value = mock_response

        processor = BatchProcessor(router=mock_router, max_batch_size=5)

        # Create batch
        batch_requests = []
        for i in range(3):
            req = AgentRequest(
                task_name=f"task_{i}",
                prompt=f"Prompt {i}",
                timeout=120,
            )
            batch_requests.append(
                BatchRequest(
                    request_id=str(uuid4()),
                    agent_type=AgentType.GEMINI,
                    request=req,
                )
            )

        # Process batch
        responses = await processor._process_gemini_batch(batch_requests)

        assert len(responses) == 3
        assert all(r.success for r in responses)
        assert mock_router.execute.call_count == 3

    @pytest.mark.asyncio
    async def test_process_batch_with_failure(self):
        """Test batch processing with some failures."""
        # Mock agent router that fails on second request
        mock_router = AsyncMock()

        def side_effect_fn(*args, **kwargs):
            if mock_router.execute.call_count == 2:
                return AgentResponse(
                    agent_name=AgentType.GEMINI,
                    task_name="test_task",
                    content="",
                    success=False,
                    error="API error",
                )
            return AgentResponse(
                agent_name=AgentType.GEMINI,
                task_name="test_task",
                content="Test response",
                success=True,
            )

        mock_router.execute.side_effect = side_effect_fn

        processor = BatchProcessor(router=mock_router, max_batch_size=5)

        # Create batch
        batch_requests = []
        for i in range(3):
            req = AgentRequest(
                task_name=f"task_{i}",
                prompt=f"Prompt {i}",
                timeout=120,
            )
            batch_requests.append(
                BatchRequest(
                    request_id=str(uuid4()),
                    agent_type=AgentType.GEMINI,
                    request=req,
                )
            )

        # Process batch
        responses = await processor._process_gemini_batch(batch_requests)

        assert len(responses) == 3
        assert responses[0].success
        assert not responses[1].success
        assert responses[2].success

    @pytest.mark.asyncio
    async def test_enqueue_and_process(self):
        """Test enqueuing and processing requests."""
        # Mock agent router
        mock_router = AsyncMock()
        mock_response = AgentResponse(
            agent_name=AgentType.GEMINI,
            task_name="test_task",
            content="Test response",
            success=True,
        )
        mock_router.execute.return_value = mock_response

        processor = BatchProcessor(router=mock_router, max_batch_size=5)

        # Enqueue requests
        request_ids = []
        for i in range(3):
            req = AgentRequest(
                task_name=f"task_{i}",
                prompt=f"Prompt {i}",
                timeout=120,
            )
            req_id = await processor.enqueue(
                agent_type=AgentType.GEMINI,
                request=req,
            )
            request_ids.append(req_id)

        # Process batch
        responses = await processor.process_batch()

        assert len(responses) == 3
        assert all(r.success for r in responses)

    @pytest.mark.asyncio
    async def test_flush_processes_remaining(self):
        """Test flush processes remaining requests."""
        # Mock agent router
        mock_router = AsyncMock()
        mock_response = AgentResponse(
            agent_name=AgentType.GEMINI,
            task_name="test_task",
            content="Test response",
            success=True,
        )
        mock_router.execute.return_value = mock_response

        processor = BatchProcessor(router=mock_router, max_batch_size=5)

        # Enqueue requests
        for i in range(2):
            req = AgentRequest(
                task_name=f"task_{i}",
                prompt=f"Prompt {i}",
                timeout=120,
            )
            await processor.enqueue(agent_type=AgentType.GEMINI, request=req)

        # Flush
        responses = await processor.flush()

        assert len(responses) == 2
        assert processor.queue.size() == 0

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test getting batch processor statistics."""
        mock_router = AsyncMock()
        processor = BatchProcessor(router=mock_router, max_batch_size=5)

        stats = processor.get_stats()

        assert "total_processed" in stats
        assert "total_batches" in stats
        assert "total_failures" in stats
        assert stats["total_processed"] == 0
        assert stats["total_batches"] == 0
        assert stats["total_failures"] == 0
