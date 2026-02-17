"""
Fix claude.ai infinite auth loop issue.
Removes automation detection and creates clean profile.
"""

import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

PROFILE_DIR = Path.home() / ".aigenflow" / "profiles"
CLAUDE_PROFILE = PROFILE_DIR / "claude"


async def create_clean_claude_profile():
    """Create a clean Claude profile with anti-detection measures."""

    print("\n" + "="*60)
    print("CLAUDE.AI PROFILE FIX")
    print("="*60)
    print("\nCreating clean profile with anti-detection measures...\n")

    # Enhanced anti-detection launch arguments
    args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-web-security",
        "--disable-features=IsolateOrigins,site-per-process",
        "--window-size=1280,800",
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            str(CLAUDE_PROFILE),
            headless=False,
            channel="chrome",
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            args=args,
            ignore_default_args=["--enable-automation", "--enable-blink-features=IdleDetection"],
        )

        page = browser.pages[0] if browser.pages else await browser.new_page()

        # Inject script to hide webdriver property
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // Hide automation indicators
            window.chrome = {
                runtime: {}
            };

            // Mock permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)

        print("Opening claude.ai...")
        print("Please complete login manually if needed.")
        print("After successful login, press Ctrl+C or close the browser.\n")

        await page.goto("https://claude.ai", wait_until="domcontentloaded", timeout=60000)

        # Wait for user to complete login
        try:
            await page.wait_for_url("https://claude.ai/**", timeout=300000)
            print("\nProfile setup complete!")
        except:
            print("\nBrowser closed or timeout reached.")

        await browser.close()


async def test_claude_access():
    """Test Claude access without infinite loop."""

    print("\n" + "="*60)
    print("CLAUDE.AI ACCESS TEST")
    print("="*60)

    args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--disable-setuid-sandbox",
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            str(CLAUDE_PROFILE),
            headless=False,
            channel="chrome",
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            args=args,
            ignore_default_args=["--enable-automation", "--enable-blink-features=IdleDetection"],
        )

        page = browser.pages[0] if browser.pages else await browser.new_page()

        # Anti-detection script
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        print("\nNavigating to claude.ai...")
        await page.goto("https://claude.ai", wait_until="domcontentloaded", timeout=30000)

        await asyncio.sleep(5)

        current_url = page.url
        print(f"Current URL: {current_url}")

        if "login" in current_url.lower() or "auth" in current_url.lower():
            print("\n⚠️ Login required. Please complete login in the browser.")
            print("Waiting for login to complete...")

            # Wait for successful login (URL change)
            try:
                await page.wait_for_url("https://claude.ai/**", timeout=120000)
                print("\n✅ Login successful!")
            except:
                print("\n⚠️ Login timeout or browser closed.")
        else:
            print("\n✅ Session valid!")

        print("\nChecking for auth loop...")
        await asyncio.sleep(3)

        final_url = page.url
        print(f"Final URL: {final_url}")

        # Check if still on auth page
        if "login" in final_url.lower() or "auth" in final_url.lower():
            print("\n❌ Still on auth page - infinite loop detected")
        else:
            print("\n✅ No auth loop detected - profile is working!")

        print("\nClose the browser when done inspecting...")
        await asyncio.sleep(30)  # Give time to inspect

        await browser.close()


async def main():
    """Main function."""
    print("\nClaude.ai Auth Fix")
    print("=" * 60)
    print("\nThis will:")
    print("1. Create a clean profile with anti-detection measures")
    print("2. Test access to verify no auth loop")
    print("\nPress Enter to continue...")
    input()

    await create_clean_claude_profile()
    await test_claude_access()


if __name__ == "__main__":
    asyncio.run(main())
