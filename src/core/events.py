"""
Event system for pipeline execution tracking.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from core.logger import get_logger, redact_secrets

logger = get_logger(__name__)


class EventType(str, Enum):
    PIPELINE_STARTED = "pipeline_started"
    PIPELINE_COMPLETED = "pipeline_completed"
    PIPELINE_FAILED = "pipeline_failed"
    PIPELINE_RESUMED = "pipeline_resumed"

    PHASE_STARTED = "phase_started"
    PHASE_COMPLETED = "phase_completed"
    PHASE_FAILED = "phase_failed"
    PHASE_RETRIED = "phase_retried"

    AGENT_CALLED = "agent_called"
    AGENT_RESPONDED = "agent_responded"
    AGENT_FAILED = "agent_failed"
    AGENT_RETRIED = "agent_retried"

    GATEWAY_CONNECTED = "gateway_connected"
    GATEWAY_DISCONNECTED = "gateway_disconnected"
    GATEWAY_ERROR = "gateway_error"

    STATE_SAVED = "state_saved"
    STATE_LOADED = "state_loaded"
    ERROR = "error"


class BaseEvent(BaseModel):
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.now)
    data: dict[str, Any] = Field(default_factory=dict)
    session_id: str | None = None


class PipelineStartedEvent(BaseEvent):
    event_type: EventType = EventType.PIPELINE_STARTED
    data: dict[str, Any] = Field(default_factory=lambda: {"config": {"topic": "", "doc_type": "bizplan"}})


class PipelineCompletedEvent(BaseEvent):
    event_type: EventType = EventType.PIPELINE_COMPLETED
    data: dict[str, Any] = Field(default_factory=lambda: {"total_phases": 5, "duration_seconds": 0})


class PipelineFailedEvent(BaseEvent):
    event_type: EventType = EventType.PIPELINE_FAILED
    data: dict[str, Any] = Field(default_factory=lambda: {"error_message": "", "failed_phase": 0})


class PhaseStartedEvent(BaseEvent):
    event_type: EventType = EventType.PHASE_STARTED
    data: dict[str, Any] = Field(default_factory=lambda: {"phase_number": 1, "phase_name": ""})


class PhaseCompletedEvent(BaseEvent):
    event_type: EventType = EventType.PHASE_COMPLETED
    data: dict[str, Any] = Field(default_factory=lambda: {"phase_number": 1, "phase_name": "", "duration_seconds": 0})


class AgentCalledEvent(BaseEvent):
    event_type: EventType = EventType.AGENT_CALLED
    data: dict[str, Any] = Field(default_factory=lambda: {"agent_name": "", "task_name": "", "attempt": 1})


class AgentRespondedEvent(BaseEvent):
    event_type: EventType = EventType.AGENT_RESPONDED
    data: dict[str, Any] = Field(default_factory=lambda: {"agent_name": "", "task_name": "", "tokens_used": 0, "response_time": 0.0})


class StateSavedEvent(BaseEvent):
    event_type: EventType = EventType.STATE_SAVED
    data: dict[str, Any] = Field(default_factory=lambda: {"file_path": ""})


class EventHandler:
    def handle(self, event: BaseEvent) -> None:
        raise NotImplementedError


class EventBus:
    def __init__(self) -> None:
        self._handlers: list[EventHandler] = []

    def subscribe(self, handler: EventHandler) -> None:
        self._handlers.append(handler)

    def publish(self, event: BaseEvent) -> None:
        for handler in self._handlers:
            try:
                handler.handle(event)
            except Exception as exc:
                logger.warning(
                    "event_handler_failed",
                    handler=handler.__class__.__name__,
                    event_type=event.event_type.value,
                    error_type=type(exc).__name__,
                    error=redact_secrets(str(exc), key_hint="error"),
                )


_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


__all__ = [
    "EventType",
    "BaseEvent",
    "EventHandler",
    "EventBus",
    "PipelineStartedEvent",
    "PipelineCompletedEvent",
    "PipelineFailedEvent",
    "PhaseStartedEvent",
    "PhaseCompletedEvent",
    "AgentCalledEvent",
    "AgentRespondedEvent",
    "StateSavedEvent",
    "get_event_bus",
]
