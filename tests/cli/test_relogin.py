"""
Tests for CLI relogin command.

Uses TDD approach: tests written before implementation.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from cli.relogin import app as relogin_app

runner = CliRunner()


class TestReloginCommand:
    """Test suite for relogin command."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings fixture."""
        settings = MagicMock()
        settings.playwright_headless = False
        return settings

    @pytest.fixture
    def mock_provider(self):
        """Mock provider fixture."""
        provider = MagicMock()
        provider.check_session = AsyncMock(return_value=False)
        provider.login_flow = AsyncMock(return_value=None)
        provider.save_session = MagicMock(return_value=None)
        return provider

    def test_relogin_chatgpt(self, mock_provider, mock_settings):
        """Test relogin command for ChatGPT."""
        with patch("cli.relogin.get_settings", return_value=mock_settings):
            with patch("cli.relogin.ChatGPTProvider", return_value=mock_provider):
                with patch("asyncio.run"):
                    result = runner.invoke(relogin_app, ["chatgpt"])
                    assert result.exit_code == 0

    def test_relogin_claude(self, mock_provider, mock_settings):
        """Test relogin command for Claude."""
        with patch("cli.relogin.get_settings", return_value=mock_settings):
            with patch("cli.relogin.ClaudeProvider", return_value=mock_provider):
                with patch("asyncio.run"):
                    result = runner.invoke(relogin_app, ["claude"])
                    assert result.exit_code == 0

    def test_relogin_invalid_provider(self, mock_settings):
        """Test relogin command with invalid provider."""
        with patch("cli.relogin.get_settings", return_value=mock_settings):
            result = runner.invoke(relogin_app, ["invalid"])
            assert result.exit_code != 0
            assert "invalid" in result.stdout.lower() or "provider" in result.stdout.lower()

    def test_relogin_headed_flag(self, mock_provider, mock_settings):
        """Test relogin command with headed flag."""
        with patch("cli.relogin.get_settings", return_value=mock_settings):
            with patch("cli.relogin.ChatGPTProvider", return_value=mock_provider):
                with patch("asyncio.run"):
                    result = runner.invoke(relogin_app, ["chatgpt", "--headed"])
                    assert result.exit_code == 0
