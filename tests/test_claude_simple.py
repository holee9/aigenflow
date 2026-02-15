"""
Claude.ai Reproducibility Test - Using PoC (simple) approach.
This matches the successful PoC pattern exactly.
"""

import asyncio
import hashlib
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

PROFILE_DIR = Path.home() / ".aigenflow" / "profiles"
BROWSER_CHANNEL = "chrome"

# Test prompt
PROMPT = """AI 기반 스마트폰 관리 시스템에 대한 창의적인 아이디어 2개를 제안해주세요.
각 아이디어는 1-2문장으로 설명해주세요.

답변은 한국어로 작성해주세요."""


def calculate_similarity(text1: str, text2: str) -> dict:
    """Calculate similarity between texts."""
    len1, len2 = len(text1), len(text2)
    len_sim = min(len1, len2) / max(len1, len2) if max(len1, len2) > 0 else 1.0

    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    jaccard = len(words1 & words2) / len(words1 | words2) if (words1 or words2) else 1.0

    sample_size = min(500, len(text1), len(text2))
    sample1, sample2 = text1[:sample_size], text2[:sample_size]
    char_match = sum(c1 == c2 for c1, c2 in zip(sample1, sample2)) / sample_size if sample_size > 0 else 1.0

    hash_match = 1.0 if hashlib.md5(text1.encode()).hexdigest() == hashlib.md5(text2.encode()).hexdigest() else 0.0

    return {
        "length_similarity": len_sim,
        "jaccard_similarity": jaccard,
        "character_match": char_match,
        "hash_match": hash_match,
        "overall": (len_sim * 0.2 + jaccard * 0.4 + char_match * 0.3 + hash_match * 0.1),
    }


async def test_claude_reproducibility():
    """Test Claude reproducibility using PoC pattern."""
    profile_path = PROFILE_DIR / "claude"

    if not profile_path.exists():
        print("Claude profile not found. Run: python tests/poc_playwright.py setup claude")
        return None

    responses = []
    errors = []

    print("\n" + "="*60)
    print("CLAUDE REPRODUCIBILITY TEST (PoC Pattern)")
    print("="*60)

    # Use exact PoC pattern - simple args
    args = ["--disable-blink-features=AutomationControlled"]

    for i in range(3):
        print(f"\nIteration {i+1}/3...")

        async with async_playwright() as p:
            # Exact PoC launch pattern
            context = await p.chromium.launch_persistent_context(
                str(profile_path),
                headless=False,
                channel=BROWSER_CHANNEL,
                viewport={"width": 1280, "height": 800},
                args=args,  # Only this arg, like PoC
            )
            page = context.pages[0] if context.pages else await context.new_page()

            try:
                print("  Navigating to claude.ai...")
                await page.goto("https://claude.ai", wait_until="domcontentloaded", timeout=30000)

                # Check for login
                current_url = page.url
                if "login" in current_url.lower():
                    print("  ✗ Not logged in")
                    await context.close()
                    return None

                print("  Session valid ✓")
                await asyncio.sleep(2)

                # Find input - use simple selector
                print("  Finding input field...")
                await page.wait_for_selector("[contenteditable='true']", timeout=10000)

                editable = await page.query_selector("[contenteditable='true']")
                if not editable:
                    errors.append(f"Iteration {i+1}: No input field found")
                    print("  ✗ No input field")
                    await context.close()
                    continue

                # Type message
                print("  Typing message...")
                await editable.fill(PROMPT)
                await asyncio.sleep(1)

                # Submit
                await editable.press("Enter")
                print("  Message sent, waiting for response...")

                # Wait for response
                await asyncio.sleep(20)

                # Capture response - try multiple selectors
                print("  Capturing response...")
                selectors = [
                    "div[data-testid='message-content']",
                    "div[data-message-author-role='assistant']",
                    "article[class*='message']",
                    "[class*='assistant']",
                ]

                captured = False
                for selector in selectors:
                    if captured:
                        break
                    try:
                        elements = await page.query_selector_all(selector)
                        if elements and len(elements) > 0:
                            # Get last substantial message
                            for elem in reversed(elements[-3:]):
                                text = await elem.inner_text()
                                if len(text) > 30:
                                    responses.append({
                                        "iteration": i + 1,
                                        "content": text,
                                        "length": len(text),
                                        "hash": hashlib.md5(text.encode()).hexdigest(),
                                    })
                                    print(f"  ✓ Captured: {len(text)} chars (selector: {selector})")
                                    captured = True
                                    break
                    except:
                        continue

                if not captured:
                    # Last resort - get page text
                    try:
                        body_text = await page.inner_text("body")
                        if body_text and len(body_text) > 100:
                            # Find last occurrence of Korean text or substantial content
                            lines = body_text.split("\n")
                            content_lines = []
                            for line in reversed(lines[-50:]):
                                if len(line) > 20:
                                    content_lines.insert(0, line)
                                    if len("\n".join(content_lines)) > 50:
                                        break

                            if content_lines:
                                content = "\n".join(content_lines)
                                responses.append({
                                    "iteration": i + 1,
                                    "content": content,
                                    "length": len(content),
                                    "hash": hashlib.md5(content.encode()).hexdigest(),
                                })
                                print(f"  ✓ Captured from body: {len(content)} chars")
                                captured = True
                    except:
                        pass

                if not captured:
                    errors.append(f"Iteration {i+1}: No response captured")
                    print("  ✗ No response captured")

            except Exception as e:
                errors.append(f"Iteration {i+1}: {str(e)}")
                print(f"  ✗ Error: {e}")

            await context.close()

    # Calculate similarities
    if len(responses) >= 2:
        print("\n  Calculating similarities...")
        similarities = []
        for i in range(len(responses) - 1):
            sim = calculate_similarity(responses[i]["content"], responses[i+1]["content"])
            similarities.append(sim)
            print(f"  Response {i+1} vs {i+2}: {sim['overall']*100:.1f}%")

        avg_sim = {
            "length": sum(s["length_similarity"] for s in similarities) / len(similarities),
            "jaccard": sum(s["jaccard_similarity"] for s in similarities) / len(similarities),
            "character": sum(s["character_match"] for s in similarities) / len(similarities),
            "hash": sum(s["hash_match"] for s in similarities) / len(similarities),
            "overall": sum(s["overall"] for s in similarities) / len(similarities),
        }

        return {
            "provider": "claude",
            "responses": responses,
            "errors": errors,
            "similarities": similarities,
            "avg_similarity": avg_sim,
        }

    return None


async def main():
    """Main function."""
    result = await test_claude_reproducibility()

    if result and "avg_similarity" in result:
        print("\n" + "="*60)
        print("RESULTS")
        print("="*60)
        print(f"Responses: {len(result['responses'])}/3")
        print(f"Overall similarity: {result['avg_similarity']['overall']*100:.1f}%")

        # Save result
        report_path = Path("docs/ai-reproducibility-results/actual/claude-result.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        import json
        report_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nResult saved to: {report_path}")
    else:
        print("\nTest failed or insufficient responses")


if __name__ == "__main__":
    asyncio.run(main())
