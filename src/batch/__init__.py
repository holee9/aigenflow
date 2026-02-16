"""
Batch processing module for AI request optimization following SPEC-ENHANCE-004.

This module provides:
- FR-3: Batch queue management for grouping requests
- US-2: Batch processing to reduce overhead
- Integration with Phase 2 parallel processing (Gemini + Perplexity)
"""

from batch.processor import BatchProcessor
from batch.queue import BatchQueue, BatchRequest

__all__ = [
    "BatchProcessor",
    "BatchQueue",
    "BatchRequest",
]
