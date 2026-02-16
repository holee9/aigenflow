"""
Pipeline state management modules.
"""

from enum import Enum


class PipelineState(str, Enum):
    """Overall pipeline state machine."""

    IDLE = "idle"
    PHASE_1 = "phase_1"
    PHASE_2 = "phase_2"
    PHASE_3 = "phase_3"
    PHASE_4 = "phase_4"
    PHASE_5 = "phase_5"
    COMPLETED = "completed"
    FAILED = "failed"
