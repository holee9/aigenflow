"""
Tests for SelectorLoader.

Tests follow TDD principles: written before implementation.
"""

from pathlib import Path
from typing import Any

import pytest
import yaml

from src.gateway.selector_loader import (
    SelectorConfig,
    SelectorLoader,
    SelectorValidationError,
)


class TestSelectorLoader:
    """Test suite for SelectorLoader class."""

    def test_init_with_valid_path(self, tmp_path: Path) -> None:
        """Test initialization with a valid selector file path."""
        loader = SelectorLoader(tmp_path / "selectors.yaml")
        assert loader.selector_path == tmp_path / "selectors.yaml"

    def test_load_selectors_success(self, tmp_path: Path) -> None:
        """Test successful loading of selectors from valid YAML."""
        # Create test selectors file
        selectors_data = {
            "providers": {
                "claude": {
                    "base_url": "https://claude.ai",
                    "chat_input": "[contenteditable]",
                    "send_button": "button[aria-label='Send']",
                    "response_container": "[data-testid='conversation-turn']",
                }
            },
            "version": "1.0.0",
        }
        selector_file = tmp_path / "selectors.yaml"
        with open(selector_file, "w") as f:
            yaml.dump(selectors_data, f)

        loader = SelectorLoader(selector_file)
        config = loader.load()

        assert isinstance(config, SelectorConfig)
        assert config.providers["claude"]["chat_input"] == "[contenteditable]"
        assert config.version == "1.0.0"

    def test_load_selectors_file_not_found(self, tmp_path: Path) -> None:
        """Test loading fails when selector file does not exist."""
        loader = SelectorLoader(tmp_path / "nonexistent.yaml")

        with pytest.raises(SelectorValidationError, match="Selector file not found"):
            loader.load()

    def test_load_selectors_invalid_yaml(self, tmp_path: Path) -> None:
        """Test loading fails with invalid YAML syntax."""
        selector_file = tmp_path / "selectors.yaml"
        with open(selector_file, "w") as f:
            f.write("invalid: yaml: content:\n  - broken")

        loader = SelectorLoader(selector_file)

        with pytest.raises(SelectorValidationError, match="Invalid YAML"):
            loader.load()

    def test_load_selectors_missing_required_fields(self, tmp_path: Path) -> None:
        """Test validation fails when required selectors are missing."""
        selectors_data = {
            "providers": {
                "claude": {
                    "base_url": "https://claude.ai",
                    # Missing required: chat_input, send_button, response_container
                }
            }
        }
        selector_file = tmp_path / "selectors.yaml"
        with open(selector_file, "w") as f:
            yaml.dump(selectors_data, f)

        loader = SelectorLoader(selector_file)

        with pytest.raises(SelectorValidationError, match="Required selector"):
            loader.load()

    def test_get_selector_success(self, tmp_path: Path) -> None:
        """Test retrieving a specific selector value."""
        selectors_data = {
            "providers": {
                "claude": {
                    "chat_input": ".chat-input",
                    "send_button": ".send-btn",
                    "response_container": ".response",
                }
            }
        }
        selector_file = tmp_path / "selectors.yaml"
        with open(selector_file, "w") as f:
            yaml.dump(selectors_data, f)

        loader = SelectorLoader(selector_file)
        config = loader.load()

        assert loader.get_selector(config, "claude", "chat_input") == ".chat-input"
        assert loader.get_selector(config, "claude", "send_button") == ".send-btn"

    def test_get_selector_provider_not_found(self, tmp_path: Path) -> None:
        """Test getting selector for non-existent provider."""
        selectors_data = {
            "providers": {
                "claude": {
                    "chat_input": ".input",
                    "send_button": ".send",
                    "response_container": ".response",
                }
            }
        }
        selector_file = tmp_path / "selectors.yaml"
        with open(selector_file, "w") as f:
            yaml.dump(selectors_data, f)

        loader = SelectorLoader(selector_file)
        config = loader.load()

        with pytest.raises(SelectorValidationError, match="Provider not found"):
            loader.get_selector(config, "gemini", "chat_input")

    def test_get_selector_key_not_found(self, tmp_path: Path) -> None:
        """Test getting non-existent selector key."""
        selectors_data = {
            "providers": {
                "claude": {
                    "chat_input": ".input",
                    "send_button": ".send",
                    "response_container": ".response",
                }
            }
        }
        selector_file = tmp_path / "selectors.yaml"
        with open(selector_file, "w") as f:
            yaml.dump(selectors_data, f)

        loader = SelectorLoader(selector_file)
        config = loader.load()

        with pytest.raises(SelectorValidationError, match="Selector key not found"):
            loader.get_selector(config, "claude", "nonexistent")

    def test_get_selector_with_optional_key(self, tmp_path: Path) -> None:
        """Test getting optional selector returns None when not present."""
        selectors_data = {
            "providers": {
                "claude": {
                    "chat_input": ".input",
                    "send_button": ".send",
                    "response_container": ".response",
                }
            }
        }
        selector_file = tmp_path / "selectors.yaml"
        with open(selector_file, "w") as f:
            yaml.dump(selectors_data, f)

        loader = SelectorLoader(selector_file)
        config = loader.load()

        # Optional selector should return None instead of raising
        result = loader.get_selector(config, "claude", "logout_button", optional=True)
        assert result is None

    def test_validate_all_providers_have_required(self, tmp_path: Path) -> None:
        """Test that all providers must have required selectors."""
        selectors_data = {
            "providers": {
                "claude": {
                    "chat_input": ".input",
                    "send_button": ".send",
                    "response_container": ".response",
                },
                "gemini": {
                    "chat_input": ".input",
                    # Missing send_button and response_container
                },
            }
        }
        selector_file = tmp_path / "selectors.yaml"
        with open(selector_file, "w") as f:
            yaml.dump(selectors_data, f)

        loader = SelectorLoader(selector_file)

        with pytest.raises(SelectorValidationError, match="Required selector"):
            loader.load()

    def test_reload_after_file_change(self, tmp_path: Path) -> None:
        """Test that reloading picks up file changes."""
        selectors_data = {
            "providers": {
                "claude": {
                    "chat_input": ".old-input",
                    "send_button": ".send",
                    "response_container": ".response",
                }
            }
        }
        selector_file = tmp_path / "selectors.yaml"
        with open(selector_file, "w") as f:
            yaml.dump(selectors_data, f)

        loader = SelectorLoader(selector_file)
        config1 = loader.load()
        assert loader.get_selector(config1, "claude", "chat_input") == ".old-input"

        # Update file
        selectors_data["providers"]["claude"]["chat_input"] = ".new-input"
        with open(selector_file, "w") as f:
            yaml.dump(selectors_data, f)

        config2 = loader.load()
        assert loader.get_selector(config2, "claude", "chat_input") == ".new-input"

    def test_get_all_selectors_for_provider(self, tmp_path: Path) -> None:
        """Test getting all selectors for a specific provider."""
        selectors_data = {
            "providers": {
                "claude": {
                    "chat_input": ".input",
                    "send_button": ".send",
                    "response_container": ".response",
                }
            }
        }
        selector_file = tmp_path / "selectors.yaml"
        with open(selector_file, "w") as f:
            yaml.dump(selectors_data, f)

        loader = SelectorLoader(selector_file)
        config = loader.load()

        selectors = loader.get_provider_selectors(config, "claude")
        assert selectors["chat_input"] == ".input"
        assert selectors["send_button"] == ".send"
        assert selectors["response_container"] == ".response"


class TestSelectorConfig:
    """Test suite for SelectorConfig Pydantic model."""

    def test_valid_config_parsing(self) -> None:
        """Test parsing valid selector configuration."""
        data: dict[str, Any] = {
            "providers": {
                "claude": {
                    "chat_input": ".input",
                    "send_button": ".send",
                    "response_container": ".response",
                }
            },
            "version": "1.0.0",
            "validation": {
                "required_selectors": ["chat_input", "send_button", "response_container"],
            },
        }

        config = SelectorConfig(**data)
        assert config.providers["claude"]["chat_input"] == ".input"
        assert config.version == "1.0.0"

    def test_config_with_empty_validation_defaults(self) -> None:
        """Test config with missing validation section uses defaults."""
        data: dict[str, Any] = {
            "providers": {
                "claude": {
                    "chat_input": ".input",
                    "send_button": ".send",
                    "response_container": ".response",
                }
            }
        }

        config = SelectorConfig(**data)
        assert config.validation.required_selectors == ["chat_input", "send_button", "response_container"]
