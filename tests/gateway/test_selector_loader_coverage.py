"""
Tests for gateway/selector_loader.py coverage improvement.
Tests SelectorLoader, SelectorConfig, ProviderSelectors classes.
"""

import tempfile
from pathlib import Path

import pytest
import yaml

from src.core.exceptions import ErrorCode
from src.gateway.selector_loader import (
    ProviderSelectors,
    SelectorConfig,
    SelectorLoader,
    SelectorValidation,
    SelectorValidationError,
)


class TestSelectorValidation:
    """Test SelectorValidation model."""

    def test_default_required_selectors(self) -> None:
        """Test default required selectors."""
        validation = SelectorValidation()
        assert validation.required_selectors == ["chat_input", "send_button", "response_container"]

    def test_default_optional_selectors(self) -> None:
        """Test default optional selectors."""
        validation = SelectorValidation()
        assert validation.optional_selectors == [
            "login_button",
            "logout_button",
            "new_chat_button",
            "username_indicator",
        ]

    def test_custom_required_selectors(self) -> None:
        """Test custom required selectors."""
        validation = SelectorValidation(required_selectors=["chat_input", "send_button"])
        assert validation.required_selectors == ["chat_input", "send_button"]

    def test_custom_optional_selectors(self) -> None:
        """Test custom optional selectors."""
        validation = SelectorValidation(optional_selectors=["logout_button"])
        assert validation.optional_selectors == ["logout_button"]


class TestProviderSelectors:
    """Test ProviderSelectors model."""

    def test_default_values(self) -> None:
        """Test all fields default to None."""
        selectors = ProviderSelectors()
        assert selectors.base_url is None
        assert selectors.login_button is None
        assert selectors.chat_input is None
        assert selectors.send_button is None
        assert selectors.response_container is None
        assert selectors.logout_button is None
        assert selectors.new_chat_button is None
        assert selectors.username_indicator is None

    def test_set_selectors(self) -> None:
        """Test setting selector values."""
        selectors = ProviderSelectors(
            chat_input="#chat-input",
            send_button="#send-button",
            response_container=".response",
        )
        assert selectors.chat_input == "#chat-input"
        assert selectors.send_button == "#send-button"
        assert selectors.response_container == ".response"

    def test_get_method_existing_key(self) -> None:
        """Test get() method with existing key."""
        selectors = ProviderSelectors(chat_input="#chat-input")
        assert selectors.get("chat_input") == "#chat-input"

    def test_get_method_missing_key_with_default(self) -> None:
        """Test get() method with missing key and default."""
        selectors = ProviderSelectors()
        assert selectors.get("missing", "default") == "default"

    def test_get_method_missing_key_no_default(self) -> None:
        """Test get() method with missing key, no default."""
        selectors = ProviderSelectors()
        assert selectors.get("missing") is None


class TestSelectorConfig:
    """Test SelectorConfig model."""

    def test_default_version(self) -> None:
        """Test default version."""
        config = SelectorConfig(providers={})
        assert config.version == "1.0.0"

    def test_custom_version(self) -> None:
        """Test custom version."""
        config = SelectorConfig(providers={}, version="2.0.0")
        assert config.version == "2.0.0"

    def test_default_validation(self) -> None:
        """Test default validation object."""
        config = SelectorConfig(providers={})
        assert isinstance(config.validation, SelectorValidation)
        assert config.validation.required_selectors == ["chat_input", "send_button", "response_container"]

    def test_custom_validation(self) -> None:
        """Test custom validation object."""
        validation = SelectorValidation(required_selectors=["chat_input"])
        config = SelectorConfig(providers={}, validation=validation)
        assert config.validation.required_selectors == ["chat_input"]

    def test_providers_must_be_dict(self) -> None:
        """Test that providers must be a dictionary."""
        with pytest.raises(ValueError, match="providers must be a dictionary"):
            SelectorConfig(providers="invalid")  # type: ignore

    def test_providers_as_dict(self) -> None:
        """Test providers as dictionary."""
        config = SelectorConfig(providers={"claude": {"chat_input": "#input"}})
        assert "claude" in config.providers

    def test_last_updated_optional(self) -> None:
        """Test last_updated is optional."""
        config = SelectorConfig(providers={})
        assert config.last_updated is None

    def test_last_updated_set(self) -> None:
        """Test setting last_updated."""
        config = SelectorConfig(providers={}, last_updated="2024-01-01")
        assert config.last_updated == "2024-01-01"


class TestSelectorLoader:
    """Test SelectorLoader class."""

    def test_init(self) -> None:
        """Test SelectorLoader initialization."""
        selector_file = tempfile.NamedTemporaryFile(suffix=".yaml", delete=True)
        loader = SelectorLoader(Path(selector_file.name))
        assert loader.selector_path == Path(selector_file.name)
        assert loader.config is None

    def test_load_file_not_found(self, tmp_path: Path) -> None:
        """Test load() with non-existent file."""
        loader = SelectorLoader(tmp_path / "nonexistent.yaml")
        with pytest.raises(SelectorValidationError) as exc_info:
            loader.load()
        assert "Selector file not found" in str(exc_info.value)
        assert exc_info.value.error_code == ErrorCode.CONFIG_VALIDATION_FAILED

    def test_load_invalid_yaml(self, tmp_path: Path) -> None:
        """Test load() with invalid YAML syntax."""
        selector_file = tmp_path / "invalid.yaml"
        selector_file.write_text("invalid: yaml: content:\n  - broken", encoding="utf-8")

        loader = SelectorLoader(selector_file)
        with pytest.raises(SelectorValidationError) as exc_info:
            loader.load()
        assert "Invalid YAML syntax" in str(exc_info.value)

    def test_load_empty_file(self, tmp_path: Path) -> None:
        """Test load() with empty file."""
        selector_file = tmp_path / "empty.yaml"
        selector_file.write_text("", encoding="utf-8")

        loader = SelectorLoader(selector_file)
        with pytest.raises(SelectorValidationError) as exc_info:
            loader.load()
        assert "Empty or invalid" in str(exc_info.value)

    def test_load_valid_minimal_config(self, tmp_path: Path) -> None:
        """Test load() with minimal valid configuration."""
        selector_file = tmp_path / "minimal.yaml"
        config_data = {
            "version": "1.0.0",
            "providers": {
                "claude": {
                    "chat_input": "#claude-input",
                    "send_button": "#claude-send",
                    "response_container": ".claude-response",
                }
            },
        }
        selector_file.write_text(yaml.dump(config_data), encoding="utf-8")

        loader = SelectorLoader(selector_file)
        config = loader.load()

        assert config.version == "1.0.0"
        assert "claude" in config.providers
        assert loader.config is not None

    def test_load_with_validation_rules(self, tmp_path: Path) -> None:
        """Test load() with custom validation rules."""
        selector_file = tmp_path / "with_validation.yaml"
        config_data = {
            "version": "1.0.0",
            "validation": {
                "required_selectors": ["chat_input", "send_button"],
                "optional_selectors": ["logout_button"],
            },
            "providers": {
                "claude": {
                    "chat_input": "#input",
                    "send_button": "#send",
                }
            },
        }
        selector_file.write_text(yaml.dump(config_data), encoding="utf-8")

        loader = SelectorLoader(selector_file)
        config = loader.load()

        assert config.validation.required_selectors == ["chat_input", "send_button"]
        assert config.validation.optional_selectors == ["logout_button"]

    def test_load_missing_required_selector(self, tmp_path: Path) -> None:
        """Test load() with missing required selector."""
        selector_file = tmp_path / "missing_required.yaml"
        config_data = {
            "version": "1.0.0",
            "providers": {
                "claude": {
                    "chat_input": "#input",
                    # Missing send_button and response_container
                }
            },
        }
        selector_file.write_text(yaml.dump(config_data), encoding="utf-8")

        loader = SelectorLoader(selector_file)
        with pytest.raises(SelectorValidationError) as exc_info:
            loader.load()
        assert "Required selector(s) missing" in str(exc_info.value)
        assert "claude" in str(exc_info.value)

    def test_load_with_null_required_selector(self, tmp_path: Path) -> None:
        """Test load() with null value for required selector."""
        selector_file = tmp_path / "null_selector.yaml"
        config_data = {
            "version": "1.0.0",
            "providers": {
                "claude": {
                    "chat_input": "#input",
                    "send_button": None,  # Null value
                    "response_container": ".response",
                }
            },
        }
        selector_file.write_text(yaml.dump(config_data), encoding="utf-8")

        loader = SelectorLoader(selector_file)
        with pytest.raises(SelectorValidationError) as exc_info:
            loader.load()
        assert "missing for claude" in str(exc_info.value)

    def test_load_invalid_provider_type(self, tmp_path: Path) -> None:
        """Test load() with invalid provider definition type."""
        selector_file = tmp_path / "invalid_provider.yaml"
        config_data = {
            "version": "1.0.0",
            "validation": {
                "required_selectors": [],  # Override to skip validation
            },
            "providers": {
                "claude": "not_a_dict",  # Invalid: should be dict
            },
        }
        selector_file.write_text(yaml.dump(config_data), encoding="utf-8")

        loader = SelectorLoader(selector_file)
        with pytest.raises(SelectorValidationError) as exc_info:
            loader.load()
        # Pydantic v2 validation error comes first
        assert "Failed to parse selector configuration" in str(exc_info.value)

    def test_get_selector_existing(self, tmp_path: Path) -> None:
        """Test get_selector() with existing selector."""
        selector_file = tmp_path / "test.yaml"
        config_data = {
            "validation": {
                "required_selectors": ["chat_input"],  # Only require chat_input
            },
            "providers": {
                "claude": {
                    "chat_input": "#claude-input",
                    "send_button": "#claude-send",
                }
            },
        }
        selector_file.write_text(yaml.dump(config_data), encoding="utf-8")

        loader = SelectorLoader(selector_file)
        config = loader.load()

        selector = loader.get_selector(config, "claude", "chat_input")
        assert selector == "#claude-input"

    def test_get_selector_provider_not_found(self, tmp_path: Path) -> None:
        """Test get_selector() with non-existent provider."""
        selector_file = tmp_path / "test.yaml"
        config_data = {
            "validation": {
                "required_selectors": [],  # No required selectors
            },
            "providers": {"claude": {"chat_input": "#input"}},
        }
        selector_file.write_text(yaml.dump(config_data), encoding="utf-8")

        loader = SelectorLoader(selector_file)
        config = loader.load()

        with pytest.raises(SelectorValidationError) as exc_info:
            loader.get_selector(config, "gemini", "chat_input")
        assert "Provider not found: gemini" in str(exc_info.value)

    def test_get_selector_key_not_found_optional(self, tmp_path: Path) -> None:
        """Test get_selector() with missing key and optional=True."""
        selector_file = tmp_path / "test.yaml"
        config_data = {
            "validation": {
                "required_selectors": [],  # No required selectors
            },
            "providers": {"claude": {"chat_input": "#input"}},
        }
        selector_file.write_text(yaml.dump(config_data), encoding="utf-8")

        loader = SelectorLoader(selector_file)
        config = loader.load()

        result = loader.get_selector(config, "claude", "logout_button", optional=True)
        assert result is None

    def test_get_selector_key_not_found_required(self, tmp_path: Path) -> None:
        """Test get_selector() with missing key and optional=False."""
        selector_file = tmp_path / "test.yaml"
        config_data = {
            "validation": {
                "required_selectors": [],  # No required selectors
            },
            "providers": {"claude": {"chat_input": "#input"}},
        }
        selector_file.write_text(yaml.dump(config_data), encoding="utf-8")

        loader = SelectorLoader(selector_file)
        config = loader.load()

        with pytest.raises(SelectorValidationError) as exc_info:
            loader.get_selector(config, "claude", "logout_button", optional=False)
        assert "Selector key not found: logout_button" in str(exc_info.value)

    def test_get_selector_null_value_optional(self, tmp_path: Path) -> None:
        """Test get_selector() with null value and optional=True."""
        selector_file = tmp_path / "test.yaml"
        config_data = {
            "validation": {
                "required_selectors": [],  # No required selectors
            },
            "providers": {"claude": {"chat_input": "#input", "logout_button": None}},
        }
        selector_file.write_text(yaml.dump(config_data), encoding="utf-8")

        loader = SelectorLoader(selector_file)
        config = loader.load()

        result = loader.get_selector(config, "claude", "logout_button", optional=True)
        assert result is None

    def test_get_provider_selectors(self, tmp_path: Path) -> None:
        """Test get_provider_selectors()."""
        selector_file = tmp_path / "test.yaml"
        config_data = {
            "validation": {
                "required_selectors": [],  # No required selectors
            },
            "providers": {
                "claude": {
                    "chat_input": "#input",
                    "send_button": "#send",
                }
            },
        }
        selector_file.write_text(yaml.dump(config_data), encoding="utf-8")

        loader = SelectorLoader(selector_file)
        config = loader.load()

        selectors = loader.get_provider_selectors(config, "claude")
        assert selectors == {"chat_input": "#input", "send_button": "#send"}

    def test_get_provider_selectors_not_found(self, tmp_path: Path) -> None:
        """Test get_provider_selectors() with non-existent provider."""
        selector_file = tmp_path / "test.yaml"
        config_data = {
            "validation": {
                "required_selectors": [],  # No required selectors
            },
            "providers": {"claude": {"chat_input": "#input"}},
        }
        selector_file.write_text(yaml.dump(config_data), encoding="utf-8")

        loader = SelectorLoader(selector_file)
        config = loader.load()

        with pytest.raises(SelectorValidationError) as exc_info:
            loader.get_provider_selectors(config, "gemini")
        assert "Provider not found: gemini" in str(exc_info.value)

    def test_get_base_url(self, tmp_path: Path) -> None:
        """Test get_base_url()."""
        selector_file = tmp_path / "test.yaml"
        config_data = {
            "validation": {
                "required_selectors": [],  # No required selectors
            },
            "providers": {
                "claude": {
                    "base_url": "https://claude.ai",
                    "chat_input": "#input",
                }
            },
        }
        selector_file.write_text(yaml.dump(config_data), encoding="utf-8")

        loader = SelectorLoader(selector_file)
        config = loader.load()

        base_url = loader.get_base_url(config, "claude")
        assert base_url == "https://claude.ai"

    def test_get_base_url_missing(self, tmp_path: Path) -> None:
        """Test get_base_url() when not defined."""
        selector_file = tmp_path / "test.yaml"
        config_data = {
            "validation": {
                "required_selectors": [],  # No required selectors
            },
            "providers": {"claude": {"chat_input": "#input"}},
        }
        selector_file.write_text(yaml.dump(config_data), encoding="utf-8")

        loader = SelectorLoader(selector_file)
        config = loader.load()

        base_url = loader.get_base_url(config, "claude")
        assert base_url is None

    def test_reload(self, tmp_path: Path) -> None:
        """Test reload() method."""
        selector_file = tmp_path / "test.yaml"
        config_data = {
            "version": "1.0.0",
            "providers": {
                "claude": {
                    "chat_input": "#input-v1",
                    "send_button": "#send",
                    "response_container": ".response",
                }
            },
        }
        selector_file.write_text(yaml.dump(config_data), encoding="utf-8")

        loader = SelectorLoader(selector_file)
        config1 = loader.load()

        # Modify file
        config_data["providers"]["claude"]["chat_input"] = "#input-v2"
        selector_file.write_text(yaml.dump(config_data), encoding="utf-8")

        # Reload
        config2 = loader.reload()

        assert config1 is not config2  # Different objects
        assert loader.get_selector(config2, "claude", "chat_input") == "#input-v2"

    def test_config_property_cached(self, tmp_path: Path) -> None:
        """Test config property returns cached value."""
        selector_file = tmp_path / "test.yaml"
        config_data = {
            "providers": {
                "claude": {
                    "chat_input": "#input",
                    "send_button": "#send",
                    "response_container": ".response",
                }
            },
        }
        selector_file.write_text(yaml.dump(config_data), encoding="utf-8")

        loader = SelectorLoader(selector_file)
        assert loader.config is None

        config1 = loader.load()
        config2 = loader.config

        assert config1 is config2  # Same cached object

    def test_multiple_providers(self, tmp_path: Path) -> None:
        """Test loading selectors for multiple providers."""
        selector_file = tmp_path / "multi.yaml"
        config_data = {
            "version": "1.0.0",
            "providers": {
                "claude": {
                    "chat_input": "#claude-input",
                    "send_button": "#claude-send",
                    "response_container": ".claude-response",
                },
                "gemini": {
                    "chat_input": ".gemini-input",
                    "send_button": ".gemini-send",
                    "response_container": ".gemini-response",
                },
                "chatgpt": {
                    "chat_input": "#chatgpt-input",
                    "send_button": "#chatgpt-send",
                    "response_container": ".chatgpt-response",
                },
            },
        }
        selector_file.write_text(yaml.dump(config_data), encoding="utf-8")

        loader = SelectorLoader(selector_file)
        config = loader.load()

        assert len(config.providers) == 3
        assert "claude" in config.providers
        assert "gemini" in config.providers
        assert "chatgpt" in config.providers

    def test_selector_error_code(self, tmp_path: Path) -> None:
        """Test SelectorValidationError has correct error code."""
        selector_file = tmp_path / "test.yaml"
        loader = SelectorLoader(selector_file)

        try:
            loader.load()
        except SelectorValidationError as e:
            assert e.error_code == ErrorCode.CONFIG_VALIDATION_FAILED

    def test_default_validation_when_missing(self, tmp_path: Path) -> None:
        """Test default validation is used when validation section is missing."""
        selector_file = tmp_path / "no_validation.yaml"
        config_data = {
            "version": "1.0.0",
            "providers": {
                "claude": {
                    "chat_input": "#input",
                    "send_button": "#send",
                    "response_container": ".response",
                }
            },
        }
        selector_file.write_text(yaml.dump(config_data), encoding="utf-8")

        loader = SelectorLoader(selector_file)
        config = loader.load()

        # Should use default required selectors
        assert config.validation.required_selectors == loader.DEFAULT_REQUIRED_SELECTORS
