"""
Perplexity provider implementation.

Uses Playwright to interact with perplexity.ai.
"""

from pathlib import Path

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

    # Authentication detection selectors
    AUTH_SELECTOR = 'textarea[placeholder="Ask anything..."]'
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
        """Send message to Perplexity."""
        # TODO: Implement Playwright interaction
        return GatewayResponse(
            content=f"Perplexity response to: {request.task_name}",
            success=True,
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
                wait_until="networkidle",
                timeout=30000,
            )

            # Check for authentication element
            try:
                await page.wait_for_selector(
                    self.AUTH_SELECTOR,
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
        Execute Perplexity login flow.

        Process:
        1. Check if session exists and is valid
        2. If not, launch browser in headed mode
        3. Wait for user to complete login
        4. Detect successful login via DOM element
        5. Extract and save cookies
        """
        # First check if existing session is valid
        if await self.check_session():
            return

        # Get browser manager
        browser_manager = await self.get_browser_manager()

        # Force headed mode for login
        browser_manager.headless = False

        # Start browser and create context
        await browser_manager.start_browser()
        await browser_manager.create_context()

        # Get page and navigate to Perplexity
        page = await browser_manager.get_page()
        await page.goto(self.base_url, wait_until="networkidle")

        # Wait for user to complete login
        try:
            await page.wait_for_selector(
                self.AUTH_SELECTOR,
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
