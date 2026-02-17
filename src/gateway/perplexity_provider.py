"""
Perplexity provider implementation.

Uses Playwright to interact with perplexity.ai.
"""

import asyncio
import time
from pathlib import Path
from typing import Any

from core.models import AgentType
from gateway.base import BaseProvider, GatewayRequest, GatewayResponse
from gateway.cookie_storage import CookieStorage, SessionMetadata
from gateway.selector_loader import SelectorLoader


class PerplexityProvider(BaseProvider):
    """
    Provider for Perplexity (perplexity.ai).

    Handles login, message sending, and session management.
    """

    agent_type: AgentType = AgentType.PERPLEXITY
    provider_name: str = "perplexity"
    base_url: str = "https://www.perplexity.ai"

    # Default authentication selector (fallback if selector_loader not available)
    DEFAULT_AUTH_SELECTOR = '[role="textbox"], textarea, div[contenteditable="true"]'
    LOGIN_TIMEOUT = 300  # 5 minutes

    def __init__(
        self,
        profile_dir: Path,
        headless: bool = True,
        selector_loader: SelectorLoader | None = None,
    ) -> None:
        super().__init__(profile_dir, headless, selector_loader)
        self.base_url = "https://www.perplexity.ai"
        self._storage = CookieStorage(profile_dir)

    async def send_message(self, request: GatewayRequest) -> GatewayResponse:
        """
        Send message to Perplexity.

        Args:
            request: GatewayRequest with task_name and prompt

        Returns:
            GatewayResponse with AI response content
        """
        start_time = time.time()

        try:
            # Load cookies from storage
            cookies = self._storage.load_cookies()

            # Get browser manager
            browser_manager = await self.get_browser_manager()

            # Start browser and create context
            await browser_manager.start_browser()
            await browser_manager.create_context()

            # Inject stored cookies
            await browser_manager.inject_cookies(cookies)

            # Get page and navigate to Perplexity
            page = await browser_manager.get_page()
            await page.goto(
                self.base_url,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            # Get selectors from selector_loader
            chat_input_selector = self.get_selector("chat_input")
            send_button_selector = self.get_selector("send_button", optional=True)
            response_container_selector = self.get_selector("response_container")

            # Wait for chat input to be available
            await page.wait_for_selector(
                chat_input_selector,
                timeout=30000,
            )

            # Check if there's a "new thread" or "new chat" button to click first
            new_chat_selector = self.get_selector("new_chat_button", optional=True)
            if new_chat_selector:
                try:
                    new_chat_button = page.locator(new_chat_selector).first
                    if await new_chat_button.is_visible():
                        await new_chat_button.click()
                        await asyncio.sleep(1)
                except Exception:
                    # New chat button may not exist or be clickable, continue
                    pass

            # Input the query
            chat_input = page.locator(chat_input_selector)
            await chat_input.fill(request.prompt)
            await asyncio.sleep(0.5)

            # Click send button if available, otherwise press Enter
            if send_button_selector:
                try:
                    send_button = page.locator(send_button_selector)
                    if await send_button.is_visible():
                        await send_button.click()
                    else:
                        await page.keyboard.press("Enter")
                except Exception:
                    await page.keyboard.press("Enter")
            else:
                await page.keyboard.press("Enter")

            # Wait for response to appear
            timeout_ms = request.timeout * 1000
            await page.wait_for_selector(
                response_container_selector,
                timeout=timeout_ms,
            )

            # Extract response content
            response_element = page.locator(response_container_selector).first

            # Wait a bit for content to fully load
            await asyncio.sleep(2)

            # Get text content from response
            content = await response_element.inner_text()

            # Calculate response time
            response_time = time.time() - start_time

            # Close browser
            await browser_manager.close()

            return GatewayResponse(
                content=content,
                success=True,
                response_time=response_time,
                metadata={"provider": "perplexity"},
            )

        except FileNotFoundError as exc:
            # No session file exists - need to login first
            return GatewayResponse(
                content="",
                success=False,
                error="No session found. Please run login_flow first.",
            )

        except Exception as exc:
            # Close browser on error
            try:
                browser_manager = await self.get_browser_manager()
                await browser_manager.close()
            except Exception:
                pass

            return GatewayResponse(
                content="",
                success=False,
                error=f"Failed to send message: {exc}",
            )

    async def check_session(self) -> bool:
        """
        Check if Perplexity session is valid.

        Returns:
            True if session is valid, False otherwise
        """
        try:
            # Load cookies from storage
            cookies = self._storage.load_cookies()

            # Get browser manager
            browser_manager = await self.get_browser_manager()

            # Create context and inject cookies
            await browser_manager.create_context()
            await browser_manager.inject_cookies(cookies)

            # Get page and navigate to Perplexity
            page = await browser_manager.get_page()
            await page.goto(
                self.base_url,
                wait_until="domcontentloaded",
                timeout=30000,
            )

            # Get auth selector (prefer selector_loader, fallback to default)
            auth_selector = self.get_selector("chat_input", optional=True)
            if auth_selector is None:
                auth_selector = self.DEFAULT_AUTH_SELECTOR

            # Check for authentication element
            try:
                await page.wait_for_selector(
                    auth_selector,
                    timeout=20000,
                )
                is_valid = True
            except Exception:
                is_valid = False

            # Close browser
            await browser_manager.close()

            # Update metadata
            if is_valid:
                self._storage.mark_validated()
            else:
                self._storage.mark_invalid()

            return is_valid

        except FileNotFoundError:
            # No session file exists
            return False
        except Exception:
            # Any error means session is invalid
            return False

    async def login_flow(self) -> None:
        """
        Execute Perplexity login flow.

        Process:
        1. Check if session file exists (quick check without browser)
        2. If not, launch browser in headed mode
        3. Wait for user to complete login
        4. Detect successful login via DOM element
        5. Extract and save cookies
        """
        # Quick check: if no session file exists, skip to login
        if not self._storage.session_exists():
            # No session file, proceed directly to login
            pass
        elif await self.check_session():
            # Session exists and is valid
            return
        # Session exists but is invalid, proceed to login

        # Get browser manager
        browser_manager = await self.get_browser_manager()

        # Force headed mode for login
        browser_manager.headless = False

        # Start browser and create context
        await browser_manager.start_browser()
        await browser_manager.create_context()

        # Get page and navigate to Perplexity
        page = await browser_manager.get_page()
        await page.goto(self.base_url, wait_until="domcontentloaded", timeout=60000)

        # Wait for user to complete login
        # Get auth selector (prefer selector_loader, fallback to default)
        auth_selector = self.get_selector("chat_input", optional=True)
        if auth_selector is None:
            auth_selector = self.DEFAULT_AUTH_SELECTOR

        try:
            await page.wait_for_selector(
                auth_selector,
                timeout=self.LOGIN_TIMEOUT * 1000,
            )

            # Extract cookies
            cookies = await browser_manager.extract_cookies()

            # Save encrypted cookies with metadata
            metadata = SessionMetadata(
                provider_name=self.provider_name,
                cookie_count=len(cookies),
                login_method="manual",
            )
            self._storage.save_cookies(cookies, metadata)

        except Exception as exc:
            raise RuntimeError(f"Login flow failed: {exc}") from exc

        finally:
            # Close browser
            await browser_manager.close()

    def save_session(self) -> None:
        """Save Perplexity session state to disk."""
        # Cookies are saved during login_flow
        pass

    def load_session(self) -> bool:
        """Load Perplexity session state from disk."""
        return self._storage.session_exists()
