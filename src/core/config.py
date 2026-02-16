"""
Configuration management for AigenFlow pipeline.
"""

from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AigenFlowSettings(BaseSettings):
    """Application settings for AigenFlow."""

    app_name: str = "aigenflow"
    debug: bool = False
    log_level: str = "INFO"
    log_format: Literal["json", "pretty"] = "pretty"

    output_dir: Path = Field(default_factory=lambda: Path("output"))
    profiles_dir: Path = Field(default_factory=lambda: Path("~/.aigenflow/profiles").expanduser())
    templates_dir: Path = Field(default_factory=lambda: Path("templates"))

    max_retries: int = 2
    timeout_seconds: int = 120
    enable_auto_save: bool = True

    gateway_timeout: int = 120
    gateway_headless: bool = True
    gateway_user_data_dir: Path | None = None

    enable_parallel_phases: bool = True
    enable_event_tracking: bool = True
    enable_summarization: bool = True
    summarization_threshold: float = 0.8

    # API/session secrets from environment variables
    openai_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENAI_API_KEY", "AC_OPENAI_API_KEY"),
    )
    gemini_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GEMINI_API_KEY", "AC_GEMINI_API_KEY"),
    )
    perplexity_session_token: str | None = Field(
        default=None,
        validation_alias=AliasChoices("PERPLEXITY_SESSION_TOKEN", "AC_PERPLEXITY_SESSION_TOKEN"),
    )
    perplexity_csrf_token: str | None = Field(
        default=None,
        validation_alias=AliasChoices("PERPLEXITY_CSRF_TOKEN", "AC_PERPLEXITY_CSRF_TOKEN"),
    )

    @field_validator("output_dir", "profiles_dir", "templates_dir")
    @classmethod
    def create_directories(cls, v: Path) -> Path:
        v.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, v: str) -> str:
        return v.upper()

    model_config = SettingsConfigDict(
        extra="ignore",
        env_prefix="AC_",
        env_file=".env",
        env_nested_delimiter="__",
        case_sensitive=False,
    )


def get_settings() -> AigenFlowSettings:
    """Get application settings instance."""
    return AigenFlowSettings()


def get_output_dir(session_id: str, settings: AigenFlowSettings | None = None) -> Path:
    """Get output directory for a specific session."""
    if settings is None:
        settings = get_settings()

    output_path = settings.output_dir / session_id
    output_path.mkdir(parents=True, exist_ok=True)

    for i in range(1, 6):
        phase_dir = output_path / f"phase{i}"
        phase_dir.mkdir(exist_ok=True)

    final_dir = output_path / "final"
    final_dir.mkdir(exist_ok=True)

    return output_path
