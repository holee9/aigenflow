"""
Core data models for agent-compare pipeline.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class AgentType(str, Enum):
    CHATGPT = "chatgpt"
    CLAUDE = "claude"
    GEMINI = "gemini"
    PERPLEXITY = "perplexity"


class DocumentType(str, Enum):
    BIZPLAN = "bizplan"
    RD = "rd"


class TemplateType(str, Enum):
    DEFAULT = "default"
    STARTUP = "startup"
    STRATEGY = "strategy"
    RD = "rd"


class PhaseStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PipelineState(str, Enum):
    IDLE = "idle"
    PHASE_1 = "phase_1"
    PHASE_2 = "phase_2"
    PHASE_3 = "phase_3"
    PHASE_4 = "phase_4"
    PHASE_5 = "phase_5"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentResponse(BaseModel):
    agent_name: AgentType
    task_name: str
    content: str
    tokens_used: int = 0
    response_time: float = 0.0
    success: bool = True
    error: str | None = None
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class PhaseResult(BaseModel):
    phase_number: int
    phase_name: str
    status: PhaseStatus
    ai_responses: list[AgentResponse] = Field(default_factory=list)
    summary: str = ""
    artifacts: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class PipelineConfig(BaseModel):
    topic: str
    doc_type: DocumentType = DocumentType.BIZPLAN
    template: TemplateType = TemplateType.DEFAULT
    language: str = "ko"
    output_dir: Path = Field(default_factory=lambda: Path("output"))
    from_phase: int | None = None
    max_retries: int = 2
    timeout_seconds: int = 120

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, v: str) -> str:
        """Validate topic is not empty and meets minimum length."""
        if not v or not v.strip():
            raise ValueError("topic cannot be empty")
        stripped = v.strip()
        if len(stripped) < 10:
            raise ValueError("topic must be at least 10 characters")
        return stripped


class PipelineSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    config: PipelineConfig
    state: PipelineState = PipelineState.IDLE
    results: list[PhaseResult] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    current_phase: int = 0

    def add_result(self, result: PhaseResult) -> None:
        self.results.append(result)
        self.current_phase = result.phase_number
        self.updated_at = datetime.now()

    def get_phase_result(self, phase_number: int) -> PhaseResult | None:
        for result in self.results:
            if result.phase_number == phase_number:
                return result
        return None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


def create_phase_result(phase_number: int, phase_name: str) -> PhaseResult:
    return PhaseResult(
        phase_number=phase_number,
        phase_name=phase_name,
        status=PhaseStatus.PENDING,
    )
