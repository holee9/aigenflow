"""Integration tests for CLI logging options."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestCLILoggingOptions:
    """Test CLI logging options."""

    @patch("core.logger.setup_logging")
    @patch("main._preserve_run_command")
    def test_log_level_option_debug(self, mock_preserve, mock_setup):
        """CLI --log-level debug configures logging correctly."""
        from main import main

        try:
            main(
                ctx=MagicMock(invoked_subcommand=None),
                version=False,
                log_level="debug",
                log_file=None,
            )
        except SystemExit:
            pass

        # Verify setup_logging was called with debug level
        mock_setup.assert_called_once()
        call_args = mock_setup.call_args
        # The call passes a profile with DEBUG level
        profile = call_args.kwargs.get("profile")
        assert profile is not None
        assert profile.log_level.value == "DEBUG"

    @patch("core.logger.setup_logging")
    @patch("main._preserve_run_command")
    def test_log_file_option(self, mock_preserve, mock_setup):
        """CLI --log-file option configures custom log file."""
        from main import main

        custom_log = Path("custom.log")
        try:
            main(
                ctx=MagicMock(invoked_subcommand=None),
                version=False,
                log_level=None,
                log_file=custom_log,
            )
        except SystemExit:
            pass

        # Verify setup_logging was called with custom log file
        mock_setup.assert_called_once()
        call_args = mock_setup.call_args
        # The call passes a profile with custom log file
        profile = call_args.kwargs.get("profile")
        assert profile is not None
        assert profile.log_file_path == custom_log

    @patch("core.logger.setup_logging")
    @patch("main._preserve_run_command")
    def test_invalid_log_level(self, mock_preserve, mock_setup):
        """Invalid log level shows error and exits."""
        from typer import Exit as TyperExit

        from main import main

        with pytest.raises((TyperExit, SystemExit)):
            main(
                ctx=MagicMock(invoked_subcommand=None),
                version=False,
                log_level="invalid",
                log_file=None,
            )

    @patch("core.logger.setup_logging")
    @patch("main._preserve_run_command")
    def test_default_logging_config(self, mock_preserve, mock_setup):
        """Without options, uses default logging configuration."""
        from main import main

        try:
            main(
                ctx=MagicMock(invoked_subcommand=None),
                version=False,
                log_level=None,
                log_file=None,
            )
        except SystemExit:
            pass

        # Verify setup_logging was called with defaults
        mock_setup.assert_called_once()
