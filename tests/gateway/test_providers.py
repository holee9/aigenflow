"""
Tests for gateway modules.
"""

import pytest

from gateway.base import BaseProvider
from gateway.chatgpt_provider import ChatGPTProvider
from gateway.claude_provider import ClaudeProvider
from gateway.gemini_provider import GeminiProvider
from gateway.perplexity_provider import PerplexityProvider


class TestBaseProvider:
    """Tests for BaseProvider interface."""

    def test_cannot_instantiate(self):
        """BaseProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseProvider(profile_dir="dummy")


class TestChatGPTProvider:
    """Tests for ChatGPT provider."""

    def test_init(self):
        """Test provider initialization."""
        provider = ChatGPTProvider(profile_dir="~/.aigenflow/profiles/chatgpt")
        assert provider.base_url == "https://chat.openai.com"

    def test_send_message(self):
        """Test send_message method."""
        provider = ChatGPTProvider(profile_dir="~/.aigenflow/profiles/chatgpt")

        # TODO: Test actual message sending
        # response = await provider.send_message(request)
        # assert response.success


class TestClaudeProvider:
    """Tests for Claude provider."""

    def test_init(self):
        """Test provider initialization."""
        provider = ClaudeProvider(profile_dir="~/.aigenflow/profiles/claude")
        assert provider.base_url == "https://claude.ai"


class TestGeminiProvider:
    """Tests for Gemini provider."""

    def test_init(self):
        """Test provider initialization."""
        provider = GeminiProvider(profile_dir="~/.aigenflow/profiles/gemini")
        assert provider.base_url == "https://gemini.google.com"


class TestPerplexityProvider:
    """Tests for Perplexity provider."""

    def test_init(self):
        """Test provider initialization."""
        provider = PerplexityProvider(profile_dir="~/.aigenflow/profiles/perplexity")
        assert provider.base_url == "https://perplexity.ai"
