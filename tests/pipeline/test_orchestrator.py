"""
Tests for orchestrator layer.
"""

import pytest

from src.pipeline.orchestrator import PipelineOrchestrator
from src.pipeline.state import PipelineState
from src.core.models import PipelineConfig


class TestPipelineState:
    """Tests for PipelineState enum."""

    def test_state_values(self):
        """Test that state values are correct."""
        assert PipelineState.IDLE == "idle"
        assert PipelineState.PHASE_1 == "phase_1"
        assert PipelineState.COMPLETED == "completed"
        assert PipelineState.FAILED == "failed"


class TestPipelineOrchestrator:
    """Tests for PipelineOrchestrator."""

    def test_init(self):
        """Test orchestrator initialization."""
        orchestrator = PipelineOrchestrator(settings=None)
        assert orchestrator is not None

    def test_create_session(self):
        """Test session creation."""
        orchestrator = PipelineOrchestrator(settings=None)

        config = PipelineConfig(
            topic="Test topic",
            doc_type="bizplan",
            template="startup",
        )
        session = orchestrator.create_session(config=config)

        assert session is not None
        assert session.config.topic == "Test topic"

    def test_state_transitions(self):
        """Test state transitions."""
        orchestrator = PipelineOrchestrator(settings=None)

        config = PipelineConfig(
            topic="Test topic",
            doc_type="bizplan",
            template="startup",
        )
        session = orchestrator.create_session(config=config)

        # Start pipeline
        assert session.state == PipelineState.IDLE
        session.state = PipelineState.PHASE_1

        # Complete
        session.state = PipelineState.COMPLETED
        assert session.state == PipelineState.COMPLETED
