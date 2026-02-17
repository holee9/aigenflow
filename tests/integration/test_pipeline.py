"""
Integration tests for pipeline workflow.
"""

from pathlib import Path

import pytest

from agents.base import AgentRequest, AgentResponse, AsyncAgent
from core.models import AgentType, PipelineConfig, PipelineState
from pipeline.orchestrator import PipelineOrchestrator


class _DummyGateway:
    pass


class _SuccessAgent(AsyncAgent):
    def __init__(self, name: str) -> None:
        super().__init__(gateway_provider=_DummyGateway())
        self._name = name

    async def execute(self, request: AgentRequest) -> AgentResponse:
        return AgentResponse(
            agent_name=self._name,
            task_name=request.task_name,
            content="ok",
            success=True,
        )


class _FailingAgent(AsyncAgent):
    def __init__(self, error: str) -> None:
        super().__init__(gateway_provider=_DummyGateway())
        self._error = error

    async def execute(self, request: AgentRequest) -> AgentResponse:
        raise RuntimeError(self._error)


class TestPipelineWorkflow:
    """Integration tests for complete pipeline."""

    def test_full_pipeline_flow(self):
        """Test complete pipeline flow end-to-end."""
        orchestrator = PipelineOrchestrator(settings=None)

        config = PipelineConfig(
            topic="AI SaaS Platform for enterprise",
            doc_type="bizplan",
            template="startup",
        )

        session = orchestrator.create_session(config=config)

        # Execute pipeline (this would take a long time with real AI calls)
        # For now, just test structure
        assert session is not None
        assert session.config.topic == "AI SaaS Platform for enterprise"

    @pytest.mark.anyio
    async def test_pipeline_runs_all_phases_and_persists_state(self, tmp_path: Path):
        orchestrator = PipelineOrchestrator(settings=None)
        orchestrator.agent_router.register_agent(AgentType.CHATGPT, _SuccessAgent("chatgpt"))
        orchestrator.agent_router.register_agent(AgentType.CLAUDE, _SuccessAgent("claude"))
        orchestrator.agent_router.register_agent(AgentType.GEMINI, _SuccessAgent("gemini"))
        orchestrator.agent_router.register_agent(AgentType.PERPLEXITY, _SuccessAgent("perplexity"))

        config = PipelineConfig(
            topic="Integration topic for full pipeline",
            output_dir=tmp_path,
        )
        session = await orchestrator.run_pipeline(config)
        output_dir = tmp_path / session.session_id

        assert session.state == PipelineState.COMPLETED
        assert session.current_phase == 5
        assert (output_dir / "pipeline_state.json").exists()
        assert (output_dir / "phase1_results.json").exists()
        assert (output_dir / "phase5_results.json").exists()

    @pytest.mark.anyio
    async def test_pipeline_stops_early_on_failure(self, tmp_path: Path):
        orchestrator = PipelineOrchestrator(settings=None)
        orchestrator.agent_router.register_agent(AgentType.CHATGPT, _SuccessAgent("chatgpt"))
        orchestrator.agent_router.register_agent(AgentType.CLAUDE, _FailingAgent("phase1 fail"))
        orchestrator.agent_router.register_agent(AgentType.GEMINI, _SuccessAgent("gemini"))
        orchestrator.agent_router.register_agent(AgentType.PERPLEXITY, _SuccessAgent("perplexity"))

        config = PipelineConfig(
            topic="Integration topic for failing pipeline",
            output_dir=tmp_path,
        )
        session = await orchestrator.run_pipeline(config)
        output_dir = tmp_path / session.session_id

        assert session.state == PipelineState.FAILED
        assert session.current_phase == 1
        assert (output_dir / "pipeline_state.json").exists()
        assert (output_dir / "phase1_results.json").exists()
