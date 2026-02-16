"""
Tests for gateway modules.
"""

from pathlib import Path
from textwrap import dedent
from typing import Any

import pytest
import yaml

from src.gateway.base import BaseProvider
from src.gateway.chatgpt_provider import ChatGPTProvider
from src.gateway.claude_provider import ClaudeProvider
from src.gateway.gemini_provider import GeminiProvider
from src.gateway.perplexity_provider import PerplexityProvider
from src.gateway.selector_loader import SelectorLoader


class TestBaseProvider:
    """Tests for BaseProvider interface."""

    def test_cannot_instantiate(self):
        """BaseProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseProvider(profile_dir="dummy")


class TestBaseProviderSelectorIntegration:
    """
    Tests for BaseProvider selector loader integration (TASK-003).

    Tests that providers can use SelectorLoader to access DOM selectors.
    """

    def test_provider_without_selector_loader(self):
        """Test provider without selector loader returns None."""
        provider = ClaudeProvider(profile_dir=Path("/tmp/claude"))

        # Without selector_loader, get_selector returns None
        assert provider.get_selector("chat_input") is None
        assert provider.get_all_selectors() == {}

    def test_provider_with_selector_loader(self, tmp_path: Path) -> None:
        """Test provider with selector loader returns correct selectors."""
        # Create test selectors file
        selectors_data = {
            "providers": {
                "claude": {
                    "base_url": "https://claude.ai",
                    "chat_input": "[contenteditable='true']",
                    "send_button": "button[aria-label='Send']",
                    "response_container": "[data-testid='conversation-turn']",
                }
            }
        }
        selector_file = tmp_path / "selectors.yaml"
        with open(selector_file, "w") as f:
            yaml.dump(selectors_data, f)

        loader = SelectorLoader(selector_file)
        provider = ClaudeProvider(
            profile_dir=Path("/tmp/claude"),
            selector_loader=loader,
        )

        # Get individual selector
        chat_input = provider.get_selector("chat_input")
        assert chat_input == "[contenteditable='true']"

        # Get all selectors
        selectors = provider.get_all_selectors()
        assert selectors["chat_input"] == "[contenteditable='true']"
        assert selectors["send_button"] == "button[aria-label='Send']"

    def test_provider_get_base_url_from_selectors(self, tmp_path: Path) -> None:
        """Test getting base URL from selector configuration."""
        selectors_data = {
            "providers": {
                "gemini": {
                    "base_url": "https://gemini.google.com",
                    "chat_input": ".ql-editor",
                    "send_button": "button[aria-label='Send']",
                    "response_container": ".model-response",
                }
            }
        }
        selector_file = tmp_path / "selectors.yaml"
        with open(selector_file, "w") as f:
            yaml.dump(selectors_data, f)

        loader = SelectorLoader(selector_file)
        provider = GeminiProvider(
            profile_dir=Path("/tmp/gemini"),
            selector_loader=loader,
        )

        base_url = provider.get_base_url()
        assert base_url == "https://gemini.google.com"

    def test_provider_get_optional_selector(self, tmp_path: Path) -> None:
        """Test getting optional selector returns None when not present."""
        selectors_data = {
            "providers": {
                "chatgpt": {
                    "chat_input": "#prompt-textarea",
                    "send_button": "button[data-testid='send-button']",
                    "response_container": "[data-message-author-role='assistant']",
                }
            }
        }
        selector_file = tmp_path / "selectors.yaml"
        with open(selector_file, "w") as f:
            yaml.dump(selectors_data, f)

        loader = SelectorLoader(selector_file)
        provider = ChatGPTProvider(
            profile_dir=Path("/tmp/chatgpt"),
            selector_loader=loader,
        )

        # Optional selector not in config returns None
        logout = provider.get_selector("logout_button", optional=True)
        assert logout is None

    def test_all_providers_use_selectors(self, tmp_path: Path) -> None:
        """Test that all providers can use the selector loader."""
        selectors_data = {
            "providers": {
                "claude": {
                    "chat_input": ".claude-input",
                    "send_button": ".claude-send",
                    "response_container": ".claude-response",
                },
                "gemini": {
                    "chat_input": ".gemini-input",
                    "send_button": ".gemini-send",
                    "response_container": ".gemini-response",
                },
                "chatgpt": {
                    "chat_input": ".chatgpt-input",
                    "send_button": ".chatgpt-send",
                    "response_container": ".chatgpt-response",
                },
                "perplexity": {
                    "chat_input": ".perplexity-input",
                    "send_button": ".perplexity-send",
                    "response_container": ".perplexity-response",
                },
            }
        }
        selector_file = tmp_path / "selectors.yaml"
        with open(selector_file, "w") as f:
            yaml.dump(selectors_data, f)

        loader = SelectorLoader(selector_file)
        config = loader.load()

        # Verify each provider can get their selectors
        for provider_class, provider_name in [
            (ClaudeProvider, "claude"),
            (GeminiProvider, "gemini"),
            (ChatGPTProvider, "chatgpt"),
            (PerplexityProvider, "perplexity"),
        ]:
            provider = provider_class(
                profile_dir=Path(f"/tmp/{provider_name}"),
                selector_loader=loader,
            )
            chat_input = provider.get_selector("chat_input")
            assert chat_input == f".{provider_name}-input"


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
