"""
Phase 1: Framing

Initial brainstorming and concept validation phase.
Tasks: BRAINSTORM_CHATGPT, VALIDATE_CLAUDE
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


class Phase1Framing(BasePhase):
    """
    Phase 1: Framing - Brainstorming and concept validation.

    This phase conducts initial brainstorming with ChatGPT and validates
    the concept with Claude to establish a strong foundation.
    """

    def __init__(
        self,
        template_manager: TemplateManager,
        agent_router: AgentRouter,
    ) -> None:
        """
        Initialize Phase 1 with dependencies.

        Args:
            template_manager: Template manager for prompt rendering
            agent_router: Agent router for task execution
        """
        self.template_manager = template_manager
        self.agent_router = agent_router

    def get_phase_number(self) -> int:
        """Return phase number 1."""
        return 1

    def get_tasks(self, session: PipelineSession) -> list[PhaseTask]:
        """
        Get Phase 1 tasks.

        Args:
            session: Current pipeline session

        Returns:
            List of PhaseTask enum values for Phase 1
        """
        return [PhaseTask.BRAINSTORM_CHATGPT, PhaseTask.VALIDATE_CLAUDE]

    async def execute(
        self,
        session: PipelineSession,
        config: PipelineConfig,
    ) -> PhaseResult:
        """
        Execute Phase 1: Framing.

        Args:
            session: Current pipeline session
            config: Pipeline configuration

        Returns:
            PhaseResult with execution results
        """
        phase_number = self.get_phase_number()
        tasks = self.get_tasks(session)
        phase_name = "Phase 1: Framing"
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
        Validate Phase 1 execution result.

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
