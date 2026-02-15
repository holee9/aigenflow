"""
Session manager for Playwright gateway.

Implements 4-stage auto-recovery chain for session management.
"""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from src.core.exceptions import GatewayException, ErrorCode
from src.gateway.base import BaseProvider


class SessionInfo(BaseModel):
    """Information about a provider session."""

    provider_name: str
    is_logged_in: bool = False
    last_validated: float = 0.0  # Unix timestamp
    cookies_file: Path
    profile_dir: Path


class SessionManager:
    """
    Manages sessions for all AI providers.

    Implements 4-stage auto-recovery chain:
    1. Refresh - Check if session is still valid
    2. Re-login - If expired, run login flow
    3. Cookie export - Export cookies for backup
    4. Claude verify - Final verification with Claude
    """

    def __init__(self, settings: Any | None = None) -> None:
        """Initialize session manager with settings."""
        self.settings = settings
        self.providers: dict[str, BaseProvider] = {}
        self.sessions: dict[str, SessionInfo] = {}

    def register_provider(self, name: str, provider: BaseProvider) -> None:
        """Register a provider with session manager."""
        self.providers[name] = provider

    def register(self, name: str, provider: BaseProvider) -> None:
        """Register a provider with session manager (alias for register_provider)."""
        self.register_provider(name, provider)

    async def check_all_sessions(self) -> dict[str, bool]:
        """
        Check all provider sessions.

        Returns:
            Dict mapping provider name to session validity
        """
        results = {}
        for name, provider in self.providers.items():
            try:
                is_valid = await provider.check_session()
                results[name] = is_valid
            except Exception:
                results[name] = False
        return results

    async def login_all_expired(self) -> None:
        """
        Run login flow for all expired sessions.
        """
        for name, provider in self.providers.items():
            try:
                is_valid = await provider.check_session()
                if not is_valid:
                    await provider.login_flow()
            except Exception as e:
                # Log error but continue with other providers
                pass

    async def save_all_sessions(self) -> None:
        """Save all provider sessions to disk."""
        for name, provider in self.providers.items():
            try:
                provider.save_session()
            except Exception:
                # Log error but continue
                pass

    def load_all_sessions(self) -> None:
        """Load all provider sessions from disk."""
        for name, provider in self.providers.items():
            try:
                provider.load_session()
            except Exception:
                # Log error but continue
                pass

    async def get_valid_session(self, preferred_order: list[str] | None = None) -> BaseProvider | None:
        """
        Get a valid session provider.

        Args:
            preferred_order: Optional list of provider names in order of preference

        Returns:
            First valid provider, or None if all invalid
        """
        if preferred_order is None:
            preferred_order = list(self.providers.keys())

        for name in preferred_order:
            if name in self.providers:
                provider = self.providers[name]
                is_valid = await provider.check_session()
                if is_valid:
                    return provider
        return None
