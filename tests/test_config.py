"""
Test configuration for all modules.
"""

import pytest
from pathlib import Path

from core.config import AigenFlowSettings
from gateway.base import BaseProvider


def test_settings_loading():
    """Test that settings can be loaded."""
    settings = AigenFlowSettings()

    assert settings.app_name == "aigenflow"
    assert settings.output_dir == Path("output")
    assert settings.profiles_dir == Path("~/.aigenflow/profiles").expanduser()


def test_profile_directory_creation():
    """Test that profile directory is created if needed."""
    settings = AigenFlowSettings()
    profiles_dir = settings.profiles_dir

    # Directory should be created by settings validation
    assert profiles_dir.exists()


def test_api_secrets_load_from_environment(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test-key")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test-key")
    monkeypatch.setenv("PERPLEXITY_SESSION_TOKEN", "px-session")
    monkeypatch.setenv("PERPLEXITY_CSRF_TOKEN", "px-csrf")

    settings = AigenFlowSettings()

    assert settings.openai_api_key == "openai-test-key"
    assert settings.gemini_api_key == "gemini-test-key"
    assert settings.perplexity_session_token == "px-session"
    assert settings.perplexity_csrf_token == "px-csrf"
