"""
Pipeline orchestration modules.
"""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from src.core.exceptions import PipelineException, ErrorCode
from src.core.models import (
    PhaseResult,
    PhaseStatus,
    PipelineConfig,
    PipelineSession,
    PipelineState,
    create_phase_result,
)
from src.agents.router import AgentRouter, AgentMapping, PhaseTask
from src.gateway.session import SessionManager
from src.templates.manager import TemplateManager
from src.output.formatter import MarkdownFormatter, FileExporter


class PipelineOrchestrator:
    """
    Orchestrates pipeline execution with state machine and event system.

    Implements state transitions: IDLE -> PHASE_1 -> ... -> COMPLETED/FAILED
    """

    def __init__(
        self,
        settings: Any = None,
        template_manager: TemplateManager | None = None,
        session_manager: SessionManager | None = None,
    ) -> None:
        """Initialize orchestrator with dependencies."""
        self.settings = settings
        self.template_manager = template_manager or TemplateManager()
        self.session_manager = session_manager or SessionManager()
        self.agent_router = AgentRouter(settings)
        self.current_session: PipelineSession | None = None

    def create_session(self, config: PipelineConfig) -> PipelineSession:
        """Create a new pipeline session."""
        return PipelineSession(config=config)

    async def execute_phase(self, session: PipelineSession, phase_number: int) -> PhaseResult:
        """
        Execute a single pipeline phase.

        Args:
            session: Current pipeline session
            phase_number: Phase to execute (1-5)

        Returns:
            PhaseResult with execution results
        """
        # TODO: Implement phase execution logic
        # 1. Get phase template
        # 2. Render prompts
        # 3. Call agents via router
        # 4. Aggregate results
        # 5. Update session state

        return create_phase_result(phase_number, f"Phase {phase_number}")

    async def run_pipeline(self, config: PipelineConfig) -> PipelineSession:
        """
        Run complete pipeline from start to finish.

        Args:
            config: Pipeline configuration

        Returns:
            PipelineSession with all results
        """
        session = self.create_session(config)
        self.current_session = session

        # Execute phases sequentially
        for phase_num in range(1, 6):
            result = await self.execute_phase(session, phase_num)
            session.add_result(result)

            # Update state
            if result.status == PhaseStatus.COMPLETED:
                session.state = PipelineState(f"phase_{phase_num}")
            elif result.status == PhaseStatus.FAILED:
                session.state = PipelineState.FAILED
                break

        # Final state
        if session.current_phase == 5:
            session.state = PipelineState.COMPLETED
        else:
            session.state = PipelineState.FAILED

        return session
