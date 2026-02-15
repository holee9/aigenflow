"""
Custom exceptions for AigenFlow pipeline.
"""

from enum import Enum


class AigenFlowException(Exception):
    """Base exception for all aigenflow errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class PipelineException(AigenFlowException):
    """Exceptions related to pipeline execution and state management."""
    pass


class GatewayException(AigenFlowException):
    """Exceptions related to AI gateway and provider connections."""
    pass


class AgentException(AigenFlowException):
    """Exceptions related to AI agent interactions."""
    pass


class TemplateException(AigenFlowException):
    """Exceptions related to template rendering and management."""
    pass


class ConfigurationException(AigenFlowException):
    """Exceptions related to configuration and settings."""
    pass


class ErrorCode(str, Enum):
    """Standardized error codes for tracking and debugging."""

    PIPELINE_INVALID_STATE = "P1001"
    PIPELINE_PHASE_FAILED = "P1002"
    PIPELINE_RESUME_FAILED = "P1003"
    PIPELINE_SAVE_FAILED = "P1004"

    GATEWAY_CONNECTION_FAILED = "G2001"
    GATEWAY_SESSION_EXPIRED = "G2002"
    GATEWAY_LOGIN_FAILED = "G2003"
    GATEWAY_RESPONSE_DETECTION_FAILED = "G2004"
    GATEWAY_RATE_LIMITED = "G2005"

    AGENT_CALL_FAILED = "A3001"
    AGENT_NO_RESPONSE = "A3002"
    AGENT_INVALID_RESPONSE = "A3003"
    AGENT_RATE_LIMITED = "A3004"

    TEMPLATE_NOT_FOUND = "T4001"
    TEMPLATE_RENDER_FAILED = "T4002"
    TEMPLATE_INVALID = "T4003"

    CONFIG_INVALID = "C5001"
    CONFIG_MISSING = "C5002"
    CONFIG_VALIDATION_FAILED = "C5003"
