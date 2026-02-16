"""
Agent router for mapping (phase, task) to AI agent.

Implements the routing table defined in SPEC-PIPELINE-001.
"""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel

from agents.base import AgentRequest, AgentResponse, AsyncAgent
from core.exceptions import AgentException
from core.models import AgentType, DocumentType


class PhaseTask(StrEnum):
    """Task types for each phase."""

    # Phase 1: Ideation
    BRAINSTORM_CHATGPT = "brainstorm_chatgpt"
    VALIDATE_CLAUDE = "validate_claude"

    # Phase 2: Deep Research
    DEEP_SEARCH_GEMINI = "deep_search_gemini"
    FACT_CHECK_PERPLEXITY = "fact_check_perplexity"

    # Phase 3: Strategy
    SWOT_CHATGPT = "swot_chatgpt"
    NARRATIVE_CLAUDE = "narrative_claude"

    # Phase 4: Writing
    BUSINESS_PLAN_CLAUDE = "business_plan_claude"
    OUTLINE_CHATGPT = "outline_chatgpt"
    CHARTS_GEMINI = "charts_gemini"

    # Phase 5: Review
    VERIFY_PERPLEXITY = "verify_perplexity"
    FINAL_REVIEW_CLAUDE = "final_review_claude"
    POLISH_CLAUDE = "polish_claude"


class AgentMapping(BaseModel):
    """Mapping of (phase, task, doc_type) to agent."""

    phase: int
    task: PhaseTask
    doc_type: DocumentType
    agent: AgentType
    fallback: AgentType | None = None

    @classmethod
    def get_default_mapping(cls) -> dict[tuple[int, PhaseTask, DocumentType], AgentType]:
        """Get default agent mapping from SPEC."""
        return {
            # Phase 1: Ideation (sequential)
            (1, PhaseTask.BRAINSTORM_CHATGPT, DocumentType.BIZPLAN): AgentType.CHATGPT,
            (1, PhaseTask.VALIDATE_CLAUDE, DocumentType.BIZPLAN): AgentType.CLAUDE,
            # Phase 2: Research (parallel)
            (2, PhaseTask.DEEP_SEARCH_GEMINI, DocumentType.BIZPLAN): AgentType.GEMINI,
            (2, PhaseTask.FACT_CHECK_PERPLEXITY, DocumentType.BIZPLAN): AgentType.PERPLEXITY,
            # Phase 3: Strategy (sequential)
            (3, PhaseTask.SWOT_CHATGPT, DocumentType.BIZPLAN): AgentType.CHATGPT,
            (3, PhaseTask.NARRATIVE_CLAUDE, DocumentType.BIZPLAN): AgentType.CLAUDE,
            # Phase 4: Writing (sequential + Claude main)
            (4, PhaseTask.BUSINESS_PLAN_CLAUDE, DocumentType.BIZPLAN): AgentType.CLAUDE,
            (4, PhaseTask.OUTLINE_CHATGPT, DocumentType.BIZPLAN): AgentType.CHATGPT,
            (4, PhaseTask.CHARTS_GEMINI, DocumentType.BIZPLAN): AgentType.GEMINI,
            # Phase 5: Review (parallel)
            (5, PhaseTask.VERIFY_PERPLEXITY, DocumentType.BIZPLAN): AgentType.PERPLEXITY,
            (5, PhaseTask.FINAL_REVIEW_CLAUDE, DocumentType.BIZPLAN): AgentType.CLAUDE,
            (5, PhaseTask.POLISH_CLAUDE, DocumentType.BIZPLAN): AgentType.CLAUDE,
        }


class AgentRouter:
    """
    Routes (phase, task) requests to appropriate AI agent.
    """

    def __init__(self, settings: Any) -> None:
        """Initialize router with settings."""
        self.settings = settings
        self.mapping = AgentMapping.get_default_mapping()
        self.agents: dict[AgentType, AsyncAgent] = {}

    def register_agent(self, agent_type: AgentType, agent: AsyncAgent) -> None:
        """Register an agent instance."""
        self.agents[agent_type] = agent

    def get_agent(self, mapping: AgentMapping) -> AsyncAgent:
        """Get agent instance for mapping."""
        agent_type = mapping.agent

        if agent_type in self.agents:
            return self.agents[agent_type]

        if mapping.fallback:
            return self.agents[mapping.fallback]

        raise AgentException(
            message=f"No agent registered for {mapping.agent}",
            details={"mapping": mapping.model_dump()},
        )

    async def execute(self, phase: int, task: PhaseTask, prompt: str, doc_type: DocumentType) -> AgentResponse:
        """
        Execute task with appropriate agent.

        Args:
            phase: Phase number
            task: Task to execute
            prompt: Prompt text
            doc_type: Document type

        Returns:
            AgentResponse
        """
        agent_type = self.mapping.get((phase, task, doc_type))
        if agent_type is None:
            raise AgentException(
                message=f"No mapping found for phase={phase}, task={task.value}, doc_type={doc_type.value}",
                details={"phase": phase, "task": task.value, "doc_type": doc_type.value},
            )

        mapping = AgentMapping(
            phase=phase,
            task=task,
            doc_type=doc_type,
            agent=agent_type,
        )

        # Get agent
        agent = self.get_agent(mapping)

        # Create request
        timeout_seconds = 120
        if self.settings is not None and hasattr(self.settings, "timeout_seconds"):
            timeout_seconds = self.settings.timeout_seconds

        request = AgentRequest(
            task_name=task.value,
            prompt=prompt,
            timeout=timeout_seconds,
        )

        # Execute
        return await agent.execute(request)
