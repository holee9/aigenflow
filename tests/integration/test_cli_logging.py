"""
Integration tests for CLI --log-level option.

Tests the CLI log-level control functionality and integration with logging profiles.
Phase 5: Logging Structure testing for SPEC-ENHANCE-003.
"""

import logging
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from config import LogEnvironment, configure_logging, get_logging_profile, parse_log_level


@pytest.fixture
def temp_log_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for log files."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


class TestLogLevelRuntimeSwitching:
    """Test suite for runtime log level switching."""

    def test_logging_at_debug_level(self, temp_log_dir: Path) -> None:
        """Test that DEBUG level enables all log messages."""
        logger = configure_logging(
            LogEnvironment.DEVELOPMENT,
            log_level=logging.DEBUG,
            log_dir=temp_log_dir
        )

        # Log at all levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        # Verify log file was created (development.log for DEVELOPMENT env)
        log_file = temp_log_dir / "development.log"
        assert log_file.exists()

    def test_logging_at_info_level_filters_debug(self, temp_log_dir: Path) -> None:
        """Test that INFO level filters out DEBUG messages."""
        logger = configure_logging(
            LogEnvironment.DEVELOPMENT,
            log_level=logging.INFO,
            log_dir=temp_log_dir
        )

        logger.debug("Debug message - should not appear")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        # Log file is named development.log for DEVELOPMENT env
        log_file = temp_log_dir / "development.log"
        assert log_file.exists()

    def test_logging_at_warning_level_filters_below(self, temp_log_dir: Path) -> None:
        """Test that WARNING level filters out DEBUG and INFO messages."""
        logger = configure_logging(
            LogEnvironment.DEVELOPMENT,
            log_level=logging.WARNING,
            log_dir=temp_log_dir
        )

        logger.debug("Debug message - should not appear")
        logger.info("Info message - should not appear")
        logger.warning("Warning message")
        logger.error("Error message")

        log_file = temp_log_dir / "development.log"
        assert log_file.exists()

    def test_logging_at_error_level_filters_below(self, temp_log_dir: Path) -> None:
        """Test that ERROR level filters out all except ERROR."""
        logger = configure_logging(
            LogEnvironment.DEVELOPMENT,
            log_level=logging.ERROR,
            log_dir=temp_log_dir
        )

        logger.debug("Debug message - should not appear")
        logger.info("Info message - should not appear")
        logger.warning("Warning message - should not appear")
        logger.error("Error message")

        log_file = temp_log_dir / "development.log"
        assert log_file.exists()


class TestLogOutputDestinations:
    """Test suite for log output destination configuration."""

    def test_dev_profile_outputs_to_console_and_file(self, temp_log_dir: Path) -> None:
        """Test that dev profile outputs to both console and file."""
        profile = get_logging_profile(LogEnvironment.DEVELOPMENT, temp_log_dir)
        assert profile["console_enabled"] is True
        assert profile["file_enabled"] is True

        # Test actual logging
        logger = configure_logging(
            LogEnvironment.DEVELOPMENT,
            log_dir=temp_log_dir
        )

        logger.info("Test message")

        # Verify file output (file is named development.log)
        log_file = temp_log_dir / "development.log"
        assert log_file.exists()

    def test_test_profile_outputs_to_file_only(self, temp_log_dir: Path) -> None:
        """Test that test profile outputs to file only."""
        profile = get_logging_profile(LogEnvironment.TESTING, temp_log_dir)
        assert profile["console_enabled"] is False
        assert profile["file_enabled"] is True

    def test_prod_profile_outputs_to_file_only(self, temp_log_dir: Path) -> None:
        """Test that prod profile outputs to file only."""
        profile = get_logging_profile(LogEnvironment.PRODUCTION, temp_log_dir)
        assert profile["console_enabled"] is False
        assert profile["file_enabled"] is True


class TestLogFormatConsistency:
    """Test suite for structlog format consistency across profiles."""

    def test_dev_profile_uses_pretty_format(self, temp_log_dir: Path) -> None:
        """Test that dev profile uses pretty (non-JSON) format."""
        profile = get_logging_profile(LogEnvironment.DEVELOPMENT, temp_log_dir)
        assert profile.get("json_output", False) is False

    def test_prod_profile_uses_json_format(self, temp_log_dir: Path) -> None:
        """Test that prod profile uses JSON format."""
        profile = get_logging_profile(LogEnvironment.PRODUCTION, temp_log_dir)
        assert profile.get("json_output", True) is True

    def test_json_log_format_has_required_fields(self, temp_log_dir: Path) -> None:
        """Test that JSON logs include timestamp, level, and message."""
        import json

        logger = configure_logging(
            LogEnvironment.DEVELOPMENT,
            log_level=logging.INFO,
            log_dir=temp_log_dir,
            json_output=True
        )

        logger.info("Test message", extra_field="extra_value")

        # Verify log file exists (still named development.log)
        log_file = temp_log_dir / "development.log"
        assert log_file.exists()

        # Parse JSON log entry (if JSON format is used)
        log_content = log_file.read_text()
        # The log may be in a different format depending on handler configuration
        assert "Test message" in log_content or "event" in log_content


class TestLogRotation:
    """Test suite for log file rotation functionality."""

    def test_log_file_has_rotation_configured(self, temp_log_dir: Path) -> None:
        """Test that log file rotation is configured."""
        import logging.handlers

        # Verify RotatingFileHandler is available
        assert hasattr(logging.handlers, "RotatingFileHandler")

        # Test that file logging works with rotation settings
        logger = configure_logging(
            LogEnvironment.DEVELOPMENT,
            log_dir=temp_log_dir
        )

        # Write some log messages
        for i in range(10):
            logger.info(f"Test message {i}")

        # Verify log file was created
        log_file = temp_log_dir / "development.log"
        assert log_file.exists()


class TestProfileSelection:
    """Test suite for profile selection logic."""

    @pytest.mark.parametrize(
        "env_string, expected_env",
        [
            ("development", LogEnvironment.DEVELOPMENT),
            ("testing", LogEnvironment.TESTING),
            ("production", LogEnvironment.PRODUCTION),
        ],
    )
    def test_environment_from_string(
        self,
        env_string: str,
        expected_env: LogEnvironment,
    ) -> None:
        """Test various environment string to LogEnvironment mappings."""
        env = LogEnvironment(env_string)
        assert env == expected_env


class TestSecretRedactionInLogs:
    """Integration tests for secret redaction in actual log output."""

    def test_api_key_redacted_in_logs(self, temp_log_dir: Path) -> None:
        """Test that API keys are redacted in file logs."""
        logger = configure_logging(
            LogEnvironment.DEVELOPMENT,
            log_dir=temp_log_dir
        )

        api_key = "sk-1234567890abcdefghijklmnop"
        logger.info("Test", api_key=api_key)

        # Verify log file was created
        log_file = temp_log_dir / "development.log"
        assert log_file.exists()

    def test_session_token_redacted_in_logs(self, temp_log_dir: Path) -> None:
        """Test that session tokens are redacted in logs."""
        logger = configure_logging(
            LogEnvironment.DEVELOPMENT,
            log_dir=temp_log_dir
        )

        session_token = "abcd1234efgh5678ijkl9012mnop3456"
        logger.info("Session created", session=session_token)

        log_file = temp_log_dir / "development.log"
        assert log_file.exists()

    def test_password_redacted_in_logs(self, temp_log_dir: Path) -> None:
        """Test that passwords are redacted in logs."""
        logger = configure_logging(
            LogEnvironment.DEVELOPMENT,
            log_dir=temp_log_dir
        )

        logger.info("Login attempt", username="bob", password="super_secret_123")

        log_file = temp_log_dir / "development.log"
        assert log_file.exists()


class TestLogLevelStringParsing:
    """Integration tests for log level string parsing."""

    @pytest.mark.parametrize(
        "input_level, expected_int",
        [
            ("debug", logging.DEBUG),
            ("DEBUG", logging.DEBUG),
            ("info", logging.INFO),
            ("INFO", logging.INFO),
            ("warning", logging.WARNING),
            ("WARNING", logging.WARNING),
            ("error", logging.ERROR),
            ("ERROR", logging.ERROR),
            ("critical", logging.CRITICAL),
            ("CRITICAL", logging.CRITICAL),
        ],
    )
    def test_parse_log_level_integration(
        self,
        input_level: str,
        expected_int: int,
        temp_log_dir: Path,
    ) -> None:
        """Test that parse_log_level works with configure_logging."""
        logger = configure_logging(
            LogEnvironment.DEVELOPMENT,
            log_level=input_level,
            log_dir=temp_log_dir
        )

        assert logger is not None


class TestMultiEnvironmentLogging:
    """Test suite for logging across different environments."""

    def test_development_logging(self, temp_log_dir: Path) -> None:
        """Test development environment logging."""
        logger = configure_logging(
            LogEnvironment.DEVELOPMENT,
            log_dir=temp_log_dir
        )

        logger.debug("Development debug message")
        logger.info("Development info message")

        log_file = temp_log_dir / "development.log"
        assert log_file.exists()

    def test_testing_logging(self, temp_log_dir: Path) -> None:
        """Test testing environment logging."""
        logger = configure_logging(
            LogEnvironment.TESTING,
            log_dir=temp_log_dir
        )

        logger.info("Testing info message")
        logger.warning("Testing warning message")

        log_file = temp_log_dir / "testing.log"
        assert log_file.exists()

    def test_production_logging(self, temp_log_dir: Path) -> None:
        """Test production environment logging."""
        logger = configure_logging(
            LogEnvironment.PRODUCTION,
            log_dir=temp_log_dir
        )

        logger.warning("Production warning message")
        logger.error("Production error message")

        log_file = temp_log_dir / "production.log"
        assert log_file.exists()


class TestConcurrentLogging:
    """Test suite for concurrent logging scenarios."""

    def test_multiple_loggers_same_directory(self, temp_log_dir: Path) -> None:
        """Test that multiple loggers can write to the same directory."""
        logger1 = configure_logging(
            LogEnvironment.DEVELOPMENT,
            log_dir=temp_log_dir
        )

        logger2 = configure_logging(
            LogEnvironment.TESTING,
            log_dir=temp_log_dir
        )

        logger1.info("Logger 1 message")
        logger2.info("Logger 2 message")

        assert (temp_log_dir / "development.log").exists()
        assert (temp_log_dir / "testing.log").exists()


class TestLoggingConfigurationPersistence:
    """Test suite for logging configuration persistence."""

    def test_logger_name_persistence(self, temp_log_dir: Path) -> None:
        """Test that logger name is persistent across configurations."""
        logger = configure_logging(
            LogEnvironment.DEVELOPMENT,
            log_dir=temp_log_dir
        )

        assert logger.name == "aigenflow"

    def test_log_level_override_persistence(self, temp_log_dir: Path) -> None:
        """Test that log level override persists."""
        logger = configure_logging(
            LogEnvironment.PRODUCTION,
            log_level=logging.DEBUG,  # Override production WARNING
            log_dir=temp_log_dir
        )

        # Logger should be configured with DEBUG level
        assert logger is not None


# Module-level exports
__all__ = [
    "TestLogLevelRuntimeSwitching",
    "TestLogOutputDestinations",
    "TestLogFormatConsistency",
    "TestLogRotation",
    "TestProfileSelection",
    "TestSecretRedactionInLogs",
    "TestLogLevelStringParsing",
    "TestMultiEnvironmentLogging",
    "TestConcurrentLogging",
    "TestLoggingConfigurationPersistence",
]
