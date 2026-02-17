"""
Tests for core data models.
"""


import pytest

from core.models import (
    AgentResponse,
    AgentType,
    DocumentType,
    PhaseResult,
    PhaseStatus,
    PipelineConfig,
    PipelineSession,
    PipelineState,
    create_phase_result,
)


class TestAgentResponse:
    def test_create_success_response(self):
        response = AgentResponse(
            agent_name=AgentType.CLAUDE,
            task_name="brainstorm",
            content="Test content",
            tokens_used=100,
            response_time=1.5,
            success=True,
        )
        assert response.agent_name == AgentType.CLAUDE
        assert response.success is True


class TestPhaseResult:
    def test_create_pending_result(self):
        result = PhaseResult(
            phase_number=1,
            phase_name="Ideation",
            status=PhaseStatus.PENDING,
        )
        assert result.status == PhaseStatus.PENDING


class TestPipelineConfig:
    def test_minimal_config(self):
        config = PipelineConfig(topic="Test topic for business plan")
        assert config.topic == "Test topic for business plan"
        assert config.doc_type == DocumentType.BIZPLAN

    def test_topic_validation(self):
        with pytest.raises(ValueError):
            PipelineConfig(topic="short")


class TestPipelineSession:
    def test_create_session(self):
        config = PipelineConfig(topic="Test topic")
        session = PipelineSession(config=config)
        assert len(session.session_id) > 0
        assert session.state == PipelineState.IDLE

    def test_add_result(self):
        config = PipelineConfig(topic="Test topic")
        session = PipelineSession(config=config)
        result = PhaseResult(phase_number=1, phase_name="Test Phase", status=PhaseStatus.COMPLETED)
        session.add_result(result)
        assert len(session.results) == 1


class TestCreatePhaseResult:
    def test_create_pending_phase(self):
        result = create_phase_result(1, "Ideation")
        assert isinstance(result, PhaseResult)
        assert result.phase_number == 1
        assert result.status == PhaseStatus.PENDING
