"""
Provider Context wrapper for browser pool integration.

This module provides a wrapper for provider-specific browser contexts,
handling cookie injection/extraction and page management with anti-detection measures.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from playwright.async_api import BrowserContext, Page

try:
    from playwright_stealth import stealth_async
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False

from core.logger import get_logger

if TYPE_CHECKING:
    from gateway.browser_pool import BrowserPool

logger = get_logger(__name__)


class ProviderContext:
    """
    Wrapper for provider-specific browser context.

    Manages cookie injection/extraction and page creation
    with anti-detection measures for AI provider gateways.
    """

    def __init__(
        self,
        provider_name: str,
        pool: BrowserPool | None = None,
        headless: bool = True,
    ) -> None:
        """
        Initialize provider context.

        Args:
            provider_name: Provider identifier (e.g., "chatgpt", "claude")
            pool: BrowserPool instance (lazy loaded via get_instance)
            headless: Whether to run browser in headless mode
        """
        self.provider_name = provider_name
        self._pool: BrowserPool | None = pool
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self._headless: bool = headless

        # NOTE: Pool is lazy-loaded in get_context() to avoid async __init__
        # Direct instantiation is prevented - must use BrowserPool.get_instance()

    async def get_context(self) -> BrowserContext:
        """
        Get or create browser context for this provider.

        Returns:
            BrowserContext instance
        """
        # FIX: Lazy load pool using singleton get_instance()
        if self._pool is None:
            from gateway.browser_pool import BrowserPool

            self._pool = await BrowserPool.get_instance(headless=self._headless)

        # Refresh context if None or if pool has a newer version (after reset)
        if self._context is None:
            self._context = await self._pool.get_context(self.provider_name)
        else:
            # Verify context is still valid by checking pages
            try:
                _ = self._context.pages  # Will raise if closed
            except Exception:
                # Context is closed, get new one
                self._context = await self._pool.get_context(self.provider_name)

        return self._context

    async def start_browser(self) -> Any:
        """
        Start browser and return browser instance for compatibility.

        This method provides compatibility with BrowserManager interface.
        The actual browser is managed by BrowserPool singleton.

        Returns:
            Browser instance from BrowserPool
        """
        if self._pool is None:
            from gateway.browser_pool import BrowserPool

            self._pool = await BrowserPool.get_instance(headless=self._headless)

        # Ensure context is initialized (which also ensures browser is initialized)
        await self.get_context()

        # Return the browser instance from pool for compatibility
        # Note: Direct browser access should be avoided in favor of context-based methods
        return self._pool._browser

    async def create_context(
        self,
        viewport: dict[str, int] | None = None,
        locale: str = "en-US",
    ) -> BrowserContext:
        """
        Get or create browser context for compatibility.

        This method provides compatibility with BrowserManager interface.
        In BrowserPool, contexts are managed per-provider and created lazily.

        Args:
            viewport: Viewport dimensions (ignored, uses pool defaults)
            locale: Browser locale (passed to pool)

        Returns:
            BrowserContext instance for this provider
        """
        # Simply delegate to get_context which handles lazy loading
        return await self.get_context()

    async def get_page(self) -> Page:
        """
        Get or create page with anti-detection.

        Returns:
            Page instance with stealth applied
        """
        context = await self.get_context()

        # Return existing page if available
        if self._page and not self._page.is_closed():
            return self._page

        # Create new page
        self._page = await context.new_page()

        # Apply stealth
        if STEALTH_AVAILABLE:
            try:
                await stealth_async(self._page)
                logger.debug(f"Applied stealth to page for {self.provider_name}")
            except Exception as e:
                logger.warning(f"Stealth application failed for {self.provider_name}: {e}")

        return self._page

    async def inject_cookies(self, cookies: list[dict[str, Any]]) -> None:
        """
        Inject cookies into provider context.

        Args:
            cookies: List of cookie dictionaries
        """
        context = await self.get_context()
        await context.add_cookies(cookies)
        logger.debug(f"Injected {len(cookies)} cookies for {self.provider_name}")

    async def extract_cookies(self) -> list[dict[str, Any]]:
        """
        Extract cookies from provider context.

        Returns:
            List of cookie dictionaries
        """
        context = await self.get_context()
        cookies = await context.cookies()
        logger.debug(f"Extracted {len(cookies)} cookies from {self.provider_name}")
        return cookies

    async def close(self) -> None:
        """
        Close provider page (context managed by pool).
        """
        if self._page and not self._page.is_closed():
            try:
                # Wait for page to be idle before closing (helps with pending operations)
                try:
                    await self._page.wait_for_load_state("domcontentloaded", timeout=1000)
                except Exception:
                    pass  # Ignore timeout, proceed with close
                await self._page.close()
                self._page = None
                logger.debug(f"Closed page for {self.provider_name}")
            except Exception as e:
                logger.warning(f"Failed to close page for {self.provider_name}: {e}")
                self._page = None  # Clear reference even if close failed

    async def get_url(self, url: str, wait_until: str = "domcontentloaded", timeout: int = 60000) -> Page:
        """
        Navigate to URL with error handling.

        Args:
            url: URL to navigate to
            wait_until: Navigation wait strategy
            timeout: Navigation timeout in ms

        Returns:
            Page instance after navigation
        """
        page = await self.get_page()
        try:
            await page.goto(url, wait_until=wait_until, timeout=timeout)
            return page
        except Exception as e:
            logger.error(f"Failed to navigate to {url} for {self.provider_name}: {e}")
            raise
