"""
Tests for logging profile configuration.

Tests cover environment-specific profiles, custom profile creation,
and profile-based logging setup.
"""

import logging
import sys
from pathlib import Path

import pytest
import structlog

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from config.logging_profiles import (
    LogEnvironment,
    LoggingProfile,
    get_logging_profile,
    parse_log_level,
)


class TestLogEnvironment:
    """Test LogEnvironment enum functionality."""

    def test_log_environment_values(self):
        """LogEnvironment enum has correct string values."""
        assert LogEnvironment.DEVELOPMENT.value == "development"
        assert LogEnvironment.TESTING.value == "testing"
        assert LogEnvironment.PRODUCTION.value == "production"


class TestLoggingProfile:
    """Test LoggingProfile dataclass."""

    def test_logging_profile_creation(self):
        """LoggingProfile can be instantiated."""
        profile = LoggingProfile(
            log_level=logging.INFO,
            console_enabled=True,
            file_enabled=True,
            json_output=True,
            log_file=Path("test.log"),
        )
        assert profile.log_level == logging.INFO
        assert profile.should_log_to_console() is True
        assert profile.should_log_to_file() is True
        assert profile.use_json is True

    def test_logging_profile_properties(self):
        """LoggingProfile properties return correct values."""
        profile = LoggingProfile(
            log_level=logging.WARNING,
            console_enabled=False,
            file_enabled=True,
            json_output=False,
            log_file=Path("test.log"),
            max_file_size_mb=10,
            backup_count=5,
        )
        assert profile.log_level == logging.WARNING
        assert profile.should_log_to_console() is False
        assert profile.should_log_to_file() is True
        assert profile.use_json is False
        assert profile.max_file_size_mb == 10
        assert profile.backup_count == 5


class TestPredefinedProfiles:
    """Test predefined logging profiles."""

    def test_development_profile(self):
        """Development profile has DEBUG level and both outputs."""
        profile = get_logging_profile(LogEnvironment.DEVELOPMENT)
        assert profile.log_level == logging.DEBUG
        assert profile.should_log_to_console() is True
        assert profile.should_log_to_file() is True
        assert profile.use_json is False

    def test_testing_profile(self):
        """Testing profile has INFO level and file-only output."""
        profile = get_logging_profile(LogEnvironment.TESTING)
        assert profile.log_level == logging.INFO
        assert profile.should_log_to_console() is False
        assert profile.should_log_to_file() is True
        assert profile.use_json is False

    def test_production_profile(self):
        """Production profile has WARNING level and file-only output."""
        profile = get_logging_profile(LogEnvironment.PRODUCTION)
        assert profile.log_level == logging.WARNING
        assert profile.should_log_to_console() is False
        assert profile.should_log_to_file() is True
        assert profile.use_json is True


class TestParseLogLevel:
    """Test log level parsing."""

    def test_parse_log_level_valid(self):
        """parse_log_level accepts valid levels."""
        assert parse_log_level("debug") == logging.DEBUG
        assert parse_log_level("info") == logging.INFO
        assert parse_log_level("warning") == logging.WARNING
        assert parse_log_level("error") == logging.ERROR
        assert parse_log_level("critical") == logging.CRITICAL

    def test_parse_log_level_invalid(self):
        """parse_log_level rejects invalid levels."""
        with pytest.raises(ValueError):
            parse_log_level("invalid")

    def test_parse_log_level_case_insensitive(self):
        """parse_log_level is case-insensitive."""
        assert parse_log_level("DEBUG") == logging.DEBUG
        assert parse_log_level("Info") == logging.INFO
        assert parse_log_level("WARNING") == logging.WARNING
