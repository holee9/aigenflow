"""
Logging profiles for different environments.

Provides environment-specific logging configurations with structlog,
supporting development, testing, and production profiles with file rotation.
"""

import logging
import sys
from enum import StrEnum
from pathlib import Path
from typing import Any

import structlog
from structlog.types import Processor


class LogEnvironment(StrEnum):
    """Logging environment types."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class LoggingProfile:
    """
    Logging profile configuration.

    Encapsulates all settings for a logging environment including
    log level, output destinations, and file handling.
    """

    def __init__(
        self,
        log_level: int,
        console_enabled: bool,
        file_enabled: bool,
        json_output: bool,
        log_file: Path,
        max_file_size_mb: int = 10,
        backup_count: int = 5,
    ) -> None:
        """
        Initialize logging profile.

        Args:
            log_level: Logging level constant (e.g., logging.DEBUG)
            console_enabled: Whether to enable console logging
            file_enabled: Whether to enable file logging
            json_output: Whether to use JSON format for logs
            log_file: Path to log file
            max_file_size_mb: Maximum size of log file before rotation (MB)
            backup_count: Number of backup files to keep
        """
        self._log_level = log_level
        self._console_enabled = console_enabled
        self._file_enabled = file_enabled
        self._json_output = json_output
        self._log_file = log_file
        self._max_file_size_mb = max_file_size_mb
        self._backup_count = backup_count

    @property
    def log_level(self) -> int:
        """Get log level."""
        return self._log_level

    @property
    def log_file_path(self) -> Path:
        """Get log file path."""
        return self._log_file

    @property
    def use_json(self) -> bool:
        """Get JSON output setting."""
        return self._json_output

    @property
    def max_file_size_mb(self) -> int:
        """Get maximum file size before rotation."""
        return self._max_file_size_mb

    @property
    def backup_count(self) -> int:
        """Get number of backup files to keep."""
        return self._backup_count

    def should_log_to_console(self) -> bool:
        """Check if console logging is enabled."""
        return self._console_enabled

    def should_log_to_file(self) -> bool:
        """Check if file logging is enabled."""
        return self._file_enabled


# Log level mapping
LOG_LEVEL_MAP: dict[str, int] = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


def parse_log_level(level_str: str) -> int:
    """
    Parse log level string to logging constant.

    Args:
        level_str: Log level string (debug, info, warning, error)

    Returns:
        Logging level constant (e.g., logging.DEBUG)

    Raises:
        ValueError: If log level string is invalid
    """
    normalized = level_str.lower().strip()
    if normalized not in LOG_LEVEL_MAP:
        valid_levels = ", ".join(LOG_LEVEL_MAP.keys())
        raise ValueError(
            f"Invalid log level: '{level_str}'. Valid levels: {valid_levels}"
        )
    return LOG_LEVEL_MAP[normalized]


def _redact_secrets(_: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """Redact sensitive information from logs."""
    sensitive_keywords = (
        "key", "token", "secret", "password", "passwd",
        "cookie", "auth", "authorization", "session",
    )

    def redact_value(value: Any, key_hint: str | None = None) -> Any:
        if isinstance(value, dict):
            return {k: redact_value(v, k) for k, v in value.items()}
        if isinstance(value, list):
            return [redact_value(item, key_hint) for item in value]
        if isinstance(value, tuple):
            return tuple(redact_value(item, key_hint) for item in value)
        if isinstance(value, str) and key_hint:
            if any(keyword in key_hint.lower() for keyword in sensitive_keywords):
                if len(value) <= 8:
                    return "***"
                return f"{value[:4]}...{value[-4:]}"
        return value

    return {k: redact_value(v, k) for k, v in event_dict.items()}


def _add_file_handler(
    logger: Any,
    log_file: Path,
    level: int,
    json_output: bool = False,
) -> None:
    """
    Add file handler with rotation to logger.

    Args:
        logger: Structlog logger instance
        log_file: Path to log file
        level: Logging level
        json_output: Whether to output JSON logs
    """
    import logging.handlers

    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Create rotating file handler (max 10MB, keep 5 files)
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(level)

    # Set formatter
    if json_output:
        formatter = logging.Formatter("%(message)s")
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    file_handler.setFormatter(formatter)

    # Add handler to underlying stdlib logger
    stdlib_logger = logging.getLogger(logger.name)
    stdlib_logger.addHandler(file_handler)
    stdlib_logger.setLevel(level)


def get_logging_profile(
    environment: LogEnvironment = LogEnvironment.PRODUCTION,
    log_dir: Path | None = None,
) -> LoggingProfile:
    """
    Get logging configuration profile for the specified environment.

    Args:
        environment: Log environment (development, testing, production)
        log_dir: Directory for log files (defaults to ./logs)

    Returns:
        LoggingProfile object containing logging configuration
    """
    if log_dir is None:
        log_dir = Path("logs")

    profiles = {
        LogEnvironment.DEVELOPMENT: LoggingProfile(
            log_level=logging.DEBUG,
            console_enabled=True,
            file_enabled=True,
            json_output=False,
            log_file=log_dir / "development.log",
        ),
        LogEnvironment.TESTING: LoggingProfile(
            log_level=logging.INFO,
            console_enabled=False,
            file_enabled=True,
            json_output=False,
            log_file=log_dir / "testing.log",
        ),
        LogEnvironment.PRODUCTION: LoggingProfile(
            log_level=logging.WARNING,
            console_enabled=False,
            file_enabled=True,
            json_output=True,
            log_file=log_dir / "production.log",
        ),
    }

    return profiles.get(environment, profiles[LogEnvironment.PRODUCTION])


def configure_logging(
    environment: LogEnvironment = LogEnvironment.PRODUCTION,
    log_level: str | int | None = None,
    log_dir: Path | None = None,
    json_output: bool | None = None,
) -> structlog.stdlib.BoundLogger:
    """
    Configure logging for the specified environment.

    Args:
        environment: Log environment (development, testing, production)
        log_level: Override log level (string or int)
        log_dir: Directory for log files
        json_output: Override JSON output setting

    Returns:
        Configured structlog logger instance
    """
    profile = get_logging_profile(environment, log_dir)

    # Allow override of log level
    if log_level is not None:
        if isinstance(log_level, str):
            level = parse_log_level(log_level)
        else:
            level = log_level
    else:
        level = profile.log_level

    # Determine JSON output
    use_json = json_output if json_output is not None else profile.use_json

    # Build processors
    processors: list[Processor] = [
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        _redact_secrets,
    ]

    # Add output processor
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
        wrapper_class=structlog.stdlib.BoundLogger,
    )

    # Get logger
    logger = structlog.get_logger("aigenflow")

    # Reset any existing handlers
    stdlib_logger = logging.getLogger("aigenflow")
    stdlib_logger.handlers.clear()
    stdlib_logger.propagate = False
    stdlib_logger.setLevel(level)

    # Add console handler if enabled
    if profile.should_log_to_console():
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        stdlib_logger.addHandler(console_handler)

    # Add file handler if enabled
    if profile.should_log_to_file():
        _add_file_handler(
            logger,
            profile.log_file_path,
            level,
            use_json,
        )

    return logger
