"""
Browser Manager for Playwright automation.

Manages browser lifecycle with anti-detection measures for AI provider authentication.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from core.models import AgentType
from gateway.selector_loader import SelectorLoader


class BrowserManager:
    """
    Manages Playwright browser instance with anti-detection configuration.

    Provides:
    - Async browser lifecycle management
    - Anti-detection parameters
    - Headed/headless mode switching
    - Resource cleanup
    """

    # Default anti-detection browser arguments
    DEFAULT_BROWSER_ARGS = [
        "--disable-blink-features=AutomationControlled",
        "--disable-infobars",
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-web-security",
        "--disable-features=IsolateOrigins,site-per-process",
    ]

    # Default user agent for Windows Chrome
    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    )

    def __init__(
        self,
        headless: bool = True,
        user_data_dir: Path | None = None,
        user_agent: str | None = None,
        ignore_https_errors: bool = False,
    ) -> None:
        """
        Initialize browser manager.

        Args:
            headless: Whether to run browser in headless mode
            user_data_dir: Optional persistent user data directory for browser
            user_agent: Custom user agent string (uses default if None)
            ignore_https_errors: Whether to ignore HTTPS errors (default: False for security)
        """
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT
        self.ignore_https_errors = ignore_https_errors

        # Browser and context references
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._playwright = None

    async def start_browser(self) -> Browser:
        """
        Start Playwright browser instance.

        Returns:
            Browser instance

        Raises:
            RuntimeError: If browser fails to start
        """
        if self._browser is not None:
            return self._browser

        try:
            self._playwright = await async_playwright().start()

            # Launch browser with anti-detection settings
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless,
                args=self.DEFAULT_BROWSER_ARGS,
            )

            return self._browser

        except Exception as exc:
            raise RuntimeError(f"Failed to start browser: {exc}") from exc

    async def create_context(
        self,
        viewport: dict[str, int] | None = None,
        locale: str = "en-US",
    ) -> BrowserContext:
        """
        Create browser context with anti-detection settings.

        Args:
            viewport: Viewport dimensions (default: 1280x720)
            locale: Browser locale (default: en-US)

        Returns:
            BrowserContext instance

        Raises:
            RuntimeError: If context creation fails
        """
        if self._browser is None:
            await self.start_browser()

        viewport_config = viewport or {"width": 1280, "height": 720}

        try:
            # Create context with anti-detection settings
            self._context = await self._browser.new_context(
                viewport=viewport_config,
                user_agent=self.user_agent,
                locale=locale,
                ignore_https_errors=self.ignore_https_errors,
            )

            return self._context

        except Exception as exc:
            raise RuntimeError(f"Failed to create browser context: {exc}") from exc

    async def get_page(self) -> Page:
        """
        Get or create a page in the current context.

        Returns:
            Page instance

        Raises:
            RuntimeError: If no context exists
        """
        if self._context is None:
            self._context = await self.create_context()

        # Get existing page or create new one
        pages = self._context.pages
        if pages:
            return pages[0]

        return await self._context.new_page()

    async def inject_cookies(self, cookies: list[dict[str, Any]]) -> None:
        """
        Inject cookies into browser context.

        Args:
            cookies: List of cookie dictionaries from Playwright

        Raises:
            RuntimeError: If no context exists
        """
        if self._context is None:
            raise RuntimeError("Cannot inject cookies without browser context")

        await self._context.add_cookies(cookies)

    async def extract_cookies(self) -> list[dict[str, Any]]:
        """
        Extract all cookies from browser context.

        Returns:
            List of cookie dictionaries

        Raises:
            RuntimeError: If no context exists
        """
        if self._context is None:
            raise RuntimeError("Cannot extract cookies without browser context")

        return await self._context.cookies()

    async def close(self) -> None:
        """Close browser and cleanup resources."""
        if self._context:
            await self._context.close()
            self._context = None

        if self._browser:
            await self._browser.close()
            self._browser = None

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def __aenter__(self) -> "BrowserManager":
        """Async context manager entry."""
        await self.start_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    @property
    def is_running(self) -> bool:
        """Check if browser is currently running."""
        return self._browser is not None and self._browser.is_connected()
