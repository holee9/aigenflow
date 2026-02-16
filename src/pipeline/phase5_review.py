"""
Phase 5: Review

Final review and refinement phase.
Tasks: VERIFY_PERPLEXITY, FINAL_REVIEW_CLAUDE, POLISH_CLAUDE
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


class Phase5Review(BasePhase):
    """
    Phase 5: Review - Final review and refinement.

    This phase verifies facts with Perplexity, performs final review
    with Claude, and polishes the content.
    """

    def __init__(
        self,
        template_manager: TemplateManager,
        agent_router: AgentRouter,
    ) -> None:
        """
        Initialize Phase 5 with dependencies.

        Args:
            template_manager: Template manager for prompt rendering
            agent_router: Agent router for task execution
        """
        self.template_manager = template_manager
        self.agent_router = agent_router

    def get_phase_number(self) -> int:
        """Return phase number 5."""
        return 5

    def get_tasks(self, session: PipelineSession) -> list[PhaseTask]:
        """
        Get Phase 5 tasks.

        Args:
            session: Current pipeline session

        Returns:
            List of PhaseTask enum values for Phase 5
        """
        return [
            PhaseTask.VERIFY_PERPLEXITY,
            PhaseTask.FINAL_REVIEW_CLAUDE,
            PhaseTask.POLISH_CLAUDE,
        ]

    async def execute(
        self,
        session: PipelineSession,
        config: PipelineConfig,
    ) -> PhaseResult:
        """
        Execute Phase 5: Review.

        Args:
            session: Current pipeline session
            config: Pipeline configuration

        Returns:
            PhaseResult with execution results
        """
        phase_number = self.get_phase_number()
        tasks = self.get_tasks(session)
        phase_name = "Phase 5: Review"
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
                        agent_name=AgentType.PERPLEXITY,
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
        Validate Phase 5 execution result.

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
