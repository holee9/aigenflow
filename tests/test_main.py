"""
Tests for CLI layer.
"""

from unittest.mock import MagicMock

from typer import Context as TyperContext


class TestCLI:
    """Tests for CLI application."""

    def test_main_function_exists(self):
        """Test that main function exists."""
        from main import main

        assert main is not None
        assert callable(main)

    def test_main_execution(self):
        """Test main execution doesn't crash."""
        from main import main

        # Just test that main can be called without error
        # (it will print help and exit normally)
        try:
            main(
                ctx=MagicMock(spec=TyperContext, invoked_subcommand=None),
                version=False,
                log_level="warning",
                environment="production",
            )
        except SystemExit:
            # Expected - typer Exit raises SystemExit
            pass
