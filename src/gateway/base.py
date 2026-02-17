"""
Base provider for AI gateway.

Defines BaseProvider interface and common functionality for all AI providers.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from core.logger import get_logger
from core.models import AgentType
from gateway.selector_loader import SelectorConfig, SelectorLoader

logger = get_logger(__name__)


class GatewayRequest(BaseModel):
    """Request to send to AI provider."""

    task_name: str
    prompt: str
    max_tokens: int | None = None
    timeout: int = 120


class GatewayResponse(BaseModel):
    """Response from AI provider."""

    content: str
    success: bool
    error: str | None = None
    tokens_used: int = 0
    response_time: float = 0.0
    metadata: dict[str, Any] = {}


class BaseProvider(ABC):
    """
    Abstract base class for all AI providers.

    Each provider (ChatGPT, Claude, Gemini, Perplexity) inherits from this
    and implements the abstract methods.

    Attributes:
        agent_type: The AgentType enum value for this provider
        provider_name: String name of the provider (e.g., "claude", "gemini")
        profile_dir: Directory path for provider profile data
        headless: Whether to run browser in headless mode
        selector_loader: SelectorLoader instance for DOM selectors
    """

    agent_type: AgentType = None  # To be overridden by subclasses
    provider_name: str = None  # To be overridden by subclasses

    def __init__(
        self,
        profile_dir: Path,
        headless: bool = True,
        selector_loader: SelectorLoader | None = None,
        ignore_https_errors: bool = False,
    ) -> None:
        """
        Initialize provider with profile directory and headless mode.

        Args:
            profile_dir: Directory for provider profile data
            headless: Whether to run browser in headless mode
            selector_loader: Optional SelectorLoader for DOM selectors
            ignore_https_errors: Whether to ignore HTTPS errors (default: False for security)
        """
        self.profile_dir = profile_dir
        self.headless = headless
        self.ignore_https_errors = ignore_https_errors
        self._selector_loader = selector_loader
        self._selector_config: SelectorConfig | None = None
        self._browser_manager = None

    @property
    def selector_loader(self) -> SelectorLoader | None:
        """Get the selector loader instance."""
        return self._selector_loader

    @selector_loader.setter
    def selector_loader(self, loader: SelectorLoader) -> None:
        """
        Set the selector loader instance.

        Args:
            loader: SelectorLoader instance to use
        """
        self._selector_loader = loader
        self._selector_config = None  # Clear cached config

    def get_selector(
        self,
        key: str,
        optional: bool = False,
    ) -> str | None:
        """
        Get a DOM selector for this provider.

        Args:
            key: Selector key (e.g., "chat_input", "send_button")
            optional: If True, return None instead of raising for missing selectors

        Returns:
            CSS selector string, or None if not found and optional=True

        Raises:
            GatewayException: If selector_loader not set or selector not found
        """
        if self._selector_loader is None:
            # Backward compatibility: return None if no loader set
            return None

        if self.provider_name is None:
            raise ValueError("provider_name must be set by subclass")

        # Lazy load selector config
        if self._selector_config is None:
            self._selector_config = self._selector_loader.load()

        return self._selector_loader.get_selector(
            self._selector_config,
            self.provider_name,
            key,
            optional=optional,
        )

    def get_all_selectors(self) -> dict[str, str]:
        """
        Get all DOM selectors for this provider.

        Returns:
            Dictionary of selector key-value pairs

        Raises:
            GatewayException: If selector_loader not set or provider not found
        """
        if self._selector_loader is None:
            return {}

        if self.provider_name is None:
            raise ValueError("provider_name must be set by subclass")

        if self._selector_config is None:
            self._selector_config = self._selector_loader.load()

        return self._selector_loader.get_provider_selectors(
            self._selector_config,
            self.provider_name,
        )

    async def get_browser_manager(self):
        """
        Get or create browser manager using browser pool.

        Returns:
            ProviderContext wrapper from BrowserPool

        Note:
            This now uses BrowserPool for context reuse instead of
            creating separate browser instances. Falls back to legacy
            BrowserManager if pool is disabled via environment variable.
        """
        import os

        # Check if browser pool is enabled (default: true)
        use_pool = os.getenv("AIGENFLOW_USE_BROWSER_POOL", "true").lower() == "true"

        if self._browser_manager is None:
            if use_pool:
                # Use new BrowserPool approach
                from gateway.provider_context import ProviderContext

                self._browser_manager = ProviderContext(
                    provider_name=self.provider_name,
                    headless=self.headless,
                )
                logger.info(f"Using BrowserPool for {self.provider_name}")
            else:
                # Legacy approach: create separate browser manager
                from gateway.browser_manager import BrowserManager

                self._browser_manager = BrowserManager(
                    headless=self.headless,
                    ignore_https_errors=self.ignore_https_errors,
                )
                logger.info(f"Using legacy BrowserManager for {self.provider_name}")

        return self._browser_manager

    def get_base_url(self) -> str | None:
        """
        Get the base URL for this provider.

        Returns:
            Base URL string, or None if not configured
        """
        return self.get_selector("base_url", optional=True)

    @abstractmethod
    async def send_message(self, request: GatewayRequest) -> GatewayResponse:
        """
        Send a message to the AI provider.

        Args:
            request: GatewayRequest with task_name and prompt

        Returns:
            GatewayResponse with content and metadata
        """
        raise NotImplementedError

    @abstractmethod
    async def check_session(self) -> bool:
        """
        Check if current session is valid (logged in).

        Returns:
            True if session is valid, False otherwise
        """
        raise NotImplementedError

    @abstractmethod
    async def login_flow(self) -> None:
        """
        Execute login flow if session is invalid.

        Should:
        1. Check if session exists
        2. If expired/missing, run login flow
        3. Save session state
        """
        raise NotImplementedError

    @abstractmethod
    def save_session(self) -> None:
        """
        Save current session state to disk.

        Sessions are persisted to allow resume functionality.
        """
        raise NotImplementedError

    @abstractmethod
    def load_session(self) -> bool:
        """
        Load session state from disk if available.

        Returns:
            True if session was loaded, False otherwise
        """
        raise NotImplementedError

    def get_profile_path(self) -> Path:
        """Get path to provider profile directory."""
        return self.profile_dir
