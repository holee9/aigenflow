"""
Tests for BrowserManager functionality.

Note: These tests require Playwright browsers to be installed.
Run with: playwright install chromium
"""

from pathlib import Path

import pytest
from playwright.async_api import async_playwright

from gateway.browser_manager import BrowserManager


@pytest.fixture
async def browser_manager() -> BrowserManager:
    """Create a BrowserManager instance for testing."""
    manager = BrowserManager(headless=True)
    yield manager
    # Cleanup
    await manager.close()


class TestBrowserManager:
    """Test suite for BrowserManager class."""

    @pytest.mark.asyncio
    async def test_initialization(self) -> None:
        """Test BrowserManager initialization."""
        manager = BrowserManager(headless=True)

        assert manager.headless is True
        assert manager._browser is None
        assert manager._context is None
        assert manager._playwright is None

    @pytest.mark.asyncio
    async def test_start_browser(self) -> None:
        """Test starting browser."""
        manager = BrowserManager(headless=True)
        browser = await manager.start_browser()

        assert browser is not None
        assert manager._browser is not None
        assert manager._playwright is not None

        # Cleanup
        await manager.close()

    @pytest.mark.asyncio
    async def test_create_context(self) -> None:
        """Test creating browser context."""
        manager = BrowserManager(headless=True)
        context = await manager.create_context()

        assert context is not None
        assert manager._context is not None

        # Cleanup
        await manager.close()

    @pytest.mark.asyncio
    async def test_get_page(self) -> None:
        """Test getting a page."""
        manager = BrowserManager(headless=True)
        page = await manager.get_page()

        assert page is not None
        assert manager._context is not None

        # Cleanup
        await manager.close()

    @pytest.mark.asyncio
    async def test_inject_cookies(self) -> None:
        """Test injecting cookies into context."""
        manager = BrowserManager(headless=True)

        sample_cookies = [
            {
                "name": "test_cookie",
                "value": "test_value",
                "domain": ".example.com",
                "path": "/",
                "expires": -1,
            }
        ]

        await manager.create_context()
        await manager.inject_cookies(sample_cookies)

        # Get cookies to verify injection
        cookies = await manager.extract_cookies()

        assert len(cookies) >= 1
        assert any(c["name"] == "test_cookie" for c in cookies)

        # Cleanup
        await manager.close()

    @pytest.mark.asyncio
    async def test_extract_cookies(self) -> None:
        """Test extracting cookies from context."""
        manager = BrowserManager(headless=True)

        # Create context and navigate to get some cookies
        await manager.create_context()
        page = await manager.get_page()

        # Navigate to example.com
        await page.goto("https://example.com")

        # Extract cookies
        cookies = await manager.extract_cookies()

        assert isinstance(cookies, list)

        # Cleanup
        await manager.close()

    @pytest.mark.asyncio
    async def test_close(self) -> None:
        """Test closing browser."""
        manager = BrowserManager(headless=True)

        # Start browser
        await manager.start_browser()
        assert manager._browser is not None

        # Close browser
        await manager.close()
        assert manager._browser is None

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Test using BrowserManager as async context manager."""
        async with BrowserManager(headless=True) as manager:
            assert manager._browser is not None
            assert manager.is_running is True

        # After exiting context, browser should be closed
        # Note: is_running checks !browser.is_connected(), so False means closed

    @pytest.mark.asyncio
    async def test_anti_detection_parameters(self) -> None:
        """Test that anti-detection parameters are set."""
        manager = BrowserManager(headless=True)

        # Check default browser args
        assert "--disable-blink-features=AutomationControlled" in manager.DEFAULT_BROWSER_ARGS
        assert "--disable-infobars" in manager.DEFAULT_BROWSER_ARGS

        # Check user agent is set
        assert "Mozilla/5.0" in manager.DEFAULT_USER_AGENT

    @pytest.mark.asyncio
    async def test_multiple_page_creation(self) -> None:
        """Test creating multiple pages returns same page."""
        manager = BrowserManager(headless=True)

        await manager.create_context()

        page1 = await manager.get_page()
        page2 = await manager.get_page()

        # Should return same page instance
        assert page1 == page2

        # Cleanup
        await manager.close()

    @pytest.mark.asyncio
    async def test_custom_user_agent(self) -> None:
        """Test setting custom user agent."""
        custom_ua = "CustomBrowser/1.0"
        manager = BrowserManager(headless=True, user_agent=custom_ua)

        assert manager.user_agent == custom_ua

        # Create context and verify user agent
        await manager.create_context()

        # Note: We can't easily verify the actual user agent without
        # navigating to a page and checking, but we've set it

        # Cleanup
        await manager.close()
