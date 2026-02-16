"""
Phase 3: Strategy

Strategic analysis and narrative development phase.
Tasks: SWOT_CHATGPT, NARRATIVE_CLAUDE
"""

from datetime import datetime

from agents.router import AgentRouter, PhaseTask
from core.models import (
    AgentResponse,
    AgentType,
    PhaseResult,
    PhaseStatus,
    PipelineConfig,
    PipelineSession,
    create_phase_result,
)
from pipeline.base import BasePhase
from templates.manager import TemplateManager


class Phase3Strategy(BasePhase):
    """
    Phase 3: Strategy - Strategic analysis and narrative development.

    This phase performs SWOT analysis with ChatGPT and develops
    strategic narrative with Claude.
    """

    def __init__(
        self,
        template_manager: TemplateManager,
        agent_router: AgentRouter,
    ) -> None:
        """
        Initialize Phase 3 with dependencies.

        Args:
            template_manager: Template manager for prompt rendering
            agent_router: Agent router for task execution
        """
        self.template_manager = template_manager
        self.agent_router = agent_router

    def get_phase_number(self) -> int:
        """Return phase number 3."""
        return 3

    def get_tasks(self, session: PipelineSession) -> list[PhaseTask]:
        """
        Get Phase 3 tasks.

        Args:
            session: Current pipeline session

        Returns:
            List of PhaseTask enum values for Phase 3
        """
        return [PhaseTask.SWOT_CHATGPT, PhaseTask.NARRATIVE_CLAUDE]

    async def execute(
        self,
        session: PipelineSession,
        config: PipelineConfig,
    ) -> PhaseResult:
        """
        Execute Phase 3: Strategy.

        Args:
            session: Current pipeline session
            config: Pipeline configuration

        Returns:
            PhaseResult with execution results
        """
        phase_number = self.get_phase_number()
        tasks = self.get_tasks(session)
        phase_name = "Phase 3: Strategy"
        result = create_phase_result(phase_number, phase_name)

        if not tasks:
            result.status = PhaseStatus.SKIPPED
            result.completed_at = datetime.now()
            return result

        responses: list[AgentResponse] = []
        failed = False

        for task in tasks:
            prompt = self.template_manager.render_prompt(
                template_name=self._build_template_name(phase_number, task),
                context={
                    "topic": session.config.topic,
                    "doc_type": session.config.doc_type.value,
                    "language": session.config.language,
                },
            )

            try:
                response = await self.agent_router.execute(
                    phase=phase_number,
                    task=task,
                    prompt=prompt,
                    doc_type=session.config.doc_type,
                )
                normalized_response = AgentResponse(
                    agent_name=AgentType(response.agent_name),
                    task_name=response.task_name,
                    content=response.content,
                    tokens_used=response.tokens_used,
                    response_time=response.response_time,
                    success=response.success,
                    error=response.error,
                )
                responses.append(normalized_response)
                if not normalized_response.success:
                    failed = True
            except Exception as exc:  # pragma: no cover - covered through error path assertions
                failed = True
                responses.append(
                    AgentResponse(
                        agent_name=AgentType.CHATGPT,
                        task_name=task.value,
                        content="",
                        success=False,
                        error=str(exc),
                    )
                )

        result.ai_responses = responses
        result.status = PhaseStatus.FAILED if failed else PhaseStatus.COMPLETED
        result.completed_at = datetime.now()
        return result

    def validate_result(self, result: PhaseResult) -> bool:
        """
        Validate Phase 3 execution result.

        Args:
            result: PhaseResult to validate

        Returns:
            True if result is valid, False otherwise
        """
        return result.status == PhaseStatus.COMPLETED

    @staticmethod
    def _build_template_name(phase_number: int, task: PhaseTask) -> str:
        """
        Build template name for task.

        Args:
            phase_number: Phase number
            task: PhaseTask enum value

        Returns:
            Template name string
        """
        return f"phase_{phase_number}/{task.value}"
