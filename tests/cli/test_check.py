"""
Tests for CLI check command.

Uses TDD approach: tests written before implementation.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from cli.check import app as check_app

runner = CliRunner()


class TestCheckCommand:
    """Test suite for check command."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings fixture."""
        settings = MagicMock()
        settings.debug = False
        return settings

    @pytest.fixture
    def mock_session_manager(self, mock_settings):
        """Mock session manager with all providers logged in."""
        manager = MagicMock()
        manager.check_all_sessions = AsyncMock(return_value={
            "chatgpt": True,
            "claude": True,
            "gemini": True,
            "perplexity": True,
        })
        manager.providers = {
            "chatgpt": MagicMock(),
            "claude": MagicMock(),
            "gemini": MagicMock(),
            "perplexity": MagicMock(),
        }
        manager.load_all_sessions = MagicMock()
        return manager

    def test_check_all_sessions_valid(self, mock_session_manager, mock_settings):
        """Test check command when all sessions are valid."""
        # Mock the async _check_sessions function to return the dict directly
        expected_status = {
            "chatgpt": True,
            "claude": True,
            "gemini": True,
            "perplexity": True,
        }

        # Mock asyncio.run to return our mock result
        with patch("asyncio.run", return_value=expected_status):
            with patch("cli.check.get_settings", return_value=mock_settings):
                with patch("cli.check.SessionManager", return_value=mock_session_manager):
                    with patch("cli.check._check_browser_installation", return_value=True):
                        result = runner.invoke(check_app)
                        assert result.exit_code == 0
                        assert "✓" in result.stdout or "valid" in result.stdout.lower() or "operational" in result.stdout.lower()

    def test_check_some_sessions_invalid(self, mock_settings):
        """Test check command when some sessions are invalid."""
        manager = MagicMock()
        manager.check_all_sessions = AsyncMock(return_value={
            "chatgpt": True,
            "claude": False,
            "gemini": True,
            "perplexity": False,
        })
        manager.providers = {
            "chatgpt": MagicMock(),
            "claude": MagicMock(),
            "gemini": MagicMock(),
            "perplexity": MagicMock(),
        }
        manager.load_all_sessions = MagicMock()

        expected_status = {
            "chatgpt": True,
            "claude": False,
            "gemini": True,
            "perplexity": False,
        }

        with patch("asyncio.run", return_value=expected_status):
            with patch("cli.check.get_settings", return_value=mock_settings):
                with patch("cli.check.SessionManager", return_value=manager):
                    with patch("cli.check._check_browser_installation", return_value=True):
                        result = runner.invoke(check_app)
                        print(f"Exit code: {result.exit_code}")
                        print(f"Output: {result.stdout}")
                        if result.exception:
                            print(f"Exception: {result.exception}")
                        # Should exit with error when some sessions are invalid
                        assert result.exit_code != 0
                        # Should show mixed status with both valid and invalid
                        assert "✓" in result.stdout or "Valid" in result.stdout
                        assert "✗" in result.stdout or "Invalid" in result.stdout

    def test_check_browser_not_installed(self, mock_settings):
        """Test check command when Playwright browser is not installed."""
        manager = MagicMock()
        manager.check_all_sessions = AsyncMock(side_effect=Exception("Browser not installed"))
        manager.load_all_sessions = MagicMock()

        expected_status = {
            "chatgpt": True,
            "claude": False,
            "gemini": True,
            "perplexity": False,
        }

        with patch("asyncio.run", return_value=expected_status):
            with patch("cli.check.get_settings", return_value=mock_settings):
                with patch("cli.check.SessionManager", return_value=manager):
                    with patch("cli.check._check_browser_installation", return_value=False):
                        result = runner.invoke(check_app)
                        assert result.exit_code != 0
                        assert "browser" in result.stdout.lower() or "not installed" in result.stdout.lower()

    def test_check_verbose_mode(self, mock_session_manager, mock_settings):
        """Test check command with verbose output."""
        mock_settings.debug = True

        expected_status = {
            "chatgpt": True,
            "claude": True,
            "gemini": True,
            "perplexity": True,
        }

        with patch("asyncio.run", return_value=expected_status):
            with patch("cli.check.get_settings", return_value=mock_settings):
                with patch("cli.check.SessionManager", return_value=mock_session_manager):
                    with patch("cli.check._check_browser_installation", return_value=True):
                        result = runner.invoke(check_app, ["--verbose"])
                        assert result.exit_code == 0
                        # Verbose mode should show more details
