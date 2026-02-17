"""
Comprehensive coverage tests for gateway session management.

Tests focus on edge cases, error handling, and exception paths to achieve 85%+ coverage.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from src.gateway.base import BaseProvider
from src.gateway.session import SessionInfo, SessionManager


class MockProvider(BaseProvider):
    """Mock provider for testing."""

    agent_type = "mock"
    provider_name = "mock_provider"

    def __init__(
        self,
        profile_dir: Path,
        headless: bool = True,
        selector_loader=None,
        should_fail: bool = False,
        is_logged_in_value: bool = True,
    ):
        super().__init__(profile_dir, headless, selector_loader)
        self.should_fail = should_fail
        self.is_logged_in_value = is_logged_in_value
        self.login_called = False
        self.save_called = False
        self.load_called = False

    async def send_message(self, request):
        """Mock send message."""
        from src.gateway.base import GatewayResponse
        return GatewayResponse(content="mock", success=True)

    async def check_session(self) -> bool:
        """Mock check session."""
        if self.should_fail:
            raise RuntimeError("Session check failed")
        return self.is_logged_in_value

    async def login_flow(self) -> None:
        """Mock login flow."""
        if self.should_fail:
            raise RuntimeError("Login flow failed")
        self.login_called = True
        self.is_logged_in_value = True

    def save_session(self) -> None:
        """Mock save session."""
        if self.should_fail:
            raise RuntimeError("Save session failed")
        self.save_called = True

    def load_session(self) -> bool:
        """Mock load session."""
        if self.should_fail:
            raise RuntimeError("Load session failed")
        self.load_called = True
        return True


class TestSessionManagerCoverage:
    """
    Comprehensive tests for SessionManager to achieve 85%+ coverage.

    Focus areas:
    - Exception handling paths (lines 74-76, 88-89, 93-97, 101-105, 125-127)
    - Error logging (line 54)
    - Edge cases and boundary conditions
    - Session lifecycle management
    """

    @pytest.mark.anyio
    async def test_log_provider_error(self):
        """Test _log_provider_error method (line 54)."""
        manager = SessionManager()

        # Create mock provider
        provider = MockProvider(profile_dir=Path("/tmp/test"))

        # Test error logging
        with patch("src.gateway.session.logger") as mock_logger:
            manager._log_provider_error(
                "test_operation",
                "test_provider",
                RuntimeError("Test error message")
            )

            # Verify logger.warning was called with correct parameters
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args

            assert call_args[1]["operation"] == "test_operation"
            assert call_args[1]["provider"] == "test_provider"
            assert call_args[1]["error_type"] == "RuntimeError"
            # Error message should be present (redaction happens in logger)
            assert "error" in call_args[1]

    @pytest.mark.anyio
    async def test_check_all_sessions_with_exceptions(self):
        """Test check_all_sessions handles exceptions (lines 74-76)."""
        manager = SessionManager()

        # Register providers that will fail
        failing_provider = MockProvider(
            profile_dir=Path("/tmp/test1"),
            should_fail=True
        )
        valid_provider = MockProvider(
            profile_dir=Path("/tmp/test2"),
            is_logged_in_value=True
        )

        manager.register("failing", failing_provider)
        manager.register("valid", valid_provider)

        # Mock logger to capture error logging
        with patch("src.gateway.session.logger") as mock_logger:
            results = await manager.check_all_sessions()

            # Failing provider should return False
            assert results["failing"] is False
            # Valid provider should return True
            assert results["valid"] is True

            # Verify error was logged for failing provider
            assert mock_logger.warning.called

    @pytest.mark.anyio
    async def test_check_all_sessions_all_providers_fail(self):
        """Test check_all_sessions when all providers fail."""
        manager = SessionManager()

        # Register multiple failing providers
        for i in range(3):
            provider = MockProvider(
                profile_dir=Path(f"/tmp/test{i}"),
                should_fail=True
            )
            manager.register(f"provider_{i}", provider)

        with patch("src.gateway.session.logger") as mock_logger:
            results = await manager.check_all_sessions()

            # All should be False
            assert all(result is False for result in results.values())
            # Errors should be logged for each
            assert mock_logger.warning.call_count == 3

    @pytest.mark.anyio
    async def test_login_all_expired_with_exceptions(self):
        """Test login_all_expired handles exceptions (lines 88-89)."""
        manager = SessionManager()

        # Register providers with different states
        failing_provider = MockProvider(
            profile_dir=Path("/tmp/test1"),
            should_fail=True,
            is_logged_in_value=False
        )
        expired_provider = MockProvider(
            profile_dir=Path("/tmp/test2"),
            is_logged_in_value=False
        )
        valid_provider = MockProvider(
            profile_dir=Path("/tmp/test3"),
            is_logged_in_value=True
        )

        manager.register("failing", failing_provider)
        manager.register("expired", expired_provider)
        manager.register("valid", valid_provider)

        with patch("src.gateway.session.logger") as mock_logger:
            await manager.login_all_expired()

            # Valid provider should not call login
            assert not valid_provider.login_called

            # Expired provider should call login
            assert expired_provider.login_called

            # Failing provider should have error logged
            assert mock_logger.warning.called

    @pytest.mark.anyio
    async def test_login_all_expired_all_fail(self):
        """Test login_all_expired when all providers fail."""
        manager = SessionManager()

        # Register multiple failing providers
        for i in range(3):
            provider = MockProvider(
                profile_dir=Path(f"/tmp/test{i}"),
                should_fail=True,
                is_logged_in_value=False
            )
            manager.register(f"provider_{i}", provider)

        with patch("src.gateway.session.logger") as mock_logger:
            await manager.login_all_expired()

            # Errors should be logged for each
            assert mock_logger.warning.call_count == 3

    @pytest.mark.anyio
    async def test_save_all_sessions_with_exceptions(self):
        """Test save_all_sessions handles exceptions (lines 93-97)."""
        manager = SessionManager()

        # Register providers with different states
        failing_provider = MockProvider(
            profile_dir=Path("/tmp/test1"),
            should_fail=True
        )
        valid_provider = MockProvider(
            profile_dir=Path("/tmp/test2")
        )

        manager.register("failing", failing_provider)
        manager.register("valid", valid_provider)

        with patch("src.gateway.session.logger") as mock_logger:
            await manager.save_all_sessions()

            # Valid provider should have save called
            assert valid_provider.save_called

            # Failing provider should have error logged
            assert mock_logger.warning.called

    @pytest.mark.anyio
    async def test_save_all_sessions_all_fail(self):
        """Test save_all_sessions when all providers fail."""
        manager = SessionManager()

        # Register multiple failing providers
        for i in range(3):
            provider = MockProvider(
                profile_dir=Path(f"/tmp/test{i}"),
                should_fail=True
            )
            manager.register(f"provider_{i}", provider)

        with patch("src.gateway.session.logger") as mock_logger:
            await manager.save_all_sessions()

            # Errors should be logged for each
            assert mock_logger.warning.call_count == 3

    @pytest.mark.anyio
    async def test_load_all_sessions_with_exceptions(self):
        """Test load_all_sessions handles exceptions (lines 101-105)."""
        manager = SessionManager()

        # Register providers with different states
        failing_provider = MockProvider(
            profile_dir=Path("/tmp/test1"),
            should_fail=True
        )
        valid_provider = MockProvider(
            profile_dir=Path("/tmp/test2")
        )

        manager.register("failing", failing_provider)
        manager.register("valid", valid_provider)

        with patch("src.gateway.session.logger") as mock_logger:
            manager.load_all_sessions()

            # Valid provider should have load called
            assert valid_provider.load_called

            # Failing provider should have error logged
            assert mock_logger.warning.called

    @pytest.mark.anyio
    async def test_load_all_sessions_all_fail(self):
        """Test load_all_sessions when all providers fail."""
        manager = SessionManager()

        # Register multiple failing providers
        for i in range(3):
            provider = MockProvider(
                profile_dir=Path(f"/tmp/test{i}"),
                should_fail=True
            )
            manager.register(f"provider_{i}", provider)

        with patch("src.gateway.session.logger") as mock_logger:
            manager.load_all_sessions()

            # Errors should be logged for each
            assert mock_logger.warning.call_count == 3

    @pytest.mark.anyio
    async def test_get_valid_session_with_check_exception(self):
        """Test get_valid_session handles check_session exceptions (lines 125-127)."""
        manager = SessionManager()

        # Register providers with different states
        failing_provider = MockProvider(
            profile_dir=Path("/tmp/test1"),
            should_fail=True
        )
        valid_provider = MockProvider(
            profile_dir=Path("/tmp/test2"),
            is_logged_in_value=True
        )

        manager.register("failing", failing_provider)
        manager.register("valid", valid_provider)

        with patch("src.gateway.session.logger") as mock_logger:
            # Test with preferred order that tries failing provider first
            result = await manager.get_valid_session(
                preferred_order=["failing", "valid"]
            )

            # Should return valid provider after failing provider throws exception
            assert result == valid_provider

            # Error should be logged for failing provider
            assert mock_logger.warning.called

    @pytest.mark.anyio
    async def test_get_valid_session_all_fail(self):
        """Test get_valid_session when all providers fail (line 130)."""
        manager = SessionManager()

        # Register only failing providers
        failing_provider = MockProvider(
            profile_dir=Path("/tmp/test1"),
            should_fail=True
        )
        invalid_provider = MockProvider(
            profile_dir=Path("/tmp/test2"),
            is_logged_in_value=False
        )

        manager.register("failing", failing_provider)
        manager.register("invalid", invalid_provider)

        with patch("src.gateway.session.logger"):
            # Should return None when no valid session found
            result = await manager.get_valid_session()
            assert result is None

    @pytest.mark.anyio
    async def test_get_valid_session_with_invalid_sessions(self):
        """Test get_valid_session when all sessions are invalid."""
        manager = SessionManager()

        # Register providers with invalid sessions
        provider1 = MockProvider(
            profile_dir=Path("/tmp/test1"),
            is_logged_in_value=False
        )
        provider2 = MockProvider(
            profile_dir=Path("/tmp/test2"),
            is_logged_in_value=False
        )

        manager.register("provider1", provider1)
        manager.register("provider2", provider2)

        # Should return None when all sessions are invalid
        result = await manager.get_valid_session()
        assert result is None

    @pytest.mark.anyio
    async def test_get_valid_session_empty_preferred_order(self):
        """Test get_valid_session with empty preferred order."""
        manager = SessionManager()

        provider = MockProvider(
            profile_dir=Path("/tmp/test"),
            is_logged_in_value=True
        )
        manager.register("test", provider)

        # Empty preferred order should not return any provider
        result = await manager.get_valid_session(preferred_order=[])
        assert result is None

    @pytest.mark.anyio
    async def test_get_valid_session_nonexistent_provider_in_order(self):
        """Test get_valid_session with non-existent provider in preferred order."""
        manager = SessionManager()

        provider = MockProvider(
            profile_dir=Path("/tmp/test"),
            is_logged_in_value=True
        )
        manager.register("existing", provider)

        # Preferred order includes non-existent provider
        result = await manager.get_valid_session(
            preferred_order=["nonexistent", "existing"]
        )

        # Should skip non-existent and return existing
        assert result == provider

    @pytest.mark.anyio
    async def test_get_valid_session_no_preferred_order(self):
        """Test get_valid_session without preferred order uses all providers."""
        manager = SessionManager()

        provider1 = MockProvider(
            profile_dir=Path("/tmp/test1"),
            is_logged_in_value=False
        )
        provider2 = MockProvider(
            profile_dir=Path("/tmp/test2"),
            is_logged_in_value=True
        )

        manager.register("provider1", provider1)
        manager.register("provider2", provider2)

        # Without preferred order, should check all providers
        result = await manager.get_valid_session()

        # Should return first valid provider (provider2)
        assert result == provider2

    @pytest.mark.anyio
    async def test_get_valid_session_first_valid(self):
        """Test get_valid_session returns first valid in preferred order."""
        manager = SessionManager()

        provider1 = MockProvider(
            profile_dir=Path("/tmp/test1"),
            is_logged_in_value=True
        )
        provider2 = MockProvider(
            profile_dir=Path("/tmp/test2"),
            is_logged_in_value=True
        )

        manager.register("provider1", provider1)
        manager.register("provider2", provider2)

        # With preferred order, should respect it
        result = await manager.get_valid_session(
            preferred_order=["provider2", "provider1"]
        )

        # Should return provider2 even though provider1 is also valid
        assert result == provider2

    def test_register_provider_alias(self):
        """Test register method is alias for register_provider."""
        manager = SessionManager()
        provider = MockProvider(profile_dir=Path("/tmp/test"))

        # Use register (alias)
        manager.register("test", provider)

        # Should be in providers dict
        assert "test" in manager.providers
        assert manager.providers["test"] == provider

    def test_init_with_settings(self):
        """Test SessionManager initialization with settings."""
        mock_settings = {"test": "value"}
        manager = SessionManager(settings=mock_settings)

        assert manager.settings == mock_settings
        assert manager.providers == {}
        assert manager.sessions == {}

    def test_init_without_settings(self):
        """Test SessionManager initialization without settings."""
        manager = SessionManager()

        assert manager.settings is None
        assert manager.providers == {}
        assert manager.sessions == {}

    def test_register_multiple_providers(self):
        """Test registering multiple providers."""
        manager = SessionManager()

        provider1 = MockProvider(profile_dir=Path("/tmp/test1"))
        provider2 = MockProvider(profile_dir=Path("/tmp/test2"))
        provider3 = MockProvider(profile_dir=Path("/tmp/test3"))

        manager.register("provider1", provider1)
        manager.register("provider2", provider2)
        manager.register("provider3", provider3)

        assert len(manager.providers) == 3
        assert manager.providers["provider1"] == provider1
        assert manager.providers["provider2"] == provider2
        assert manager.providers["provider3"] == provider3

    @pytest.mark.anyio
    async def test_check_all_sessions_empty_manager(self):
        """Test check_all_sessions with no registered providers."""
        manager = SessionManager()

        results = await manager.check_all_sessions()

        assert results == {}

    @pytest.mark.anyio
    async def test_login_all_expired_empty_manager(self):
        """Test login_all_expired with no registered providers."""
        manager = SessionManager()

        # Should not raise any exception
        await manager.login_all_expired()

    @pytest.mark.anyio
    async def test_save_all_sessions_empty_manager(self):
        """Test save_all_sessions with no registered providers."""
        manager = SessionManager()

        # Should not raise any exception
        await manager.save_all_sessions()

    def test_load_all_sessions_empty_manager(self):
        """Test load_all_sessions with no registered providers."""
        manager = SessionManager()

        # Should not raise any exception
        manager.load_all_sessions()

    @pytest.mark.anyio
    async def test_get_valid_session_empty_manager(self):
        """Test get_valid_session with no registered providers."""
        manager = SessionManager()

        result = await manager.get_valid_session()

        assert result is None


class TestSessionInfo:
    """Tests for SessionInfo model."""

    def test_session_info_creation(self):
        """Test SessionInfo model creation."""
        info = SessionInfo(
            provider_name="test_provider",
            is_logged_in=True,
            last_validated=1234567890.0,
            cookies_file=Path("/tmp/cookies.json"),
            profile_dir=Path("/tmp/profile")
        )

        assert info.provider_name == "test_provider"
        assert info.is_logged_in is True
        assert info.last_validated == 1234567890.0
        assert info.cookies_file == Path("/tmp/cookies.json")
        assert info.profile_dir == Path("/tmp/profile")

    def test_session_info_defaults(self):
        """Test SessionInfo model default values."""
        info = SessionInfo(
            provider_name="test_provider",
            cookies_file=Path("/tmp/cookies.json"),
            profile_dir=Path("/tmp/profile")
        )

        # Check defaults
        assert info.is_logged_in is False
        assert info.last_validated == 0.0

    def test_session_info_model_validation(self):
        """Test SessionInfo validates required fields."""
        # Missing required fields should raise ValidationError
        with pytest.raises(Exception):
            SessionInfo(
                provider_name="test"
                # Missing cookies_file and profile_dir
            )
