"""
Tests for CLI setup command.

Uses TDD approach: tests written before implementation.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from cli.setup import app as setup_app

runner = CliRunner()


class TestSetupCommand:
    """Test suite for setup command."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings fixture."""
        settings = MagicMock()
        settings.debug = False
        settings.playwright_headless = True
        settings.profile_dir = MagicMock()
        return settings

    @pytest.fixture
    def mock_session_manager(self, mock_settings):
        """Mock session manager."""
        manager = MagicMock()
        manager.login_all_expired = AsyncMock(return_value=None)
        manager.save_all_sessions = AsyncMock(return_value=None)
        return manager

    def test_setup_default_headless(self, mock_session_manager, mock_settings):
        """Test setup command with default headless mode."""
        with patch("cli.setup.get_settings", return_value=mock_settings):
            with patch("cli.setup.SessionManager", return_value=mock_session_manager):
                with patch("cli.setup._check_browser_installation", return_value=True):
                    with patch("asyncio.run"):
                        result = runner.invoke(setup_app)
                        # Should succeed even in headless mode
                        assert result.exit_code == 0

    def test_setup_headed_mode(self, mock_session_manager, mock_settings):
        """Test setup command with headed browser."""
        mock_settings.playwright_headless = False

        with patch("cli.setup.get_settings", return_value=mock_settings):
            with patch("cli.setup.SessionManager", return_value=mock_session_manager):
                with patch("cli.setup._check_browser_installation", return_value=True):
                    with patch("asyncio.run"):
                        result = runner.invoke(setup_app, ["--headed"])
                        assert result.exit_code == 0

    def test_setup_browser_not_installed(self, mock_settings):
        """Test setup command when Playwright browser is not installed."""
        with patch("cli.setup.get_settings", return_value=mock_settings):
            with patch("cli.setup._check_browser_installation", return_value=False):
                result = runner.invoke(setup_app)
                assert result.exit_code != 0
                assert "browser" in result.stdout.lower() or "playwright" in result.stdout.lower()

    def test_setup_specific_provider(self, mock_session_manager, mock_settings):
        """Test setup command for specific provider."""
        mock_settings.playwright_headless = False

        with patch("cli.setup.get_settings", return_value=mock_settings):
            with patch("cli.setup.SessionManager", return_value=mock_session_manager):
                with patch("cli.setup._check_browser_installation", return_value=True):
                    with patch("asyncio.run"):
                        result = runner.invoke(setup_app, ["--provider", "claude"])
                        assert result.exit_code == 0

    def test_setup_invalid_provider(self, mock_settings):
        """Test setup command with invalid provider name."""
        with patch("cli.setup.get_settings", return_value=mock_settings):
            with patch("cli.setup._check_browser_installation", return_value=True):
                result = runner.invoke(setup_app, ["--provider", "invalid"])
                assert result.exit_code != 0
                assert "invalid" in result.stdout.lower() or "provider" in result.stdout.lower()
