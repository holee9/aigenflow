"""
ChatGPT Reproducibility Test
"""

import asyncio
import hashlib
import json
from pathlib import Path
from playwright.async_api import async_playwright

PROFILE_DIR = Path.home() / ".aigenflow" / "profiles"
BROWSER_CHANNEL = "chrome"

PROMPT = """AI 기반 스마트폰 관리 시스템에 대한 창의적인 아이디어 2개를 제안해주세요.
각 아이디어는 1-2문장으로 설명해주세요.

답변은 한국어로 작성해주세요."""


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


async def test_chatgpt():
    profile_path = PROFILE_DIR / "chatgpt"

    if not profile_path.exists():
        print("ChatGPT profile not found")
        return None

    responses = []
    errors = []

    print("\n" + "="*60)
    print("CHATGPT REPRODUCIBILITY TEST")
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
                await page.goto("https://chat.openai.com", wait_until="domcontentloaded", timeout=30000)

                if "login" in page.url.lower():
                    print("  Not logged in")
                    await context.close()
                    return None

                print("  Finding input...")
                await page.wait_for_selector("#prompt-textarea, textarea", timeout=15000)

                textarea = await page.query_selector("#prompt-textarea, textarea")
                if not textarea:
                    print("  No textarea found")
                    await context.close()
                    continue

                await textarea.fill(PROMPT)
                await asyncio.sleep(1)

                # Submit with Enter
                await textarea.press("Enter")
                print("  Message sent, waiting...")
                await asyncio.sleep(20)

                # Capture response
                selectors = [
                    "div[data-message-author-role='assistant']",
                    "article[data-message-author-role='assistant']",
                    "div[class*='assistant']",
                    "[class*='markdown']",
                ]
                captured = False

                for selector in selectors:
                    if captured:
                        break
                    try:
                        elements = await page.query_selector_all(selector)
                        if elements and len(elements) > 0:
                            # Get last assistant message
                            text = await elements[-1].inner_text()
                            # Filter out system messages
                            if (len(text) > 30 and
                                "ChatGPT" not in text[:20] and
                                "OpenAI" not in text[:20]):
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
                    # Fallback to body text
                    body_text = await page.inner_text("body")
                    lines = body_text.split("\n")
                    content_lines = []
                    for line in reversed(lines[-100:]):
                        if len(line) > 20:
                            content_lines.insert(0, line)
                            if len("\n".join(content_lines)) > 100:
                                break

                    if content_lines:
                        content = "\n".join(content_lines)
                        responses.append({
                            "iteration": i + 1,
                            "content": content,
                            "length": len(content),
                            "hash": hashlib.md5(content.encode()).hexdigest(),
                        })
                        print(f"  Captured from body: {len(content)} chars")
                    else:
                        errors.append(f"Iteration {i+1}: No response")
                        print("  No response captured")

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
            "provider": "chatgpt",
            "responses": responses,
            "errors": errors,
            "similarities": similarities,
            "avg_similarity": avg_sim,
        }

        # Save result
        json_path = Path("docs/ai-reproducibility-results/actual/chatgpt-result.json")
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nResult saved to: {json_path}")

        return result

    return None


async def main():
    result = await test_chatgpt()

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
