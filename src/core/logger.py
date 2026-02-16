"""
Logging configuration for AigenFlow pipeline.

Provides profile-based logging with environment-specific configurations,
file rotation support, and dynamic log level changes.
"""

import logging
import logging.handlers
import re
import sys
from pathlib import Path
from typing import Any

import structlog

from config.logging_profiles import (
    LoggingProfile,
    get_logging_profile,
)

_SENSITIVE_KEYWORDS = (
    "key",
    "token",
    "secret",
    "password",
    "passwd",
    "cookie",
    "auth",
    "authorization",
    "session",
)
_LONG_SECRET_PATTERN = re.compile(r"[A-Za-z0-9_\-]{20,}")


def _is_sensitive_key(key: str) -> bool:
    """Check if a key might contain sensitive data."""
    lowered = key.lower()
    return any(keyword in lowered for keyword in _SENSITIVE_KEYWORDS)


def _mask_string(value: str) -> str:
    """Mask a potentially sensitive string."""
    stripped = value.strip()
    if not stripped:
        return value
    if len(stripped) <= 8:
        return "***"
    return f"{stripped[:4]}...{stripped[-4:]}"


def redact_secrets(value: Any, key_hint: str | None = None) -> Any:
    """
    Recursively redact sensitive values in logs.

    Args:
        value: Value to redact (dict, list, tuple, str, or other)
        key_hint: Optional key name to check for sensitivity

    Returns:
        Redacted value with sensitive data masked
    """
    if isinstance(value, dict):
        return {k: redact_secrets(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_secrets(item, key_hint) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_secrets(item, key_hint) for item in value)
    if isinstance(value, str):
        if key_hint and _is_sensitive_key(key_hint):
            return _mask_string(value)
        if _LONG_SECRET_PATTERN.fullmatch(value.strip()):
            return _mask_string(value)
        return value
    return value


def redact_event_dict(_: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """Structlog processor to redact sensitive information."""
    return redact_secrets(event_dict)


def _get_log_level_int(level: str | int) -> int:
    """Convert string or int log level to logging module constant."""
    if isinstance(level, int):
        return level
    if isinstance(level, str):
        return getattr(logging, level.upper())
    return logging.INFO


def setup_logging(
    level: int | str | None = None,
    log_file: Path | None = None,
    json_logs: bool = False,
    profile: LoggingProfile | None = None,
) -> structlog.stdlib.BoundLogger:
    """
    Configure structured logging with optional file rotation.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            If None, uses level from profile or defaults to INFO.
        log_file: Path to log file. If None, uses path from profile or defaults.
        json_logs: Whether to use JSON format. If None, uses profile setting.
        profile: LoggingProfile with complete configuration. If provided,
            other parameters are ignored.

    Returns:
        Configured structlog bound logger

    Examples:
        >>> # Basic setup with defaults
        >>> logger = setup_logging()

        >>> # With custom log level
        >>> logger = setup_logging(level="DEBUG")

        >>> # With file logging
        >>> logger = setup_logging(log_file=Path("app.log"))

        >>> # With profile
        >>> from config.logging_profiles import LogEnvironment
        >>> profile = get_logging_profile(LogEnvironment.DEVELOPMENT)
        >>> logger = setup_logging(profile=profile)
    """
    # Use profile if provided, otherwise create custom profile
    if profile is None:
        profile = get_logging_profile()
        # Override profile settings with explicit parameters
        if level is not None:
            level_int = _get_log_level_int(level)
        else:
            level_int = _get_log_level_int(profile.log_level.value)

        if log_file is None:
            log_file = profile.log_file_path

        use_json = json_logs if json_logs is not None else profile.use_json
    else:
        level_int = _get_log_level_int(profile.log_level.value)
        log_file = profile.log_file_path
        use_json = profile.use_json

    # Base processors for all log entries
    processors = [
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        redact_event_dict,
    ]

    # JSON or console renderer
    if use_json:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Get the underlying stdlib logger
    logger = structlog.get_logger()
    stdlib_logger = logging.getLogger("aigenflow")
    stdlib_logger.setLevel(level_int)

    # Clear existing handlers
    stdlib_logger.handlers.clear()

    # Add console handler if enabled
    if profile.should_log_to_console():
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level_int)
        stdlib_logger.addHandler(console_handler)

    # Add file handler with rotation if enabled
    if profile.should_log_to_file():
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Rotating file handler with size-based rotation
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=profile.max_file_size_mb * 1024 * 1024,  # Convert MB to bytes
            backupCount=profile.backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(level_int)
        stdlib_logger.addHandler(file_handler)

    return logger.bind()


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (defaults to "aigenflow")

    Returns:
        Structlog bound logger

    Examples:
        >>> logger = get_logger()
        >>> logger.info("Application started")

        >>> logger = get_logger("my.module")
        >>> logger.debug("Debugging info", extra_key="value")
    """
    logger_name = name or "aigenflow"
    return structlog.get_logger(logger_name)


class LogContext:
    """
    Context manager for binding structured log context.

    Examples:
        >>> with LogContext(user_id="123", request_id="abc"):
        ...     logger.info("Processing request")
        ...     # Log entries will include user_id and request_id

        >>> logger = LogContext(transaction_id="xyz").__enter__()
        >>> logger.info("Started")
        >>> # Remember to call __exit__() or use as context manager
    """

    def __init__(self, **context: Any) -> None:
        self._context = context
        self._logger = structlog.get_logger()

    def __enter__(self) -> structlog.stdlib.BoundLogger:
        """Bind context and return logger."""
        return self._logger.bind(**self._context)

    def __exit__(self, *args: Any) -> None:
        """Exit context (no-op for structlog)."""
        pass


def set_log_level(level: str | int) -> None:
    """
    Dynamically change the log level at runtime.

    Args:
        level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Examples:
        >>> # Enable debug logging
        >>> set_log_level("DEBUG")

        >>> # Reduce verbosity
        >>> set_log_level("WARNING")
    """
    level_int = _get_log_level_int(level)
    logger = logging.getLogger("aigenflow")
    logger.setLevel(level_int)

    # Update all handlers
    for handler in logger.handlers:
        handler.setLevel(level_int)


def get_current_log_level() -> str:
    """
    Get the current log level as a string.

    Returns:
        Current log level name (e.g., "INFO", "DEBUG")

    Examples:
        >>> get_current_log_level()
        'INFO'
    """
    logger = logging.getLogger("aigenflow")
    return logging.getLevelName(logger.level)
