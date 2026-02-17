"""
Gemini provider implementation.

Uses Playwright to interact with gemini.google.com.
"""

import asyncio
import time
from pathlib import Path

from core.models import AgentType
from gateway.base import BaseProvider, GatewayRequest, GatewayResponse
from gateway.cookie_storage import CookieStorage, SessionMetadata
from gateway.selector_loader import SelectorLoader


class GeminiProvider(BaseProvider):
    """
    Provider for Gemini (gemini.google.com).

    Handles login, message sending, and session management.
    """

    agent_type: AgentType = AgentType.GEMINI
    provider_name: str = "gemini"
    base_url: str = "https://gemini.google.com"

    # Default authentication selector (fallback if selector_loader not available)
    DEFAULT_AUTH_SELECTOR = '.ql-editor, .rich-textarea, div[contenteditable="true"], textarea'
    LOGIN_TIMEOUT = 300  # 5 minutes

    def __init__(
        self,
        profile_dir: Path,
        headless: bool = True,
        selector_loader: SelectorLoader | None = None,
    ) -> None:
        super().__init__(profile_dir, headless, selector_loader)
        self.base_url = "https://gemini.google.com"
        self._storage = CookieStorage(profile_dir)

    async def send_message(self, request: GatewayRequest) -> GatewayResponse:
        """
        Send message to Gemini.

        Args:
            request: GatewayRequest with task_name and prompt

        Returns:
            GatewayResponse with AI response content
        """
        start_time = time.time()
        browser_manager = None

        try:
            # Load stored cookies
            cookies = self._storage.load_cookies()

            # Get browser manager
            browser_manager = await self.get_browser_manager()

            # Start browser and create context
            await browser_manager.start_browser()
            await browser_manager.create_context()

            # Inject stored cookies
            await browser_manager.inject_cookies(cookies)

            # Get page and navigate to Gemini
            page = await browser_manager.get_page()
            await page.goto(
                self.base_url,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            # Wait for page to load
            await asyncio.sleep(2)

            # Get selectors for Gemini
            chat_input_selector = self.get_selector("chat_input", optional=True)
            if chat_input_selector is None:
                chat_input_selector = self.DEFAULT_AUTH_SELECTOR

            send_button_selector = self.get_selector("send_button", optional=True)
            if send_button_selector is None:
                send_button_selector = "button[aria-label='Send'], button[aria-label='send']"

            response_container_selector = self.get_selector("response_container", optional=True)
            if response_container_selector is None:
                response_container_selector = ".model-response, .response-container, .conversation-turn, [data-testid*='response']"

            # Find and click the chat input
            try:
                input_element = await page.wait_for_selector(
                    chat_input_selector,
                    timeout=15000,
                )
                await input_element.click()
            except Exception as e:
                return GatewayResponse(
                    content="",
                    success=False,
                    error=f"Could not find chat input element: {e}",
                    response_time=time.time() - start_time,
                )

            # Type the prompt
            await input_element.fill(request.prompt)
            await asyncio.sleep(0.5)

            # Click send button or press Enter
            try:
                send_button = await page.query_selector(send_button_selector)
                if send_button:
                    await send_button.click()
                else:
                    await page.keyboard.press("Enter")
            except Exception:
                await page.keyboard.press("Enter")

            # Wait for response
            await asyncio.sleep(1)

            # Wait for response to appear with timeout
            timeout_ms = request.timeout * 1000
            response_content = ""

            try:
                await page.wait_for_selector(
                    response_container_selector,
                    timeout=timeout_ms,
                )

                # Extract response content
                await asyncio.sleep(2)

                response_elements = await page.query_selector_all(response_container_selector)
                if response_elements:
                    # Get the last response element (most recent)
                    last_response = response_elements[-1]
                    response_content = await last_response.inner_text()
                else:
                    response_content = await page.inner_text("body")

            except Exception as e:
                return GatewayResponse(
                    content="",
                    success=False,
                    error=f"Timeout waiting for response: {e}",
                    response_time=time.time() - start_time,
                )

            response_time = time.time() - start_time

            return GatewayResponse(
                content=response_content,
                success=True,
                response_time=response_time,
                metadata={"provider": "gemini"},
            )

        except FileNotFoundError:
            return GatewayResponse(
                content="",
                success=False,
                error="No session found. Please login first.",
                response_time=time.time() - start_time,
            )
        except Exception as e:
            return GatewayResponse(
                content="",
                success=False,
                error=f"Failed to send message: {e}",
                response_time=time.time() - start_time,
            )
        finally:
            if browser_manager:
                await browser_manager.close()

    async def check_session(self) -> bool:
        """
        Check if Gemini session is valid.

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

            # Get page and navigate to Gemini
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
        Execute Gemini login flow.

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

        # Get page and navigate to Gemini
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
        """Save Gemini session state to disk."""
        # Cookies are saved during login_flow
        pass

    def load_session(self) -> bool:
        """Load Gemini session state from disk."""
        return self._storage.session_exists()
