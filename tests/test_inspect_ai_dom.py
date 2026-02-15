"""
Inspect actual AI service DOM structure for response capture.
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

PROFILE_DIR = Path.home() / ".aigenflow" / "profiles"
BROWSER_CHANNEL = "chrome"


async def inspect_claude():
    """Inspect Claude DOM structure."""
    profile_path = PROFILE_DIR / "claude"

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            str(profile_path),
            headless=False,
            channel=BROWSER_CHANNEL,
            viewport={"width": 1280, "height": 800},
        )
        page = context.pages[0] if context.pages else await context.new_page()

        await page.goto("https://claude.ai", wait_until="domcontentloaded", timeout=30000)

        print("\n" + "="*60)
        print("CLAUDE DOM INSPECTION")
        print("="*60)
        print("Current URL:", page.url)

        # Check for login
        if "login" in page.url.lower() or "signin" in page.url.lower():
            print("Not logged in")
            await context.close()
            return

        # Try to find message containers
        selectors_to_try = [
            "div[data-testid='message-content']",
            "div[data-message-author-role]",
            ".font-claude-message",
            "article",
            "[class*='message']",
            "[class*='response']",
        ]

        for selector in selectors_to_try:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"\nSelector: {selector}")
                    print(f"  Found: {len(elements)} elements")
                    for i, elem in enumerate(elements[-3:]):  # Last 3
                        text = await elem.inner_text()
                        preview = text[:100].replace("\n", " ")
                        print(f"  [{i+len(elements)-3}] {preview}...")
            except Exception as e:
                print(f"Selector {selector}: Error - {e}")

        # Wait for user to see the page
        input("\nPress Enter to continue...")

        await context.close()


async def inspect_gemini():
    """Inspect Gemini DOM structure."""
    profile_path = PROFILE_DIR / "gemini"

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            str(profile_path),
            headless=False,
            channel=BROWSER_CHANNEL,
            viewport={"width": 1280, "height": 800},
        )
        page = context.pages[0] if context.pages else await context.new_page()

        await page.goto("https://gemini.google.com", wait_until="domcontentloaded", timeout=30000)

        print("\n" + "="*60)
        print("GEMINI DOM INSPECTION")
        print("="*60)
        print("Current URL:", page.url)

        # Check for login
        if "login" in page.url.lower() or "signin" in page.url.lower():
            print("Not logged in")
            await context.close()
            return

        # Try to find message containers
        selectors_to_try = [
            ".model-response",
            "div[data-test-id='chat-turn']",
            "[class*='response']",
            "[class*='message']",
            "markdown",
            ".text-content",
        ]

        for selector in selectors_to_try:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"\nSelector: {selector}")
                    print(f"  Found: {len(elements)} elements")
                    for i, elem in enumerate(elements[-3:]):  # Last 3
                        text = await elem.inner_text()
                        preview = text[:100].replace("\n", " ")
                        print(f"  [{i+len(elements)-3}] {preview}...")
            except Exception as e:
                print(f"Selector {selector}: Error - {e}")

        input("\nPress Enter to continue...")
        await context.close()


async def inspect_perplexity():
    """Inspect Perplexity DOM structure."""
    profile_path = PROFILE_DIR / "perplexity"

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            str(profile_path),
            headless=False,
            channel=BROWSER_CHANNEL,
            viewport={"width": 1280, "height": 800},
        )
        page = context.pages[0] if context.pages else await context.new_page()

        await page.goto("https://www.perplexity.ai", wait_until="domcontentloaded", timeout=30000)

        print("\n" + "="*60)
        print("PERPLEXITY DOM INSPECTION")
        print("="*60)
        print("Current URL:", page.url)

        # Check for login
        if "login" in page.url.lower() or "signin" in page.url.lower():
            print("Not logged in")
            await context.close()
            return

        # Try to find message containers
        selectors_to_try = [
            ".thread-message",
            "[class*='answer']",
            "[class*='response']",
            "[class*='message']",
            "div[class*='prose']",
        ]

        for selector in selectors_to_try:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"\nSelector: {selector}")
                    print(f"  Found: {len(elements)} elements")
                    for i, elem in enumerate(elements[-3:]):  # Last 3
                        text = await elem.inner_text()
                        preview = text[:100].replace("\n", " ")
                        print(f"  [{i+len(elements)-3}] {preview}...")
            except Exception as e:
                print(f"Selector {selector}: Error - {e}")

        input("\nPress Enter to continue...")
        await context.close()


async def main():
    """Run all inspections."""
    print("\n" + "="*60)
    print("AI SERVICE DOM INSPECTION")
    print("="*60)
    print("\nThis will open browsers for inspection.")
    print("Close each browser when done inspecting.\n")

    await inspect_claude()
    await inspect_gemini()
    await inspect_perplexity()


if __name__ == "__main__":
    asyncio.run(main())
