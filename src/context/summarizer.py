"""
Context summarizer for reducing token usage while preserving critical information.

Uses AI agents to summarize accumulated context from previous phases,
preserving key decisions, data points, and citation sources.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from src.agents.base import AgentRequest, AgentResponse
from src.agents.router import AgentRouter, PhaseTask
from src.core.logger import get_logger
from src.core.models import AgentType, DocumentType, PhaseResult

logger = get_logger(__name__)


@dataclass
class SummaryResult:
    """
    Result of context summarization operation.

    Attributes:
        original_text: Original full context text
        summarized_text: AI-generated summary
        tokens_original: Token count of original text
        tokens_summary: Token count after summarization
        reduction_ratio: Ratio of tokens saved (0.0-1.0)
        timestamp: When summarization occurred
        success: Whether summarization succeeded
        error: Error message if failed
    """

    original_text: str
    summarized_text: str
    tokens_original: int
    tokens_summary: int
    reduction_ratio: float
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    error: str | None = None

    def get_summary_dict(self) -> dict[str, Any]:
        """Convert summary result to dictionary for serialization."""
        return {
            "original_length": len(self.original_text),
            "summary_length": len(self.summarized_text),
            "tokens_original": self.tokens_original,
            "tokens_summary": self.tokens_summary,
            "reduction_ratio": self.reduction_ratio,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "error": self.error,
        }


class SummaryConfig(BaseModel):
    """
    Configuration for context summarization.

    Attributes:
        enabled: Whether summarization is enabled
        target_reduction_ratio: Target token reduction ratio (default 0.5 = 50%)
        agent_type: Which AI agent to use for summarization
        max_retries: Number of retry attempts on failure
        preserve_sections: List of section names to preserve verbatim
    """

    enabled: bool = True
    target_reduction_ratio: float = 0.5
    agent_type: AgentType = AgentType.CLAUDE
    max_retries: int = 2
    preserve_sections: list[str] = field(
        default_factory=lambda: ["key_decisions", "data_points", "citations"]
    )


class ContextSummary:
    """
    AI-powered context summarization for token optimization.

    Summarizes accumulated context while preserving critical information:
    - Key decisions made in previous phases
    - Important data points and metrics
    - Citation sources and references
    - Action items and next steps

    On failure, returns original context to ensure pipeline continuity.
    """

    # Default summary prompt template
    DEFAULT_SUMMARY_PROMPT = """Please summarize the following context from previous pipeline phases while preserving:

1. Key decisions and their rationales
2. Important data points and metrics
3. Citation sources and references
4. Action items and next steps

Target: Reduce to approximately {target_ratio:.0%} of original token count while maintaining critical information.

Context to summarize:
-----------
{context}
-----------

Provide a concise summary that captures the essential information."""

    def __init__(
        self,
        agent_router: AgentRouter,
        config: SummaryConfig | None = None,
    ) -> None:
        """
        Initialize context summarizer.

        Args:
            agent_router: AgentRouter for accessing AI agents
            config: Optional summary configuration
        """
        self.agent_router = agent_router
        self.config = config or SummaryConfig()
        self._summaries: dict[int, SummaryResult] = {}

    def _build_summary_prompt(
        self,
        context: str,
        phase_number: int,
    ) -> str:
        """
        Build summary prompt with phase-specific context.

        Args:
            context: Context text to summarize
            phase_number: Current phase number

        Returns:
            Formatted prompt string
        """
        target_ratio = self.config.target_reduction_ratio
        return self.DEFAULT_SUMMARY_PROMPT.format(
            target_ratio=target_ratio,
            context=context,
        )

    def _extract_context_from_results(self, results: list[PhaseResult]) -> str:
        """
        Extract and format context from phase results.

        Args:
            results: List of PhaseResult objects

        Returns:
            Formatted context string
        """
        sections = []

        for result in results:
            if result.status.value not in ["completed", "skipped"]:
                continue

            # Add phase summary
            sections.append(f"## Phase {result.phase_number}: {result.phase_name}")
            sections.append(f"Status: {result.status.value}")

            # Add AI response summaries
            if result.ai_responses:
                for idx, response in enumerate(result.ai_responses):
                    sections.append(
                        f"\nTask {idx + 1} ({response.agent_name.value}): {response.task_name}"
                    )
                    # Include key content (limit to prevent double summarization)
                    content_preview = response.content[:500]
                    if len(response.content) > 500:
                        content_preview += "\n...(truncated for summary input)"
                    sections.append(content_preview)

            # Add phase summary if available
            if result.summary:
                sections.append(f"\nPhase Summary:\n{result.summary}")

            sections.append("\n" + "-" * 50 + "\n")

        return "\n".join(sections)

    async def _summarize_with_agent(
        self,
        context: str,
        phase_number: int,
    ) -> tuple[str, int, int]:
        """
        Perform summarization using AI agent.

        Args:
            context: Context to summarize
            phase_number: Current phase number

        Returns:
            Tuple of (summary_text, original_tokens, summary_tokens)

        Raises:
            Exception: If summarization fails after retries
        """
        from src.context.tokenizer import TokenCounter

        # Count original tokens
        token_counter = TokenCounter()
        original_result = token_counter.count(context, model_name="claude")
        original_tokens = original_result.total_tokens

        # Build summary prompt
        prompt = self._build_summary_prompt(context, phase_number)

        # Use summary-specific task
        # We'll use a generic summarization task
        summary_task = PhaseTask.NARRATIVE_CLAUDE  # Reuse existing task for summarization

        logger.info(
            f"Starting context summarization for Phase {phase_number}: "
            f"{original_tokens} tokens -> target {self.config.target_reduction_ratio:.0%} reduction"
        )

        # Execute with retry logic
        last_error = None
        for attempt in range(self.config.max_retries + 1):
            try:
                # Use the agent router to execute summarization
                response = await self.agent_router.execute(
                    phase=phase_number,
                    task=summary_task,
                    prompt=prompt,
                    doc_type=DocumentType.BIZPLAN,
                )

                if not response.success:
                    raise Exception(f"Agent execution failed: {response.error}")

                summary_text = response.content.strip()

                # Count summary tokens
                summary_result = token_counter.count(summary_text, model_name="claude")
                summary_tokens = summary_result.total_tokens

                logger.info(
                    f"Summarization completed: {original_tokens} -> {summary_tokens} tokens "
                    f"({summary_tokens / original_tokens:.1%} of original)"
                )

                return summary_text, original_tokens, summary_tokens

            except Exception as exc:
                last_error = exc
                logger.warning(
                    f"Summarization attempt {attempt + 1}/{self.config.max_retries + 1} failed: {exc}"
                )
                if attempt < self.config.max_retries:
                    await asyncio.sleep(1)  # Brief delay before retry
                continue

        # All retries exhausted
        raise Exception(f"Summarization failed after {self.config.max_retries + 1} attempts: {last_error}")

    async def summarize_phase_context(
        self,
        session_results: list[PhaseResult],
        current_phase: int,
    ) -> SummaryResult:
        """
        Summarize context from completed phases.

        Args:
            session_results: List of phase results from current session
            current_phase: Current phase number (phases before this will be summarized)

        Returns:
            SummaryResult with summarization outcome
        """
        if not self.config.enabled:
            logger.debug("Summarization is disabled, returning original context")
            return SummaryResult(
                original_text="",
                summarized_text="",
                tokens_original=0,
                tokens_summary=0,
                reduction_ratio=0.0,
                success=False,
                error="Summarization disabled",
            )

        try:
            # Filter results from phases before current phase
            previous_results = [r for r in session_results if r.phase_number < current_phase]

            if not previous_results:
                logger.debug(f"No previous phases to summarize before Phase {current_phase}")
                return SummaryResult(
                    original_text="",
                    summarized_text="",
                    tokens_original=0,
                    tokens_summary=0,
                    reduction_ratio=0.0,
                    success=True,
                )

            # Extract context from results
            context = self._extract_context_from_results(previous_results)

            if not context or len(context.strip()) < 100:
                logger.debug("Insufficient context to summarize")
                return SummaryResult(
                    original_text=context,
                    summarized_text=context,
                    tokens_original=len(context) // 4,  # Rough estimate
                    tokens_summary=len(context) // 4,
                    reduction_ratio=0.0,
                    success=True,
                )

            # Perform summarization
            summary_text, original_tokens, summary_tokens = await self._summarize_with_agent(
                context, current_phase
            )

            # Calculate reduction ratio
            reduction_ratio = 1.0 - (summary_tokens / original_tokens) if original_tokens > 0 else 0.0

            result = SummaryResult(
                original_text=context,
                summarized_text=summary_text,
                tokens_original=original_tokens,
                tokens_summary=summary_tokens,
                reduction_ratio=reduction_ratio,
                success=True,
            )

            # Store summary for later retrieval
            self._summaries[current_phase] = result

            return result

        except Exception as exc:
            # On failure, return result with error but don't fail the pipeline
            logger.error(f"Context summarization failed: {exc}")
            return SummaryResult(
                original_text=context if "context" in locals() else "",
                summarized_text=context if "context" in locals() else "",
                tokens_original=0,
                tokens_summary=0,
                reduction_ratio=0.0,
                success=False,
                error=str(exc),
            )

    def get_summary(self, phase: int) -> SummaryResult | None:
        """
        Retrieve previously generated summary for a phase.

        Args:
            phase: Phase number

        Returns:
            SummaryResult if available, None otherwise
        """
        return self._summaries.get(phase)

    def get_all_summaries(self) -> dict[int, SummaryResult]:
        """
        Get all generated summaries.

        Returns:
            Dictionary mapping phase numbers to SummaryResult objects
        """
        return self._summaries.copy()

    def clear_summaries(self) -> None:
        """Clear all stored summaries."""
        self._summaries.clear()

    def should_summarize_before_phase(
        self,
        session_results: list[PhaseResult],
        current_phase: int,
        provider: str = "claude",
        threshold: float = 0.8,
    ) -> bool:
        """
        Determine if summarization should be triggered before a phase.

        Args:
            session_results: List of phase results from current session
            current_phase: Current phase number
            provider: AI provider name for token limit
            threshold: Threshold percentage (default 0.8 = 80%)

        Returns:
            True if summarization is recommended
        """
        from src.context.tokenizer import TokenCounter

        # Filter results from phases before current phase
        previous_results = [r for r in session_results if r.phase_number < current_phase]

        if not previous_results:
            return False

        # Extract context and count tokens
        context = self._extract_context_from_results(previous_results)
        token_counter = TokenCounter()
        result = token_counter.count(context, model_name=provider)

        # Check if near limit
        return result.is_near_limit(provider, threshold)
