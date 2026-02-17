"""
ChatGPT provider implementation.

Uses Playwright to interact with chat.openai.com.
"""

import asyncio
from pathlib import Path
from typing import Any

from core.models import AgentType
from gateway.base import BaseProvider, GatewayRequest, GatewayResponse
from gateway.cookie_storage import CookieStorage, SessionMetadata
from gateway.selector_loader import SelectorLoader


class ChatGPTProvider(BaseProvider):
    """
    Provider for ChatGPT (chat.openai.com).

    Handles login, message sending, and session management.
    """

    agent_type: AgentType = AgentType.CHATGPT
    provider_name: str = "chatgpt"
    base_url: str = "https://chat.openai.com"

    # Default authentication selector (fallback if selector_loader not available)
    DEFAULT_AUTH_SELECTOR = '#prompt-textarea, [contenteditable="true"], textarea'
    LOGIN_TIMEOUT = 300  # 5 minutes

    def __init__(
        self,
        profile_dir: Path,
        headless: bool = True,
        selector_loader: SelectorLoader | None = None,
    ) -> None:
        super().__init__(profile_dir, headless, selector_loader)
        self.base_url = "https://chat.openai.com"
        self._storage = CookieStorage(profile_dir)

    async def send_message(self, request: GatewayRequest) -> GatewayResponse:
        """
        Send message to ChatGPT.

        Args:
            request: GatewayRequest with task_name and prompt

        Returns:
            GatewayResponse with AI response
        """
        import time

        start_time = time.time()

        try:
            # Load cookies from storage
            cookies = self._storage.load_cookies()

            # Get browser manager
            browser_manager = await self.get_browser_manager()

            # Start browser and create context with cookies
            await browser_manager.start_browser()
            await browser_manager.create_context()
            await browser_manager.inject_cookies(cookies)

            # Get page and navigate to ChatGPT
            page = await browser_manager.get_page()

            # Use base URL from selector or fall back to configured URL
            base_url = self.get_selector("base_url", optional=True) or self.base_url
            await page.goto(
                base_url,
                wait_until="domcontentloaded",
                timeout=30000,
            )

            # Get selectors from configuration
            chat_input_selector = self.get_selector("chat_input", optional=True)
            if chat_input_selector is None:
                chat_input_selector = self.DEFAULT_AUTH_SELECTOR

            send_button_selector = self.get_selector("send_button", optional=True)
            response_container_selector = self.get_selector("response_container", optional=True)

            # Wait for chat input to be available
            try:
                await page.wait_for_selector(
                    chat_input_selector,
                    timeout=20000,
                )
            except Exception as exc:
                return GatewayResponse(
                    content="",
                    success=False,
                    error=f"Chat input not found. Session may be invalid: {exc}",
                    response_time=time.time() - start_time,
                )

            # Find and interact with the chat input
            chat_input = page.locator(chat_input_selector).first
            await chat_input.click()
            await chat_input.fill(request.prompt)

            # Send message - either click send button or press Enter
            message_sent = False
            if send_button_selector:
                try:
                    send_button = page.locator(send_button_selector).first
                    if await send_button.is_visible(timeout=2000):
                        await send_button.click()
                        message_sent = True
                except Exception:
                    pass

            # Fallback to Enter key if button click didn't work
            if not message_sent:
                await page.keyboard.press("Enter")

            # Wait for response
            timeout_ms = request.timeout * 1000
            response_received = False

            if response_container_selector:
                try:
                    # Wait for at least one response element to appear
                    await page.wait_for_selector(
                        response_container_selector,
                        timeout=timeout_ms,
                        state="visible",
                    )
                    response_received = True

                    # Additional wait for streaming to complete
                    # ChatGPT shows a loading indicator while generating
                    await page.wait_for_timeout(2000)

                    # Wait for any loading indicators to disappear
                    # Common patterns for ChatGPT loading states
                    loading_selectors = [
                        ".result-streaming",
                        "[data-testid='loading']",
                        ".cursor-blink",
                        "span.animate-pulse",
                    ]

                    for loading_selector in loading_selectors:
                        try:
                            await page.wait_for_selector(
                                loading_selector,
                                timeout=3000,
                                state="hidden",
                            )
                        except Exception:
                            pass

                except Exception as exc:
                    return GatewayResponse(
                        content="",
                        success=False,
                        error=f"Timeout waiting for response: {exc}",
                        response_time=time.time() - start_time,
                    )
            else:
                # Fallback: wait a fixed time if no response selector
                await page.wait_for_timeout(min(timeout_ms, 10000))
                response_received = True

            # Extract response content
            response_text = ""
            if response_received and response_container_selector:
                try:
                    # Get all response elements
                    response_elements = await page.locator(response_container_selector).all()

                    if response_elements:
                        # Get the last response (most recent)
                        last_response = response_elements[-1]
                        response_text = await last_response.inner_text()
                    else:
                        response_text = "Response received but content could not be extracted"

                except Exception as exc:
                    response_text = f"Response received but extraction failed: {exc}"

            # Estimate token count (rough approximation: ~4 chars per token)
            estimated_tokens = len(response_text) // 4 if response_text else 0

            return GatewayResponse(
                content=response_text,
                success=bool(response_text),
                tokens_used=estimated_tokens,
                response_time=time.time() - start_time,
            )

        except FileNotFoundError:
            return GatewayResponse(
                content="",
                success=False,
                error="No session found. Please run login first.",
                response_time=time.time() - start_time,
            )
        except Exception as exc:
            return GatewayResponse(
                content="",
                success=False,
                error=f"Failed to send message: {exc}",
                response_time=time.time() - start_time,
            )
        finally:
            # Clean up browser resources
            if self._browser_manager:
                await self._browser_manager.close()
                self._browser_manager = None

    async def check_session(self) -> bool:
        """
        Check if ChatGPT session is valid.

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

            # Get page and navigate to ChatGPT
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
        Execute ChatGPT login flow.

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

        # Get page and navigate to ChatGPT
        page = await browser_manager.get_page()
        await page.goto(self.base_url, wait_until="domcontentloaded", timeout=60000)

        # Wait for user to complete login
        # Detect successful login by waiting for auth element
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
        """
        Save ChatGPT session state to disk.

        Note: This is a synchronous wrapper for async cookie extraction.
        In practice, cookies are saved during login_flow.
        """
        # Cookies are saved during login_flow
        # This method exists for API compatibility
        pass

    def load_session(self) -> bool:
        """
        Load ChatGPT session state from disk.

        Returns:
            True if session was loaded successfully, False otherwise

        Note: This is a synchronous wrapper. Session validation
        happens in check_session() which is async.
        """
        return self._storage.session_exists()
