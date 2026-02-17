"""
Playwright Gateway PoC Test
- Tests persistent profile session management
- Tests sending a message and capturing response from Perplexity
"""
import asyncio
import sys
from pathlib import Path

from playwright.async_api import TimeoutError as PlaywrightTimeout
from playwright.async_api import async_playwright

PROFILE_DIR = Path.home() / ".aigenflow" / "profiles"
TIMEOUT_MS = 60_000

# Use installed Chrome to avoid automation detection (CAPTCHA loops)
BROWSER_CHANNEL = "chrome"


async def setup_profile(provider: str, url: str):
    """Open browser for manual login, save profile on browser close."""
    profile_path = PROFILE_DIR / provider
    profile_path.mkdir(parents=True, exist_ok=True)

    print(f"[SETUP] Opening {provider} for login...")
    print(f"[SETUP] Profile path: {profile_path}")

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            str(profile_path),
            headless=False,
            channel=BROWSER_CHANNEL,
            viewport={"width": 1280, "height": 800},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else await context.new_page()

        print(f"[SETUP] Navigating to {url} (using installed Chrome)...")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        print(f"[SETUP] Page loaded: {await page.title()}")

        print()
        print(f"  >>> {provider} 에 로그인하세요.")
        print("  >>> 로그인 완료 후 브라우저 창을 닫으면 프로필이 저장됩니다.")
        print("  >>> (최대 5분 대기)")
        print()

        # Wait for user to close the browser page
        try:
            await page.wait_for_event("close", timeout=300_000)
            print("[SETUP] Browser closed by user.")
        except PlaywrightTimeout:
            print("[SETUP] Timeout (5 min). Saving profile now...")

        # Gracefully close context to flush profile to disk
        try:
            await context.close()
        except Exception:
            pass

        print(f"[SETUP] Profile saved for {provider}!")


async def check_session(provider: str, url: str) -> bool:
    """Check if saved profile has a valid session."""
    profile_path = PROFILE_DIR / provider

    if not profile_path.exists():
        print(f"[CHECK] No profile found for {provider}")
        return False

    print(f"[CHECK] Testing {provider} session...")

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            str(profile_path),
            headless=True,
            channel=BROWSER_CHANNEL,
            viewport={"width": 1280, "height": 800},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else await context.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            current_url = page.url
            title = await page.title()

            # Check if redirected to login page
            is_login = any(kw in current_url.lower() for kw in ["login", "signin", "auth"])
            is_valid = not is_login and title != ""

            print(f"[CHECK] URL: {current_url}")
            print(f"[CHECK] Title: {title}")
            print(f"[CHECK] Session valid: {is_valid}")

            await context.close()
            return is_valid

        except Exception as e:
            print(f"[CHECK] Error: {e}")
            await context.close()
            return False


async def send_message_perplexity(question: str) -> str:
    """Send a message to Perplexity and capture response."""
    profile_path = PROFILE_DIR / "perplexity"

    if not profile_path.exists():
        print("[ERROR] No Perplexity profile. Run: python poc_playwright.py setup perplexity")
        return ""

    print(f"[SEND] Sending to Perplexity: {question[:50]}...")

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            str(profile_path),
            headless=True,
            channel=BROWSER_CHANNEL,
            viewport={"width": 1280, "height": 800},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else await context.new_page()

        try:
            # Go to Perplexity
            await page.goto("https://www.perplexity.ai/", wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(2000)

            # Find textarea and type question
            textarea = page.locator("textarea").first
            await textarea.click()
            await textarea.fill(question)
            await page.wait_for_timeout(500)

            # Submit (Enter or button)
            await textarea.press("Enter")
            print("[SEND] Message sent, waiting for response...")

            # Wait for response to appear and complete
            await page.wait_for_timeout(10000)

            # Try to capture response text
            # Perplexity renders responses in markdown-like blocks
            response_selectors = [
                "[class*='prose']",
                "[class*='answer']",
                "[class*='response']",
                "[class*='markdown']",
                "article",
            ]

            response_text = ""
            for selector in response_selectors:
                elements = page.locator(selector)
                count = await elements.count()
                if count > 0:
                    for i in range(count):
                        text = await elements.nth(i).inner_text()
                        if len(text) > len(response_text):
                            response_text = text

            if not response_text:
                # Fallback: get all visible text from main content area
                body_text = await page.locator("main").inner_text()
                response_text = body_text

            await context.close()

            print(f"[SEND] Response length: {len(response_text)} chars")
            return response_text

        except Exception as e:
            print(f"[SEND] Error: {e}")
            await context.close()
            return ""


async def diag():
    """Diagnostic: launch headed browser to verify Playwright works."""
    print("[DIAG] Launching Chromium browser (headed mode)...")
    print("[DIAG] Browser should stay open for 10 seconds.")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://example.com", wait_until="domcontentloaded")
        title = await page.title()
        print(f"[DIAG] Page loaded OK - Title: {title}")
        print("[DIAG] Waiting 10 seconds... (browser should be visible)")
        await page.wait_for_timeout(10_000)
        await browser.close()
        print("[DIAG] Browser closed. Playwright headed mode works!")


async def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python poc_playwright.py setup <provider>    # Login and save profile")
        print("  python poc_playwright.py check <provider>    # Check session validity")
        print("  python poc_playwright.py test                # Send test message to Perplexity")
        print("  python poc_playwright.py diag                # Diagnostic: test browser launch")
        print("")
        print("Providers: perplexity, chatgpt, gemini, claude")
        return

    command = sys.argv[1]

    providers = {
        "perplexity": "https://www.perplexity.ai/",
        "chatgpt": "https://chat.openai.com/",
        "gemini": "https://gemini.google.com/",
        "claude": "https://claude.ai/",
    }

    if command == "setup":
        provider = sys.argv[2] if len(sys.argv) > 2 else "perplexity"
        url = providers.get(provider, providers["perplexity"])
        await setup_profile(provider, url)

    elif command == "check":
        provider = sys.argv[2] if len(sys.argv) > 2 else None
        if provider:
            url = providers.get(provider, providers["perplexity"])
            await check_session(provider, url)
        else:
            print("=== Session Health Check ===")
            for name, url in providers.items():
                await check_session(name, url)
                print()

    elif command == "test":
        question = "What are the top 3 advantages of TypeScript over JavaScript? Keep it brief."
        response = await send_message_perplexity(question)
        if response:
            print("\n=== RESPONSE ===")
            print(response[:1000])
        else:
            print("[FAIL] No response captured")

    elif command == "diag":
        await diag()

    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    asyncio.run(main())
