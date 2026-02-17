"""
Tests for gateway session management.
"""

import pytest

from gateway.chatgpt_provider import ChatGPTProvider
from gateway.claude_provider import ClaudeProvider
from gateway.session import SessionManager


class TestSessionManager:
    """Tests for SessionManager."""

    def test_init(self):
        """Test SessionManager initialization."""
        manager = SessionManager()

    def test_register_provider(self):
        """Test provider registration."""
        manager = SessionManager()
        provider = ChatGPTProvider(profile_dir="dummy")

        manager.register("chatgpt", provider)
        assert "chatgpt" in manager.providers

    @pytest.mark.anyio
    async def test_get_valid_session(self):
        """Test get_valid_session returns valid provider."""
        manager = SessionManager()
        provider = ChatGPTProvider(profile_dir="dummy")
        manager.register("chatgpt", provider)

        # Mock valid session
        manager.providers["chatgpt"].is_logged_in = True

        valid = await manager.get_valid_session()
        assert valid == manager.providers["chatgpt"]

    @pytest.mark.anyio
    async def test_check_all_sessions(self):
        """Test check_all_sessions returns status dict."""
        manager = SessionManager()
        manager.register("chatgpt", ChatGPTProvider(profile_dir="dummy"))
        manager.register("claude", ClaudeProvider(profile_dir="dummy"))

        manager.providers["chatgpt"].is_logged_in = True

        results = await manager.check_all_sessions()
        assert "chatgpt" in results
        assert "claude" in results

    @pytest.mark.anyio
    async def test_login_all_expired(self):
        """Test login_all_expired method."""
        manager = SessionManager()
        manager.register("chatgpt", ChatGPTProvider(profile_dir="dummy"))
        manager.providers["chatgpt"].is_logged_in = False

        # Should run login flow
        await manager.login_all_expired()
