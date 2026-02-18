"""
Browser Pool for Aigenflow - Single browser instance with multiple contexts.

This module implements a singleton pattern for managing a single browser instance
across all AI provider agents, reducing memory usage and startup time.
"""

from __future__ import annotations

import asyncio
import signal
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

    _instance: BrowserPool | None = None
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
    async def get_instance(cls, headless: bool = True) -> BrowserPool:
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

        Implements graceful cleanup with error handling and subprocess termination.
        """
        logger.debug("[BrowserPool] Starting close_all() cleanup")
        cleanup_errors = []

        # Close all contexts first
        logger.debug(f"[BrowserPool] Closing {len(self._contexts)} contexts")
        for provider_name, context in self._contexts.items():
            if context:
                try:
                    await context.close()
                    logger.debug(f"[BrowserPool] Closed context for {provider_name}")
                except Exception as e:
                    cleanup_errors.append(f"{provider_name}: {e}")
                    logger.debug(f"[BrowserPool] Error closing {provider_name}: {e}")

        self._contexts.clear()
        self._valid_contexts.clear()  # Clear valid contexts tracking
        self._context_locks.clear()  # Clear locks too
        logger.debug("[BrowserPool] Contexts and locks cleared")

        # Close browser
        if self._browser:
            try:
                # Close all pages in the browser first (helps with subprocess cleanup)
                contexts = self._browser.contexts
                logger.debug(f"[BrowserPool] Closing {len(contexts)} browser contexts")
                for ctx in contexts:
                    try:
                        await ctx.close()
                    except Exception:
                        pass
                logger.debug("[BrowserPool] Closing browser")
                await self._browser.close()
                # Allow subprocess transports to close gracefully
                await asyncio.sleep(0.1)
                logger.debug("[BrowserPool] Browser closed")
            except Exception as e:
                cleanup_errors.append(f"browser: {e}")
                logger.debug(f"[BrowserPool] Error closing browser: {e}")
            self._browser = None

        # Stop playwright
        if self._playwright:
            try:
                logger.debug("[BrowserPool] Stopping playwright")
                await self._playwright.stop()
                # Allow subprocess transports to fully close before event loop cleanup
                await asyncio.sleep(0.1)
                logger.debug("[BrowserPool] Playwright stopped")
            except Exception as e:
                cleanup_errors.append(f"playwright: {e}")
                logger.debug(f"[BrowserPool] Error stopping playwright: {e}")
            self._playwright = None

        # NOTE: Skip subprocess termination during close_all()
        # OS automatically terminates child processes when parent exits.
        # Calling psutil during cleanup causes hangs and KeyboardInterrupt.
        # _terminate_browser_subprocesses() is available for manual cleanup if needed.

        self._initialized = False

        # Filter out expected cleanup errors (event loop already closed during shutdown)
        # These are benign during program exit
        expected_errors = ["Event loop is closed", "'NoneType' object has no attribute 'send'"]
        filtered_errors = [e for e in cleanup_errors if not any(exp in e for exp in expected_errors)]

        if filtered_errors:
            logger.warning(f"BrowserPool cleanup had errors: {filtered_errors}")
        elif cleanup_errors:
            # Only expected errors - log at debug level
            logger.debug(f"BrowserPool cleanup: {len(cleanup_errors)} expected errors during shutdown")
        else:
            logger.info("BrowserPool closed all resources")

        logger.debug("[BrowserPool] close_all() completed")

    async def _terminate_browser_subprocesses(self) -> None:
        """
        Forcefully terminate any remaining browser subprocesses.

        This is a safety measure for orphaned Chromium processes.
        Uses psutil if available, otherwise attempts signal-based termination.
        """
        try:
            import psutil

            current_process = psutil.Process()
            children = current_process.children(recursive=True)

            browser_procs = []
            for child in children:
                try:
                    name = child.name().lower()
                    if "chromium" in name or "chrome" in name or "chrome.exe" in name:
                        browser_procs.append(child)
                except Exception:
                    pass

            if browser_procs:
                # Try graceful termination first
                for proc in browser_procs:
                    try:
                        proc.terminate()
                    except Exception:
                        pass

                # Wait up to 1 second
                try:
                    await asyncio.sleep(0.5)
                except Exception:
                    pass

                # Force kill any remaining
                for proc in browser_procs:
                    try:
                        if proc.is_running():
                            proc.kill()
                    except Exception:
                        pass

                logger.debug(f"Terminated {len(browser_procs)} browser subprocess(es)")
        except ImportError:
            # psutil not available, try signal-based approach
            await self._signal_terminate_subprocesses()
        except Exception as e:
            logger.debug(f"Subprocess termination warning: {e}")

    async def _signal_terminate_subprocesses(self) -> None:
        """
        Fallback subprocess termination using OS signals.

        Used when psutil is not available.
        """
        import os

        try:
            # Send SIGTERM to process group (Unix) or current process (Windows)
            if hasattr(signal, "SIGTERM"):
                # Unix-like systems
                os.killpg(os.getpgid(0), signal.SIGTERM)
            else:
                # Windows - can't easily kill process group without psutil
                pass
        except Exception:
            pass

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
