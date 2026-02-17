"""
Tests for core event system.
"""

from datetime import datetime

from core.events import (
    AgentCalledEvent,
    BaseEvent,
    EventHandler,
    EventType,
    PhaseStartedEvent,
    PipelineStartedEvent,
    get_event_bus,
)


class TestEvents:
    """Tests for event models."""

    def test_pipeline_started_event(self):
        """Test PipelineStartedEvent creation."""
        event = PipelineStartedEvent(
            data={"config": {"topic": "Test", "doc_type": "bizplan"}}
        )

        assert event.event_type == EventType.PIPELINE_STARTED
        assert isinstance(event.timestamp, datetime)

    def test_phase_started_event(self):
        """Test PhaseStartedEvent creation."""
        event = PhaseStartedEvent(
            data={"phase_number": 1, "phase_name": "Ideation"}
        )

        assert event.event_type == EventType.PHASE_STARTED
        assert event.data["phase_number"] == 1

    def test_agent_called_event(self):
        """Test AgentCalledEvent creation."""
        event = AgentCalledEvent(
            data={"agent_name": "claude", "task_name": "brainstorm", "attempt": 1}
        )

        assert event.event_type == EventType.AGENT_CALLED
        assert event.data["agent_name"] == "claude"


class TestEventBus:
    """Tests for EventBus."""

    def test_get_event_bus_singleton(self):
        """Test that get_event_bus returns singleton instance."""
        bus1 = get_event_bus()
        bus2 = get_event_bus()

        assert bus1 is bus2

    def test_subscribe_and_publish(self):
        """Test subscribing handler and publishing events."""
        bus = get_event_bus()

        # Track handled events
        handled_events = []

        class TestHandler(EventHandler):
            """Test event handler."""

            def handle(self, event: BaseEvent) -> None:
                handled_events.append(event)

        handler = TestHandler()
        bus.subscribe(handler)

        event = PipelineStartedEvent()
        bus.publish(event)

        assert len(handled_events) == 1
        assert handled_events[0] == event

    def test_handler_error_doesnt_fail_bus(self):
        """Test that handler errors don't stop event bus."""
        bus = get_event_bus()

        class FailingHandler(EventHandler):
            """Handler that always raises exception."""

            def handle(self, event: BaseEvent) -> None:
                raise RuntimeError("Handler error")

        class TrackingHandler(EventHandler):
            """Handler that tracks events."""

            def __init__(self):
                self.events = []

            def handle(self, event: BaseEvent) -> None:
                self.events.append(event)

        failing = FailingHandler()
        tracking = TrackingHandler()

        bus.subscribe(failing)
        bus.subscribe(tracking)

        event = PipelineStartedEvent()
        bus.publish(event)

        # Failing handler should raise exception silently
        # Tracking handler should still receive event
        assert len(tracking.events) == 1
