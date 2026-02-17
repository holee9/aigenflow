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
        # TODO: Implement Playwright interaction
        # 1. Navigate to chat.openai.com
        # 2. Find prompt textarea
        # 3. Input prompt
        # 4. Wait for response
        # 5. Extract response

        # Placeholder response
        return GatewayResponse(
            content=f"ChatGPT response to: {request.task_name}",
            success=True,
        )

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
                wait_until="commit",
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
                    timeout=10000,
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
        await page.goto(self.base_url, wait_until="commit", timeout=60000)

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
