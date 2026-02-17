"""
Claude provider implementation.

Uses Playwright to interact with claude.ai.
"""

import asyncio
from pathlib import Path
from time import time

from core.models import AgentType
from gateway.base import BaseProvider, GatewayRequest, GatewayResponse
from gateway.cookie_storage import CookieStorage, SessionMetadata
from gateway.selector_loader import SelectorLoader


class ClaudeProvider(BaseProvider):
    """
    Provider for Claude (claude.ai).

    Handles login, message sending, and session management.
    """

    agent_type: AgentType = AgentType.CLAUDE
    provider_name: str = "claude"
    base_url: str = "https://claude.ai"

    # Default authentication selector (fallback if selector_loader not available)
    DEFAULT_AUTH_SELECTOR = 'div[contenteditable="true"], [contenteditable="true"]'
    LOGIN_TIMEOUT = 300  # 5 minutes

    def __init__(
        self,
        profile_dir: Path,
        headless: bool = True,
        selector_loader: SelectorLoader | None = None,
    ) -> None:
        super().__init__(profile_dir, headless, selector_loader)
        self.base_url = "https://claude.ai"
        self._storage = CookieStorage(profile_dir)

    async def send_message(self, request: GatewayRequest) -> GatewayResponse:
        """
        Send message to Claude using Playwright.

        Process:
        1. Load stored cookies
        2. Navigate to claude.ai
        3. Find and fill chat input
        4. Send message
        5. Wait for response
        6. Extract response content

        Args:
            request: GatewayRequest with task_name and prompt

        Returns:
            GatewayResponse with content and metadata
        """
        start_time = time()

        try:
            # Load cookies from storage
            cookies = self._storage.load_cookies()

            # Get browser manager
            browser_manager = await self.get_browser_manager()

            # Start browser and create context
            await browser_manager.start_browser()
            await browser_manager.create_context()

            # Inject cookies
            await browser_manager.inject_cookies(cookies)

            # Get page and navigate to Claude
            page = await browser_manager.get_page()
            await page.goto(
                self.base_url,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            # Get selectors from selector_loader
            chat_input_selector = self.get_selector("chat_input", optional=True)
            if chat_input_selector is None:
                chat_input_selector = self.DEFAULT_AUTH_SELECTOR

            send_button_selector = self.get_selector("send_button", optional=True)
            response_selector = self.get_selector("response_container", optional=True)

            # Wait for chat input to be available
            await page.wait_for_selector(
                chat_input_selector,
                timeout=30000,
            )

            # Find the chat input element
            chat_input = await page.query_selector(chat_input_selector)
            if not chat_input:
                return GatewayResponse(
                    content="",
                    success=False,
                    error="Chat input element not found",
                )

            # Click on input to focus
            await chat_input.click()

            # Type the prompt
            await page.keyboard.type(request.prompt, delay=10)

            # Small delay to ensure input is registered
            await asyncio.sleep(0.5)

            # Send the message - try multiple methods
            message_sent = False

            # Method 1: Click send button if available
            if send_button_selector:
                try:
                    send_button = await page.query_selector(send_button_selector)
                    if send_button:
                        await send_button.click()
                        message_sent = True
                except Exception:
                    pass

            # Method 2: Press Enter if button click failed
            if not message_sent:
                # Use modifier key combination for Claude (Cmd+Enter on Mac, Ctrl+Enter on Windows)
                # For web interface, often just Enter works, or Cmd/Ctrl+Enter
                try:
                    await page.keyboard.press("Enter")
                    message_sent = True
                except Exception:
                    pass

            if not message_sent:
                return GatewayResponse(
                    content="",
                    success=False,
                    error="Failed to send message",
                )

            # Wait for response with timeout
            timeout_ms = request.timeout * 1000
            response_content = ""

            # Wait for response container to appear
            if response_selector:
                try:
                    # Wait for any response element to appear
                    await page.wait_for_selector(
                        response_selector,
                        timeout=timeout_ms,
                    )

                    # Additional wait to ensure content is loaded
                    await asyncio.sleep(2)

                    # Extract text content from response
                    response_elements = await page.query_selector_all(response_selector)
                    if response_elements:
                        # Get the last response element (most recent)
                        last_response = response_elements[-1]
                        response_content = await last_response.inner_text()

                except Exception as exc:
                    return GatewayResponse(
                        content="",
                        success=False,
                        error=f"Failed to extract response: {exc}",
                    )
            else:
                # Fallback: wait and get all text content
                await asyncio.sleep(min(10, request.timeout))
                response_content = await page.inner_text("body")

            # Calculate response time
            response_time = time() - start_time

            # Clean up
            await browser_manager.close()

            return GatewayResponse(
                content=response_content.strip(),
                success=True,
                response_time=response_time,
                metadata={
                    "provider": self.provider_name,
                    "task_name": request.task_name,
                },
            )

        except Exception as exc:
            # Clean up on error
            if self._browser_manager:
                try:
                    await self._browser_manager.close()
                except Exception:
                    pass

            return GatewayResponse(
                content="",
                success=False,
                error=str(exc),
                response_time=time() - start_time,
            )

    async def check_session(self) -> bool:
        """
        Check if Claude session is valid.

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

            # Get page and navigate to Claude
            page = await browser_manager.get_page()
            await page.goto(
                self.base_url,
                wait_until="domcontentloaded",
                timeout=60000,
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
        Execute Claude login flow.

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

        # Get page and navigate to Claude
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
        """Save Claude session state to disk."""
        # Cookies are saved during login_flow
        pass

    def load_session(self) -> bool:
        """Load Claude session state from disk."""
        return self._storage.session_exists()
