"""
Browser Pool for AigenFlow - Single browser instance with multiple contexts.

This module implements a singleton pattern for managing a single browser instance
across all AI provider agents, reducing memory usage and startup time.
"""

import asyncio
from typing import Any

from playwright.async_api import Browser, BrowserContext

try:
    from playwright_stealth import stealth_async
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False

from core.logger import get_logger

logger = get_logger(__name__)


class BrowserPool:
    """
    Singleton pool managing a single browser instance with multiple contexts.

    Benefits:
        - Single browser process (~50-100MB) vs multiple (~200-400MB)
        - Context isolation ensures sessions don't interfere
        - Lazy context creation for efficiency
        - Lifecycle management for cleanup

    Thread Safety:
        - Uses asyncio.Lock for singleton creation
        - Per-provider locks for context creation
    """

    _instance: "BrowserPool | None" = None
    _lock = asyncio.Lock()

    def __init__(self) -> None:
        """Private constructor - use get_instance() instead."""
        self._browser: Browser | None = None
        self._contexts: dict[str, BrowserContext] = {}
        self._context_locks: dict[str, asyncio.Lock] = {}
        self._valid_contexts: set[str] = set()  # Track created, not-closed contexts
        self._playwright = None
        self.headless: bool = True
        self._initialized = False

    @classmethod
    async def get_instance(cls, headless: bool = True) -> "BrowserPool":
        """
        Get or create singleton instance with async lock protection.

        Args:
            headless: Whether to run browser in headless mode

        Returns:
            BrowserPool instance
        """
        # CRITICAL FIX: Acquire lock FIRST to prevent race condition
        async with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
                await cls._instance.initialize(headless)
        return cls._instance

    async def initialize(self, headless: bool = True) -> None:
        """
        Initialize browser pool.

        Args:
            headless: Headless mode flag
        """
        if self._initialized:
            return

        self.headless = headless

        try:
            from playwright.async_api import async_playwright

            self._playwright = await async_playwright().start()

            # Launch single browser instance with anti-detection
            self._browser = await self._playwright.chromium.launch(
                headless=headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--exclude-switches=enable-automation",
                    "--disable-infobars",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-gpu",
                    "--disable-web-security",
                    "--disable-features=IsolateOrigins,site-per-process",
                    "--disable-extensions",
                    "--disable-background-timer-throttling",
                    "--disable-renderer-backgrounding",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-background-networking",
                ],
            )

            self._initialized = True
            logger.info(
                "BrowserPool initialized",
                headless=headless,
                browser_id=id(self._browser) if self._browser else None,
            )

        except Exception as exc:
            logger.error("BrowserPool initialization failed", error=str(exc))
            await self.close()  # Cleanup on failure
            raise RuntimeError(f"Failed to initialize BrowserPool: {exc}") from exc

    async def get_context(
        self,
        provider_name: str,
        viewport: dict[str, int] | None = None,
        locale: str = "en-US",
    ) -> BrowserContext:
        """
        Get or create browser context for provider.

        Uses lazy loading strategy - contexts are created on first use.

        Args:
            provider_name: Provider identifier (e.g., "chatgpt", "claude")
            viewport: Viewport dimensions (default: 1280x720)
            locale: Browser locale

        Returns:
            BrowserContext instance for the provider
        """
        if not self._initialized:
            await self.initialize(self.headless)

        # Return existing context if available
        # Use _valid_contexts set to track which contexts have been created and not closed
        if provider_name in self._valid_contexts and provider_name in self._contexts:
            context = self._contexts[provider_name]
            # Quick health check: try to access context
            try:
                _ = context.pages  # Will raise if context is closed
                logger.debug(f"Reusing existing context for {provider_name}")
                return context
            except Exception:
                # Context is closed, remove from valid set
                self._valid_contexts.discard(provider_name)

        # FIX: Use setdefault() to prevent race condition in lock creation
        lock = self._context_locks.setdefault(provider_name, asyncio.Lock())

        # Create new context with lock for thread safety
        async with lock:
            # Double-check after acquiring lock
            if provider_name in self._valid_contexts and provider_name in self._contexts:
                context = self._contexts[provider_name]
                try:
                    _ = context.pages
                    return context
                except Exception:
                    self._valid_contexts.discard(provider_name)

            # Create new context
            viewport_config = viewport or {"width": 1280, "height": 720}
            context = await self._browser.new_context(
                viewport=viewport_config,
                locale=locale,
            )

            # NOTE: Stealth is applied per-page, not per-context
            # This avoids page crashes from creating/closing pages during context init

            self._contexts[provider_name] = context
            self._valid_contexts.add(provider_name)  # Mark as valid
            logger.info(f"Created new context for {provider_name}")

            return context

    async def get_page(
        self,
        provider_name: str,
        viewport: dict[str, int] | None = None,
        locale: str = "en-US",
    ) -> tuple[BrowserContext, Any]:
        """
        Get or create page for provider with anti-detection.

        Args:
            provider_name: Provider identifier
            viewport: Viewport dimensions
            locale: Browser locale

        Returns:
            Tuple of (BrowserContext, Page)
        """
        context = await self.get_context(provider_name, viewport, locale)

        # Create new page for this request
        page = await context.new_page()

        # Apply anti-detection to page
        if STEALTH_AVAILABLE:
            try:
                await stealth_async(page)
            except Exception:
                pass  # Continue without stealth

        return context, page

    async def preload_context(
        self,
        provider_name: str,
        cookies: list[dict[str, Any]],
    ) -> BrowserContext:
        """
        Preload context with cookies.

        Args:
            provider_name: Provider identifier
            cookies: List of cookie dictionaries

        Returns:
            BrowserContext with injected cookies
        """
        context = await self.get_context(provider_name)
        await context.add_cookies(cookies)
        logger.info(f"Preloaded context for {provider_name}", cookie_count=len(cookies))
        return context

    async def close_context(self, provider_name: str) -> None:
        """Close specific provider context."""
        if provider_name in self._contexts:
            context = self._contexts[provider_name]
            if context:
                try:
                    await context.close()
                    logger.info(f"Closed context for {provider_name}")
                except Exception as e:
                    logger.warning(f"Failed to close context for {provider_name}: {e}")
            del self._contexts[provider_name]

        # FIX: Remove from valid contexts and clean up lock
        self._valid_contexts.discard(provider_name)
        if provider_name in self._context_locks:
            del self._context_locks[provider_name]

    async def close_all(self) -> None:
        """
        Close all contexts and browser.

        Implements graceful cleanup with error handling.
        """
        cleanup_errors = []

        # Close all contexts first
        for provider_name, context in self._contexts.items():
            if context:
                try:
                    await context.close()
                except Exception as e:
                    cleanup_errors.append(f"{provider_name}: {e}")

        self._contexts.clear()
        self._valid_contexts.clear()  # Clear valid contexts tracking
        self._context_locks.clear()  # Clear locks too

        # Close browser
        if self._browser:
            try:
                await self._browser.close()
            except Exception as e:
                cleanup_errors.append(f"browser: {e}")
            self._browser = None

        # Stop playwright
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception as e:
                cleanup_errors.append(f"playwright: {e}")
            self._playwright = None

        self._initialized = False

        if cleanup_errors:
            logger.warning(f"BrowserPool cleanup had errors: {cleanup_errors}")
        else:
            logger.info("BrowserPool closed all resources")

    @property
    def is_initialized(self) -> bool:
        """Check if pool is initialized."""
        return self._initialized

    @property
    def context_count(self) -> int:
        """Get number of active contexts."""
        return len(self._valid_contexts)

    @property
    def active_contexts(self) -> list[str]:
        """Get list of active provider names."""
        return list(self._valid_contexts)


async def reset_pool() -> None:
    """Reset the singleton instance (for testing)."""
    if BrowserPool._instance:
        await BrowserPool._instance.close_all()
    BrowserPool._instance = None
    BrowserPool._lock = asyncio.Lock()
