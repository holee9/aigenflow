"""
BasePhase abstract class for pipeline phases.

Defines the interface that all pipeline phases must implement.
"""

from abc import ABC, abstractmethod
from typing import Any

from core.models import PhaseResult, PipelineConfig, PipelineSession


class BasePhase(ABC):
    """
    Abstract base class for all pipeline phases.

    Each phase (Framing, Research, Strategy, Writing, Review) inherits from this
    and implements the abstract methods to define phase-specific behavior.
    """

    @abstractmethod
    def get_tasks(self, session: PipelineSession) -> list[Any]:
        """
        Get the list of tasks for this phase.

        Args:
            session: Current pipeline session

        Returns:
            List of tasks (PhaseTask enum values) to execute
        """
        pass

    @abstractmethod
    async def execute(self, session: PipelineSession, config: PipelineConfig) -> PhaseResult:
        """
        Execute the phase with given session and configuration.

        Args:
            session: Current pipeline session
            config: Pipeline configuration

        Returns:
            PhaseResult with execution results
        """
        pass

    @abstractmethod
    def validate_result(self, result: PhaseResult) -> bool:
        """
        Validate the phase execution result.

        Args:
            result: PhaseResult to validate

        Returns:
            True if result is valid, False otherwise
        """
        pass

    def get_phase_number(self) -> int:
        """
        Get the phase number for this phase.

        Returns:
            Phase number (1-5)
        """
        # Default implementation - can be overridden
        return 1
