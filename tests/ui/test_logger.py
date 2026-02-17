"""
Tests for LogStream class.

Uses TDD approach: tests written before implementation.
"""

from datetime import datetime

from src.ui.logger import LogLevel, LogStream


class TestLogStream:
    """Test suite for LogStream class."""

    def test_init_default_console(self):
        """Test LogStream initializes with default console."""
        logger = LogStream()

        assert logger.console is not None
        assert logger.get_log_count() == 0

    def test_init_custom_console(self):
        """Test LogStream initializes with custom console."""
        from rich.console import Console

        console = Console()
        logger = LogStream(console=console)

        assert logger.console == console

    def test_log_increments_count(self):
        """Test log increments log count."""
        logger = LogStream()

        logger.log("Test message")
        assert logger.get_log_count() == 1

        logger.log("Another message")
        assert logger.get_log_count() == 2

    def test_log_with_level(self):
        """Test log with different levels."""
        logger = LogStream()

        logger.log("Debug message", LogLevel.DEBUG)
        assert logger.get_log_count() == 1

        logger.log("Info message", LogLevel.INFO)
        assert logger.get_log_count() == 2

        logger.log("Warning message", LogLevel.WARNING)
        assert logger.get_log_count() == 3

        logger.log("Error message", LogLevel.ERROR)
        assert logger.get_log_count() == 4

        logger.log("Critical message", LogLevel.CRITICAL)
        assert logger.get_log_count() == 5

    def test_log_with_timestamp(self):
        """Test log with custom timestamp."""
        logger = LogStream()
        ts = datetime(2026, 2, 16, 12, 0, 0)

        logger.log("Test message", timestamp=ts)

        assert logger.get_log_count() == 1

    def test_info_convenience_method(self):
        """Test info convenience method."""
        logger = LogStream()

        logger.info("Info message")

        assert logger.get_log_count() == 1

    def test_warning_convenience_method(self):
        """Test warning convenience method."""
        logger = LogStream()

        logger.warning("Warning message")

        assert logger.get_log_count() == 1

    def test_error_convenience_method(self):
        """Test error convenience method."""
        logger = LogStream()

        logger.error("Error message")

        assert logger.get_log_count() == 1

    def test_debug_convenience_method(self):
        """Test debug convenience method."""
        logger = LogStream()

        logger.debug("Debug message")

        assert logger.get_log_count() == 1

    def test_critical_convenience_method(self):
        """Test critical convenience method."""
        logger = LogStream()

        logger.critical("Critical message")

        assert logger.get_log_count() == 1

    def test_multiple_logs(self):
        """Test multiple log messages."""
        logger = LogStream()

        for i in range(10):
            logger.info(f"Message {i}")

        assert logger.get_log_count() == 10

    def test_get_log_count(self):
        """Test get_log_count returns correct count."""
        logger = LogStream()

        assert logger.get_log_count() == 0

        logger.info("Message 1")
        assert logger.get_log_count() == 1

        logger.info("Message 2")
        assert logger.get_log_count() == 2
