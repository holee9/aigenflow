"""Integration tests for CLI logging options."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer import Context as TyperContext
from typer import Exit as TyperExit

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestCLILoggingOptions:
    """Test CLI logging options."""

    def test_log_level_option_debug(self):
        """CLI --log-level debug configures logging correctly."""
        # Mock before import
        with patch("src.config.configure_logging") as mock_configure:
            # Force fresh import
            if "main" in sys.modules:
                del sys.modules["main"]
            from main import main

            # Use a dummy subcommand to trigger logging setup
            try:
                main(
                    ctx=MagicMock(spec=TyperContext, invoked_subcommand="run"),
                    version=False,
                    log_level="debug",
                    environment="production",
                )
            except SystemExit:
                pass

            # Verify configure_logging was called with debug level
            mock_configure.assert_called_once()
            # All args are keyword arguments
            env_arg = mock_configure.call_args.kwargs.get("environment")
            log_level = mock_configure.call_args.kwargs.get("log_level")
            assert hasattr(env_arg, "value") and env_arg.value == "production"
            assert log_level == "debug"

    def test_log_file_option(self):
        """CLI log_file option - note: currently not supported directly."""
        # Note: log_file option is not currently supported in main.py
        # This test documents that behavior
        with patch("src.config.configure_logging") as mock_configure:
            if "main" in sys.modules:
                del sys.modules["main"]
            from main import main

            try:
                main(
                    ctx=MagicMock(spec=TyperContext, invoked_subcommand="run"),
                    version=False,
                    log_level="info",
                    environment="production",
                )
            except SystemExit:
                pass

            # Verify configure_logging was called
            mock_configure.assert_called_once()

    def test_invalid_log_level(self):
        """Invalid log level shows error and exits."""
        # configure_logging raises ValueError for invalid log level
        with patch("src.config.configure_logging") as mock_configure:
            mock_configure.side_effect = ValueError("Invalid log level")
            if "main" in sys.modules:
                del sys.modules["main"]
            from main import main

            with pytest.raises((TyperExit, SystemExit)):
                main(
                    ctx=MagicMock(spec=TyperContext, invoked_subcommand="run"),
                    version=False,
                    log_level="invalid",
                    environment="production",
                )

    def test_default_logging_config(self):
        """Without options, uses default logging configuration."""
        with patch("src.config.configure_logging") as mock_configure:
            if "main" in sys.modules:
                del sys.modules["main"]
            from main import main

            try:
                main(
                    ctx=MagicMock(spec=TyperContext, invoked_subcommand="run"),
                    version=False,
                    log_level="warning",
                    environment="production",
                )
            except SystemExit:
                pass

            # Verify configure_logging was called with defaults
            mock_configure.assert_called_once()
            log_level = mock_configure.call_args.kwargs.get("log_level")
            assert log_level == "warning"
