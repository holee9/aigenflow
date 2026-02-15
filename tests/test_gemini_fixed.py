"""
Gemini Reproducibility Test - Fixed DOM issue
"""

import asyncio
import hashlib
from pathlib import Path
from playwright.async_api import async_playwright

PROFILE_DIR = Path.home() / ".aigenflow" / "profiles"
BROWSER_CHANNEL = "chrome"

PROMPT = """What are 2 healthy breakfast ideas? Keep it brief.
Respond in Korean."""


def calculate_similarity(text1: str, text2: str) -> dict:
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


async def test_gemini():
    profile_path = PROFILE_DIR / "gemini"

    if not profile_path.exists():
        print("Gemini profile not found")
        return None

    responses = []
    errors = []

    print("\n" + "="*60)
    print("GEMINI REPRODUCIBILITY TEST")
    print("="*60)

    args = ["--disable-blink-features=AutomationControlled"]

    for i in range(3):
        print(f"\nIteration {i+1}/3...")

        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                str(profile_path),
                headless=False,
                channel=BROWSER_CHANNEL,
                viewport={"width": 1280, "height": 800},
                args=args,
            )
            page = context.pages[0] if context.pages else await context.new_page()

            try:
                await page.goto("https://gemini.google.com", wait_until="domcontentloaded", timeout=30000)

                if "login" in page.url.lower():
                    print("  Not logged in")
                    await context.close()
                    return None

                print("  Finding input...")
                await page.wait_for_selector(".ql-editor, textarea", timeout=15000)

                # FIX: Re-query element before press
                editor = await page.query_selector(".ql-editor, textarea")
                if not editor:
                    print("  No editor found")
                    await context.close()
                    continue

                # Type and submit using page.press directly
                await editor.fill(PROMPT)
                await asyncio.sleep(1)

                # FIX: Use page.press with selector to avoid stale element
                try:
                    await page.press(".ql-editor, textarea", "Enter")
                except:
                    # Fallback to keyboard
                    await page.keyboard.press("Enter")

                print("  Message sent, waiting...")
                await asyncio.sleep(20)

                # Capture response - try to find actual response, not safety message
                await asyncio.sleep(5)  # Extra wait for full rendering

                selectors = [
                    "div.model-response",
                    "markdown",
                    "div[data-test-id='chat-turn']",
                    "div[class*='response']",
                ]
                captured = False

                for selector in selectors:
                    if captured:
                        break
                    try:
                        elements = await page.query_selector_all(selector)
                        if elements and len(elements) > 0:
                            # Check ALL elements, not just last one
                            for elem in elements:
                                text = await elem.inner_text()
                                # Filter out safety messages
                                if (len(text) > 30 and
                                    "AI이며" not in text and
                                    "realize" not in text and
                                    "실수" not in text and
                                    "Gemini는 AI이며" not in text):
                                    responses.append({
                                        "iteration": i + 1,
                                        "content": text,
                                        "length": len(text),
                                        "hash": hashlib.md5(text.encode()).hexdigest(),
                                    })
                                    print(f"  Captured: {len(text)} chars")
                                    captured = True
                                    break
                    except:
                        continue

                if not captured:
                    # Last resort - get all text and filter
                    body_text = await page.inner_text("body")
                    # Find longest text that's not safety message
                    candidates = []
                    for line in body_text.split("\n"):
                        if len(line) > 50 and "AI이며" not in line and "실수" not in line:
                            candidates.append(line)

                    if candidates:
                        # Take longest candidate
                        content = max(candidates, key=len)
                        responses.append({
                            "iteration": i + 1,
                            "content": content,
                            "length": len(content),
                            "hash": hashlib.md5(content.encode()).hexdigest(),
                        })
                        print(f"  Captured from candidates: {len(content)} chars")
                    else:
                        errors.append(f"Iteration {i+1}: Only safety message captured")
                        print("  Only safety message found")

            except Exception as e:
                errors.append(f"Iteration {i+1}: {e}")
                print(f"  Error: {e}")

            await context.close()

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

        result = {
            "provider": "gemini",
            "responses": responses,
            "errors": errors,
            "similarities": similarities,
            "avg_similarity": avg_sim,
        }

        # Save result
        import json
        json_path = Path("docs/ai-reproducibility-results/actual/gemini-result.json")
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nResult saved to: {json_path}")

        return result

    return None


async def main():
    result = await test_gemini()

    if result and "avg_similarity" in result:
        print("\n" + "="*60)
        print("RESULTS")
        print("="*60)
        print(f"Responses: {len(result['responses'])}/3")
        print(f"Overall similarity: {result['avg_similarity']['overall']*100:.1f}%")
    else:
        print("\nTest failed")


if __name__ == "__main__":
    asyncio.run(main())
