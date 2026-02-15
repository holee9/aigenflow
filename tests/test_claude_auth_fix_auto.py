"""
Automatic fix for claude.ai infinite auth loop.
Creates clean profile with enhanced anti-detection.
"""

import asyncio
import shutil
from pathlib import Path
from playwright.async_api import async_playwright

PROFILE_DIR = Path.home() / ".aigenflow" / "profiles"
CLAUDE_PROFILE = PROFILE_DIR / "claude"
CLAUDE_BACKUP = PROFILE_DIR / "claude.backup"


async def fix_claude_profile():
    """Fix Claude profile with enhanced anti-detection."""

    print("\n" + "="*60)
    print("CLAUDE.AI AUTH FIX")
    print("="*60)

    # Backup existing profile
    if CLAUDE_PROFILE.exists():
        print(f"\nBacking up existing profile to {CLAUDE_BACKUP}")
        if CLAUDE_BACKUP.exists():
            shutil.rmtree(CLAUDE_BACKUP)
        shutil.copytree(CLAUDE_PROFILE, CLAUDE_BACKUP)
        print("Backup complete")
    else:
        print("\nNo existing Claude profile found. Creating new one.")

    # Remove old profile to start fresh
    if CLAUDE_PROFILE.exists():
        print(f"\nRemoving old profile: {CLAUDE_PROFILE}")
        shutil.rmtree(CLAUDE_PROFILE)

    print("\nCreating new Claude profile with anti-detection...")

    # Enhanced launch arguments
    args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-web-security",
        "--disable-features=IsolateOrigins,site-per-process",
        "--disable-site-isolation-trials",
        "--window-size=1280,800",
    ]

    # Realistic user agent
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

    async with async_playwright() as p:
        print("\nLaunching browser with anti-detection measures...")

        browser = await p.chromium.launch_persistent_context(
            str(CLAUDE_PROFILE),
            headless=False,
            channel="chrome",
            viewport={"width": 1280, "height": 800},
            user_agent=user_agent,
            args=args,
            ignore_default_args=["--enable-automation", "--enable-blink-features=IdleDetection"],
            locale="en-US",
            timezone_id="America/New_York",
        )

        page = browser.pages[0] if browser.pages else await browser.new_page()

        # Anti-detection scripts
        await page.add_init_script("""
            // Hide webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // Mock chrome object
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

            // Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            // Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """)

        print("\nOpening claude.ai...")
        print("Please complete login if prompted.")
        print("The browser will close automatically after 30 seconds.\n")

        try:
            await page.goto("https://claude.ai", wait_until="domcontentloaded", timeout=60000)

            # Wait for page load and potential auth
            await asyncio.sleep(30)

            current_url = page.url
            print(f"\nCurrent URL: {current_url}")

            if "login" in current_url.lower() or "auth" in current_url.lower():
                print("\n⚠️ Still on login page after 30 seconds")
                print("You may need to complete login manually.")
                print("Press Enter when login is complete...")
                input()
            else:
                print("\n✅ Successfully loaded claude.ai main page!")

        except Exception as e:
            print(f"\n⚠️ Error: {e}")

        print("\nClosing browser...")
        await browser.close()

    print("\n" + "="*60)
    print("CLAUDE PROFILE FIX COMPLETE")
    print("="*60)
    print(f"\nNew profile created at: {CLAUDE_PROFILE}")
    print(f"Old profile backed up to: {CLAUDE_BACKUP}")
    print("\nYou can now run the reproducibility test.")


async def test_claude_access():
    """Test Claude access after fix."""

    print("\n" + "="*60)
    print("CLAUDE ACCESS TEST")
    print("="*60)

    args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
    ]

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            str(CLAUDE_PROFILE),
            headless=False,
            channel="chrome",
            viewport={"width": 1280, "height": 800},
            user_agent=user_agent,
            args=args,
            ignore_default_args=["--enable-automation"],
        )

        page = browser.pages[0] if browser.pages else await browser.new_page()

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

        if "login" not in current_url.lower() and "auth" not in current_url.lower():
            print("\n✅ Claude access successful - no auth loop!")
            print("\nTrying to send a test message...")

            try:
                # Try to find input and send message
                await page.wait_for_selector("[contenteditable='true'], div[contenteditable='true']", timeout=10000)
                editable = await page.query_selector("[contenteditable='true'], div[contenteditable='true']")

                if editable:
                    await editable.fill("Hello, this is a test message.")
                    await asyncio.sleep(1)
                    await editable.press("Enter")

                    print("Message sent! Waiting for response...")
                    await asyncio.sleep(15)

                    # Check for response
                    elements = await page.query_selector_all("div[data-testid='message-content']")
                    if elements and len(elements) >= 2:
                        print("\n✅ Response received - Claude is working!")
                    else:
                        print("\n⚠️ No response yet, but no auth loop!")
                else:
                    print("\n⚠️ Could not find input field")
            except Exception as e:
                print(f"\n⚠️ Test message error: {e}")
                print("But no auth loop detected!")
        else:
            print("\n❌ Auth loop still present")
            print("You may need to complete login manually in the browser.")

        print("\nClose browser to continue...")
        await asyncio.sleep(10)

        await browser.close()


async def main():
    """Main function."""
    await fix_claude_profile()

    print("\n" + "="*60)
    print("Test Claude access now?")
    print("1. Yes - Test access")
    print("2. No - Exit")
    print("="*60)

    choice = input("\nEnter choice (1 or 2): ")

    if choice == "1":
        await test_claude_access()

    print("\nDone! You can now run the reproducibility test.")


if __name__ == "__main__":
    asyncio.run(main())
