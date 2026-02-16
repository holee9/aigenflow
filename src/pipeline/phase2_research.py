"""
Phase 2: Research

Deep research and fact-checking phase.
Tasks: DEEP_SEARCH_GEMINI, FACT_CHECK_PERPLEXITY

Enhanced with batch processing following SPEC-ENHANCE-004 Phase 2.
"""

from datetime import datetime

from agents.base import AgentRequest
from agents.router import AgentRouter, PhaseTask
from batch.processor import BatchProcessor
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


class Phase2Research(BasePhase):
    """
    Phase 2: Research - Deep research and fact-checking.

    This phase conducts deep research with Gemini and performs
    fact-checking with Perplexity to ensure accuracy.
    """

    def __init__(
        self,
        template_manager: TemplateManager,
        agent_router: AgentRouter,
        enable_batching: bool = False,
        batch_size: int = 5,
    ) -> None:
        """
        Initialize Phase 2 with dependencies.

        Args:
            template_manager: Template manager for prompt rendering
            agent_router: Agent router for task execution
            enable_batching: Enable batch processing for Phase 2 tasks
            batch_size: Maximum batch size (default: 5 per SPEC-ENHANCE-004)
        """
        self.template_manager = template_manager
        self.agent_router = agent_router
        self.enable_batching = enable_batching

        # Initialize batch processor if enabled
        if enable_batching:
            self.batch_processor = BatchProcessor(
                router=agent_router,
                max_batch_size=batch_size,
            )
        else:
            self.batch_processor = None

    def get_phase_number(self) -> int:
        """Return phase number 2."""
        return 2

    def get_tasks(self, session: PipelineSession) -> list[PhaseTask]:
        """
        Get Phase 2 tasks.

        Args:
            session: Current pipeline session

        Returns:
            List of PhaseTask enum values for Phase 2
        """
        return [PhaseTask.DEEP_SEARCH_GEMINI, PhaseTask.FACT_CHECK_PERPLEXITY]

    async def execute(
        self,
        session: PipelineSession,
        config: PipelineConfig,
    ) -> PhaseResult:
        """
        Execute Phase 2: Research.

        Uses batch processing if enabled for parallel Gemini + Perplexity execution.

        Args:
            session: Current pipeline session
            config: Pipeline configuration

        Returns:
            PhaseResult with execution results
        """
        phase_number = self.get_phase_number()
        tasks = self.get_tasks(session)
        phase_name = "Phase 2: Research"
        result = create_phase_result(phase_number, phase_name)

        if not tasks:
            result.status = PhaseStatus.SKIPPED
            result.completed_at = datetime.now()
            return result

        # Choose execution method based on batching configuration
        if self.enable_batching and self.batch_processor:
            responses = await self._execute_with_batching(session, phase_number, tasks)
        else:
            responses = await self._execute_sequential(session, phase_number, tasks)

        failed = any(not response.success for response in responses)

        result.ai_responses = responses
        result.status = PhaseStatus.FAILED if failed else PhaseStatus.COMPLETED
        result.completed_at = datetime.now()
        return result

    async def _execute_sequential(
        self,
        session: PipelineSession,
        phase_number: int,
        tasks: list[PhaseTask],
    ) -> list[AgentResponse]:
        """
        Execute Phase 2 tasks sequentially (original behavior).

        Args:
            session: Current pipeline session
            phase_number: Phase number
            tasks: List of tasks to execute

        Returns:
            List of agent responses
        """
        responses: list[AgentResponse] = []

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
            except Exception as exc:  # pragma: no cover - covered through error path assertions
                responses.append(
                    AgentResponse(
                        agent_name=AgentType.GEMINI,
                        task_name=task.value,
                        content="",
                        success=False,
                        error=str(exc),
                    )
                )

        return responses

    async def _execute_with_batching(
        self,
        session: PipelineSession,
        phase_number: int,
        tasks: list[PhaseTask],
    ) -> list[AgentResponse]:
        """
        Execute Phase 2 tasks with batch processing.

        Enqueues Gemini and Perplexity requests for parallel batch execution.

        Args:
            session: Current pipeline session
            phase_number: Phase number
            tasks: List of tasks to execute

        Returns:
            List of agent responses
        """
        # Clear any previous batch state
        if self.batch_processor:
            self.batch_processor.queue.clear()

        # Enqueue all tasks
        for task in tasks:
            prompt = self.template_manager.render_prompt(
                template_name=self._build_template_name(phase_number, task),
                context={
                    "topic": session.config.topic,
                    "doc_type": session.config.doc_type.value,
                    "language": session.config.language,
                },
            )

            # Determine agent type from task
            agent_type = self._get_agent_type_for_task(task)

            # Create request
            request = AgentRequest(
                task_name=task.value,
                prompt=prompt,
                timeout=session.config.timeout_seconds,
            )

            # Enqueue for batch processing
            await self.batch_processor.enqueue(
                agent_type=agent_type,
                request=request,
            )

        # Process batch
        responses = await self.batch_processor.process_batch()

        # Normalize responses
        normalized_responses: list[AgentResponse] = []
        for response in responses:
            normalized_response = AgentResponse(
                agent_name=AgentType(response.agent_name),
                task_name=response.task_name,
                content=response.content,
                tokens_used=response.tokens_used,
                response_time=response.response_time,
                success=response.success,
                error=response.error,
            )
            normalized_responses.append(normalized_response)

        return normalized_responses

    def _get_agent_type_for_task(self, task: PhaseTask) -> AgentType:
        """
        Get agent type for a given task.

        Args:
            task: PhaseTask enum value

        Returns:
            Corresponding AgentType
        """
        # Map tasks to agent types based on SPEC-PIPELINE-001
        task_to_agent = {
            PhaseTask.DEEP_SEARCH_GEMINI: AgentType.GEMINI,
            PhaseTask.FACT_CHECK_PERPLEXITY: AgentType.PERPLEXITY,
        }
        return task_to_agent.get(task, AgentType.GEMINI)

    def validate_result(self, result: PhaseResult) -> bool:
        """
        Validate Phase 2 execution result.

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
