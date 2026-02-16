"""
Selector loader for externalized DOM selectors.

Loads and validates CSS selectors from YAML configuration file.
Provides type-safe access to provider-specific selectors.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator

from core.exceptions import ConfigurationException, ErrorCode


class SelectorValidationError(ConfigurationException):
    """Raised when selector validation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(f"Selector validation failed: {message}", details)
        self.error_code = ErrorCode.CONFIG_VALIDATION_FAILED


class SelectorValidation(BaseModel):
    """Validation rules for selector configuration."""

    required_selectors: list[str] = Field(
        default_factory=lambda: ["chat_input", "send_button", "response_container"]
    )
    optional_selectors: list[str] = Field(
        default_factory=lambda: ["login_button", "logout_button", "new_chat_button", "username_indicator"]
    )


class ProviderSelectors(BaseModel):
    """Selector definitions for a single provider."""

    base_url: str | None = None
    login_button: str | None = None
    chat_input: str | None = None
    send_button: str | None = None
    response_container: str | None = None
    logout_button: str | None = None
    new_chat_button: str | None = None
    username_indicator: str | None = None

    def get(self, key: str, default: Any = None) -> Any:
        """Get selector value by key, with default fallback."""
        return getattr(self, key, default)


class SelectorConfig(BaseModel):
    """Complete selector configuration from YAML file."""

    providers: dict[str, dict[str, Any]]
    version: str = "1.0.0"
    validation: SelectorValidation = Field(default_factory=SelectorValidation)
    last_updated: str | None = None

    @field_validator("providers", mode="before")
    @classmethod
    def validate_providers(cls, value: Any) -> dict[str, Any]:
        """Ensure providers is a dictionary."""
        if not isinstance(value, dict):
            raise ValueError("providers must be a dictionary")
        return value


class SelectorLoader:
    """
    Loads and validates DOM selectors from YAML configuration.

    Usage:
        loader = SelectorLoader("path/to/selectors.yaml")
        config = loader.load()
        chat_input = loader.get_selector(config, "claude", "chat_input")
    """

    DEFAULT_REQUIRED_SELECTORS = ["chat_input", "send_button", "response_container"]

    def __init__(self, selector_path: Path) -> None:
        """
        Initialize selector loader.

        Args:
            selector_path: Path to selectors.yaml file
        """
        self.selector_path = selector_path
        self._config: SelectorConfig | None = None

    def load(self) -> SelectorConfig:
        """
        Load selectors from YAML file.

        Returns:
            SelectorConfig with parsed and validated selectors

        Raises:
            SelectorValidationError: If file not found, invalid YAML, or validation fails
        """
        if not self.selector_path.exists():
            raise SelectorValidationError(
                f"Selector file not found: {self.selector_path}",
                {"path": str(self.selector_path)},
            )

        try:
            with open(self.selector_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            raise SelectorValidationError(
                f"Invalid YAML syntax: {exc}",
                {"path": str(self.selector_path), "error": str(exc)},
            ) from exc

        if not data or not isinstance(data, dict):
            raise SelectorValidationError(
                "Empty or invalid selector configuration",
                {"path": str(self.selector_path)},
            )

        # Build config with defaults
        validation_data = data.get("validation", {})
        if not validation_data:
            validation_data = {"required_selectors": self.DEFAULT_REQUIRED_SELECTORS}

        try:
            config = SelectorConfig(
                providers=data.get("providers", {}),
                version=data.get("version", "1.0.0"),
                validation=SelectorValidation(**validation_data),
                last_updated=data.get("last_updated"),
            )
        except Exception as exc:
            raise SelectorValidationError(
                f"Failed to parse selector configuration: {exc}",
                {"error": str(exc)},
            ) from exc

        # Validate all providers have required selectors
        self._validate_required_selectors(config)

        self._config = config
        return config

    def _validate_required_selectors(self, config: SelectorConfig) -> None:
        """
        Validate that all providers have required selectors.

        Args:
            config: SelectorConfig to validate

        Raises:
            SelectorValidationError: If any provider is missing required selectors
        """
        required = config.validation.required_selectors

        for provider_name, provider_selectors in config.providers.items():
            if not isinstance(provider_selectors, dict):
                raise SelectorValidationError(
                    f"Invalid selector definition for provider: {provider_name}",
                    {"provider": provider_name},
                )

            missing = [key for key in required if key not in provider_selectors or not provider_selectors[key]]

            if missing:
                raise SelectorValidationError(
                    f"Required selector(s) missing for {provider_name}: {', '.join(missing)}",
                    {"provider": provider_name, "missing": missing},
                )

    def get_selector(
        self,
        config: SelectorConfig,
        provider: str,
        key: str,
        optional: bool = False,
    ) -> str | None:
        """
        Get a specific selector value.

        Args:
            config: Loaded selector configuration
            provider: Provider name (claude, gemini, chatgpt, perplexity)
            key: Selector key (chat_input, send_button, etc.)
            optional: If True, return None for missing selectors instead of raising

        Returns:
            Selector string, or None if optional=True and selector not found

        Raises:
            SelectorValidationError: If provider or selector key not found
        """
        if provider not in config.providers:
            raise SelectorValidationError(
                f"Provider not found: {provider}",
                {"available": list(config.providers.keys())},
            )

        provider_selectors = config.providers[provider]

        if key not in provider_selectors:
            if optional:
                return None
            raise SelectorValidationError(
                f"Selector key not found: {key}",
                {"provider": provider, "key": key, "available": list(provider_selectors.keys())},
            )

        value = provider_selectors[key]
        if value is None:
            if optional:
                return None
            raise SelectorValidationError(
                f"Selector key '{key}' has null value for provider {provider}",
                {"provider": provider, "key": key},
            )

        return str(value)

    def get_provider_selectors(self, config: SelectorConfig, provider: str) -> dict[str, str]:
        """
        Get all selectors for a specific provider.

        Args:
            config: Loaded selector configuration
            provider: Provider name

        Returns:
            Dictionary of all selector key-value pairs for the provider

        Raises:
            SelectorValidationError: If provider not found
        """
        if provider not in config.providers:
            raise SelectorValidationError(
                f"Provider not found: {provider}",
                {"available": list(config.providers.keys())},
            )

        return config.providers[provider].copy()

    def get_base_url(self, config: SelectorConfig, provider: str) -> str | None:
        """
        Get base URL for a provider.

        Args:
            config: Loaded selector configuration
            provider: Provider name

        Returns:
            Base URL string, or None if not defined
        """
        return self.get_selector(config, provider, "base_url", optional=True)

    def reload(self) -> SelectorConfig:
        """
        Reload selector configuration from file.

        Clears cached configuration and reloads from disk.

        Returns:
            Newly loaded SelectorConfig
        """
        self._config = None
        return self.load()

    @property
    def config(self) -> SelectorConfig | None:
        """Get cached configuration, if loaded."""
        return self._config
