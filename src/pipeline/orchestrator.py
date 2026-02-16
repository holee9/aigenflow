"""Pipeline orchestration modules."""

from datetime import datetime
from typing import Any

from src.agents.router import AgentRouter, PhaseTask
from src.context.summarizer import ContextSummary, SummaryConfig
from src.context.tokenizer import TokenCounter
from src.core.models import (
    AgentResponse,
    AgentType,
    PhaseResult,
    PhaseStatus,
    PipelineConfig,
    PipelineSession,
    PipelineState,
    create_phase_result,
)
from src.core.logger import get_logger
from src.gateway.session import SessionManager
from src.output.formatter import FileExporter
from src.pipeline.base import BasePhase
from src.pipeline.phase1_framing import Phase1Framing
from src.pipeline.phase2_research import Phase2Research
from src.pipeline.phase3_strategy import Phase3Strategy
from src.pipeline.phase4_writing import Phase4Writing
from src.pipeline.phase5_review import Phase5Review
from src.templates.manager import TemplateManager

logger = get_logger(__name__)

TOTAL_PHASES = 5


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
        enable_ui: bool = False,
        enable_summarization: bool = True,
        summarization_threshold: float = 0.8,
    ) -> None:
        """
        Initialize orchestrator with dependencies.

        Args:
            settings: Configuration settings
            template_manager: Template manager for prompt rendering
            session_manager: Session manager for browser sessions
            enable_ui: Enable Rich UI components (progress, logging, summary)
            enable_summarization: Enable context summarization (default True)
            summarization_threshold: Token threshold for triggering summarization (default 0.8 = 80%)
        """
        self.settings = settings
        self.template_manager = template_manager or TemplateManager()
        self.session_manager = session_manager or SessionManager()
        self.agent_router = AgentRouter(settings)
        self.current_session: PipelineSession | None = None
        self.enable_ui = enable_ui
        self.enable_summarization = enable_summarization
        self.summarization_threshold = summarization_threshold

        # Initialize context optimization components
        self.token_counter = TokenCounter()
        if self.enable_summarization:
            summary_config = SummaryConfig(enabled=True)
            self.context_summary = ContextSummary(
                agent_router=self.agent_router,
                config=summary_config,
            )
        else:
            self.context_summary = None

        # Initialize phase classes
        self._phases: dict[int, BasePhase] = {
            1: Phase1Framing(self.template_manager, self.agent_router),
            2: Phase2Research(self.template_manager, self.agent_router),
            3: Phase3Strategy(self.template_manager, self.agent_router),
            4: Phase4Writing(self.template_manager, self.agent_router),
            5: Phase5Review(self.template_manager, self.agent_router),
        }

        # Initialize UI components if enabled
        if self.enable_ui:
            from rich.console import Console

            from src.ui.logger import LogStream
            from src.ui.progress import PipelineProgress
            from src.ui.summary import PhaseSummary

            console = Console()
            self.ui_progress = PipelineProgress(console)
            self.ui_logger = LogStream(console)
            self.ui_summary = PhaseSummary(console)
        else:
            self.ui_progress = None
            self.ui_logger = None
            self.ui_summary = None

    def create_session(self, config: PipelineConfig) -> PipelineSession:
        """Create a new pipeline session."""
        return PipelineSession(config=config)

    def get_phase_tasks(self, phase_number: int) -> list[PhaseTask]:
        """
        Return configured tasks for each phase.

        This method is kept for backward compatibility.
        It delegates to the phase classes.

        Args:
            phase_number: Phase number (1-5)

        Returns:
            List of PhaseTask enum values
        """
        phase = self._phases.get(phase_number)
        if phase is None:
            return []

        # Create a dummy session to call get_tasks
        config = PipelineConfig(topic="Dummy topic for getting phase tasks")
        session = PipelineSession(config=config)
        return phase.get_tasks(session)

    def _save_phase_result(self, exporter: FileExporter | None, result: PhaseResult) -> None:
        if exporter is None:
            return
        exporter.save_json(f"phase{result.phase_number}_results", result.model_dump(mode="json"))

    def _save_pipeline_state(self, exporter: FileExporter | None, session: PipelineSession) -> None:
        if exporter is None:
            return
        exporter.save_json("pipeline_state", session.model_dump(mode="json"))

    async def _check_and_summarize_context(
        self,
        session: PipelineSession,
        phase_number: int,
    ) -> None:
        """
        Check token usage and trigger summarization if threshold exceeded.

        Args:
            session: Current pipeline session
            phase_number: Phase about to execute
        """
        try:
            # Determine provider for token limit check
            # Use the first agent's type from the previous phase if available
            provider = "claude"  # Default
            if session.results:
                last_result = session.results[-1]
                if last_result.ai_responses:
                    provider = last_result.ai_responses[0].agent_name.value

            # Check if summarization is needed
            should_summarize = self.context_summary.should_summarize_before_phase(
                session_results=session.results,
                current_phase=phase_number,
                provider=provider,
                threshold=self.summarization_threshold,
            )

            if should_summarize:
                logger.info(
                    f"Token usage threshold ({self.summarization_threshold:.0%}) exceeded before Phase {phase_number}, "
                    "triggering context summarization"
                )

                # Perform summarization
                summary_result = await self.context_summary.summarize_phase_context(
                    session_results=session.results,
                    current_phase=phase_number,
                )

                if summary_result.success:
                    logger.info(
                        f"Context summarized: {summary_result.tokens_original} -> "
                        f"{summary_result.tokens_summary} tokens "
                        f"({summary_result.reduction_ratio:.1%} reduction)"
                    )

                    # Store summary in session artifacts
                    if not hasattr(session, "artifacts"):
                        session.artifacts = {}
                    session.artifacts[f"context_summary_phase_{phase_number}"] = summary_result.get_summary_dict()

                    # Update UI logger if enabled
                    if self.ui_logger:
                        self.ui_logger.info(
                            f"Context summarized before Phase {phase_number}: "
                            f"{summary_result.tokens_original} -> {summary_result.tokens_summary} tokens "
                            f"({summary_result.reduction_ratio:.1%} reduction)"
                        )
                else:
                    logger.warning(f"Context summarization failed: {summary_result.error}")
                    if self.ui_logger:
                        self.ui_logger.warning(f"Context summarization failed: {summary_result.error}")
            else:
                # Log token usage even if not summarizing
                from src.context.tokenizer import TokenCounter

                context = self.context_summary._extract_context_from_results(session.results)
                token_result = TokenCounter().count(context, model_name=provider)
                percentage_used = token_result.get_percentage_used(provider)

                logger.debug(
                    f"Token usage before Phase {phase_number}: {token_result.total_tokens} tokens "
                    f"({percentage_used:.1f}% of {provider} limit)"
                )

        except Exception as exc:
            # Don't fail the pipeline if context optimization fails
            logger.error(f"Error during context optimization check: {exc}")
            if self.ui_logger:
                self.ui_logger.error(f"Context optimization check failed: {exc}")

    @staticmethod
    def _finalize_session_state(session: PipelineSession) -> None:
        if session.state == PipelineState.FAILED:
            return
        if session.current_phase == TOTAL_PHASES:
            session.state = PipelineState.COMPLETED
        else:
            session.state = PipelineState.FAILED

    async def execute_phase(self, session: PipelineSession, phase_number: int) -> PhaseResult:
        """
        Execute a single pipeline phase.

        Args:
            session: Current pipeline session
            phase_number: Phase to execute (1-5)

        Returns:
            PhaseResult with execution results
        """
        # Check token usage and trigger summarization if needed
        if self.enable_summarization and self.context_summary and phase_number > 1:
            await self._check_and_summarize_context(session, phase_number)

        # Get the appropriate phase class
        phase = self._phases.get(phase_number)

        if phase is None:
            # Phase not configured, return skipped result
            result = create_phase_result(phase_number, f"Phase {phase_number}")
            result.status = PhaseStatus.SKIPPED
            result.completed_at = datetime.now()
            return result

        # Log phase start if UI enabled
        if self.ui_logger:
            self.ui_logger.info(f"Starting Phase {phase_number}: {phase.get_phase_number()}")

        # Execute the phase
        result = await phase.execute(session, session.config)

        # Update UI progress if enabled
        if self.ui_progress and phase_number <= 5:
            phase_names = {
                1: "Framing",
                2: "Research",
                3: "Strategy",
                4: "Writing",
                5: "Review",
            }
            # Get first agent from responses for display
            agent_name = "Unknown"
            if result.ai_responses:
                agent_name = result.ai_responses[0].agent_name.value

            self.ui_progress.update_phase(
                phase_number=phase_number,
                phase_name=phase_names.get(phase_number, f"Phase {phase_number}"),
                agent_name=agent_name,
            )

        # Log phase completion if UI enabled
        if self.ui_logger:
            if result.status == PhaseStatus.COMPLETED:
                self.ui_logger.info(f"Phase {phase_number} completed successfully")
            elif result.status == PhaseStatus.FAILED:
                self.ui_logger.error(f"Phase {phase_number} failed")
            else:
                self.ui_logger.warning(f"Phase {phase_number} skipped")

        return result

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
        output_dir = config.output_dir / session.session_id
        output_dir.mkdir(parents=True, exist_ok=True)
        exporter = FileExporter(output_dir)

        # Initialize context optimization tracking
        if self.enable_summarization and self.context_summary:
            logger.info("Context optimization enabled for pipeline execution")
            session.artifacts = {"context_summaries": {}}

        # Start UI progress if enabled
        if self.ui_progress:
            self.ui_progress.start(total_phases=TOTAL_PHASES)

        # Log pipeline start if UI enabled
        if self.ui_logger:
            self.ui_logger.info(f"Starting pipeline for topic: {config.topic}")

        try:
            for phase_num in range(1, TOTAL_PHASES + 1):
                result = await self.execute_phase(session, phase_num)
                session.add_result(result)
                self._save_phase_result(exporter, result)

                if result.status in {PhaseStatus.COMPLETED, PhaseStatus.SKIPPED}:
                    session.state = PipelineState(f"phase_{phase_num}")
                elif result.status == PhaseStatus.FAILED:
                    session.state = PipelineState.FAILED
                    if self.ui_logger:
                        self.ui_logger.error("Pipeline failed, stopping execution")
                    break

            self._finalize_session_state(session)

            # Save context summaries to artifacts
            if self.enable_summarization and self.context_summary:
                all_summaries = self.context_summary.get_all_summaries()
                if all_summaries and hasattr(session, "artifacts"):
                    session.artifacts["context_summaries"] = {
                        str(phase): summary.get_summary_dict()
                        for phase, summary in all_summaries.items()
                    }
                    logger.info(f"Saved {len(all_summaries)} context summaries to session artifacts")

            # Stop UI progress and show summary if enabled
            if self.ui_progress:
                self.ui_progress.stop()
                self.ui_progress.show_session_summary(session)

            if self.ui_summary:
                self.ui_summary.show_session_phases(session)

            # Log pipeline completion if UI enabled
            if self.ui_logger:
                if session.state == PipelineState.COMPLETED:
                    self.ui_logger.info("Pipeline completed successfully!")
                else:
                    self.ui_logger.warning(f"Pipeline ended with state: {session.state.value}")

        finally:
            self._save_pipeline_state(exporter, session)

        return session
