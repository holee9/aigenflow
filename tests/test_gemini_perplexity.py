"""
Gemini & Perplexity Reproducibility Test
Simple approach using PoC pattern.
"""

import asyncio
import hashlib
import json
from datetime import datetime
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

                editor = await page.query_selector(".ql-editor, textarea")
                if not editor:
                    print("  No editor found")
                    await context.close()
                    continue

                await editor.fill(PROMPT)
                await asyncio.sleep(1)
                await editor.press("Enter")
                print("  Message sent, waiting...")
                await asyncio.sleep(20)

                # Capture response
                selectors = ["div.model-response", "markdown", "div[data-test-id='chat-turn']"]
                captured = False

                for selector in selectors:
                    if captured:
                        break
                    try:
                        elements = await page.query_selector_all(selector)
                        if elements:
                            text = await elements[-1].inner_text()
                            if len(text) > 30:
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

        return {
            "provider": "gemini",
            "responses": responses,
            "errors": errors,
            "similarities": similarities,
            "avg_similarity": avg_sim,
        }

    return None


async def test_perplexity():
    profile_path = PROFILE_DIR / "perplexity"

    if not profile_path.exists():
        print("Perplexity profile not found")
        return None

    responses = []
    errors = []

    print("\n" + "="*60)
    print("PERPLEXITY REPRODUCIBILITY TEST")
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
                await page.goto("https://www.perplexity.ai", wait_until="domcontentloaded", timeout=30000)

                if "login" in page.url.lower():
                    print("  Not logged in")
                    await context.close()
                    return None

                print("  Finding input...")
                await page.wait_for_selector("[role='textbox'], textarea", timeout=15000)

                textbox = await page.query_selector("[role='textbox'], textarea")
                if not textbox:
                    print("  No textbox found")
                    await context.close()
                    continue

                await textbox.fill(PROMPT)
                await asyncio.sleep(1)
                await textbox.press("Enter")
                print("  Message sent, waiting...")
                await asyncio.sleep(20)

                # Capture response
                selectors = ["div.thread-message", "div[class*='answer']"]
                captured = False

                for selector in selectors:
                    if captured:
                        break
                    try:
                        elements = await page.query_selector_all(selector)
                        if elements:
                            text = await elements[-1].inner_text()
                            if len(text) > 30:
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

        return {
            "provider": "perplexity",
            "responses": responses,
            "errors": errors,
            "similarities": similarities,
            "avg_similarity": avg_sim,
        }

    return None


def generate_report(results: list) -> str:
    lines = []
    lines.append("# Gemini & Perplexity 재현성 평가 보고서")
    lines.append("")
    lines.append(f"**평가 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**반복 횟수**: 3회")
    lines.append("")

    lines.append("## 1. 평가 개요")
    lines.append("")
    lines.append("| AI | 상태 | 성공 | 평균 유사도 |")
    lines.append("|----|------|------|-----------|")

    for r in results:
        if r and "avg_similarity" in r:
            status = "완료"
            success = f"{len(r['responses'])}/3"
            avg_sim = f"{r['avg_similarity']['overall']*100:.1f}%"
        else:
            status = "실패"
            success = "0/3"
            avg_sim = "N/A"

        lines.append(f"| {r['provider']} | {status} | {success} | {avg_sim} |")

    lines.append("")

    lines.append("## 2. 상세 결과")
    lines.append("")

    for r in results:
        if r:
            lines.append(f"### {r['provider'].upper()}")
            lines.append("")

            if r.get("responses"):
                lines.append("**응답 요약**:")
                for resp in r["responses"]:
                    preview = resp["content"][:100].replace("\n", " ")
                    lines.append(f"  - 반복 {resp['iteration']}: {resp['length']}자")
                    lines.append(f"    내용: {preview}...")

            if "avg_similarity" in r:
                avg = r["avg_similarity"]
                lines.append("")
                lines.append("**유사도 분석**:")
                lines.append(f"- 종합 유사도: {avg['overall']*100:.1f}%")

            lines.append("")

    lines.append("*보고서 생성일: " + datetime.now().strftime('%Y-%m-%d %H:%M'))

    return "\n".join(lines)


async def main():
    print("\n" + "="*60)
    print("GEMINI & PERPLEXITY REPRODUCIBILITY TEST")
    print("="*60)

    results = []

    # Test Gemini
    gemini_result = await test_gemini()
    if gemini_result:
        results.append(gemini_result)

    # Test Perplexity
    perplexity_result = await test_perplexity()
    if perplexity_result:
        results.append(perplexity_result)

    # Generate report
    if results:
        report = generate_report(results)
        report_path = Path("docs/ai-reproducibility-results/actual/gemini-perplexity-report.md")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding="utf-8")

        print(f"\n" + "="*60)
        print(f"Report saved: {report_path}")
        print("="*60)

        # Save JSON
        for r in results:
            json_path = Path(f"docs/ai-reproducibility-results/actual/{r['provider']}-result.json")
            json_path.write_text(json.dumps(r, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"JSON saved: {json_path}")


if __name__ == "__main__":
    asyncio.run(main())
