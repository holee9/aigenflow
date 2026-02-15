"""
Gemini & Perplexity Reproducibility Test (Claude excluded due to auth issue).
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


async def test_gemini():
    """Test Gemini reproducibility (3 iterations)."""
    profile_path = PROFILE_DIR / "gemini"

    if not profile_path.exists():
        print("Gemini profile not found")
        return None

    responses = []
    errors = []

    print("\n" + "="*60)
    print("Testing GEMINI")
    print("="*60)

    async with async_playwright() as p:
        for i in range(3):
            context = await p.chromium.launch_persistent_context(
                str(profile_path),
                headless=False,
                channel=BROWSER_CHANNEL,
                viewport={"width": 1280, "height": 800},
                args=["--disable-blink-features=AutomationControlled"],
            )
            page = context.pages[0] if context.pages else await context.new_page()

            try:
                await page.goto("https://gemini.google.com", wait_until="domcontentloaded", timeout=30000)

                # Check login
                if "login" in page.url.lower():
                    print(f"  Message {i+1}/3: ✗ Not logged in")
                    await context.close()
                    return None

                print(f"  Message {i+1}/3...")

                # Wait for input
                await page.wait_for_selector(".ql-editor, textarea", timeout=15000)

                # Get the editor element
                editor = await page.query_selector(".ql-editor, textarea")
                if not editor:
                    errors.append(f"Message {i+1}: No editor found")
                    print(f"    ✗ No editor found")
                    await context.close()
                    continue

                # Type message
                await editor.fill(PROMPT)
                await asyncio.sleep(1)

                # Submit
                await editor.press("Enter")
                print("    sent, waiting...", end="", flush=True)

                # Wait for response
                await asyncio.sleep(20)

                # Capture response - try multiple selectors
                captured = False
                selectors = [
                    "div.model-response",
                    "markdown",
                    "div[data-test-id='chat-turn']",
                ]

                for selector in selectors:
                    if captured:
                        break
                    try:
                        elements = await page.query_selector_all(selector)
                        if elements:
                            # Get last response
                            text = await elements[-1].inner_text()
                            if len(text) > 30:
                                responses.append({
                                    "iteration": i + 1,
                                    "content": text,
                                    "length": len(text),
                                    "hash": hashlib.md5(text.encode()).hexdigest(),
                                })
                                print(f" ✓ {len(text)} chars")
                                captured = True
                                break
                    except:
                        continue

                if not captured:
                    errors.append(f"Message {i+1}: No response captured")
                    print(" ✗ No response captured")

            except Exception as e:
                errors.append(f"Message {i+1}: {str(e)}")
                print(f"    ✗ Error: {e}")

            await context.close()

    # Calculate similarities
    if len(responses) >= 2:
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
    """Test Perplexity reproducibility (3 iterations)."""
    profile_path = PROFILE_DIR / "perplexity"

    if not profile_path.exists():
        print("Perplexity profile not found")
        return None

    responses = []
    errors = []

    print("\n" + "="*60)
    print("Testing PERPLEXITY")
    print("="*60)

    async with async_playwright() as p:
        for i in range(3):
            context = await p.chromium.launch_persistent_context(
                str(profile_path),
                headless=False,
                channel=BROWSER_CHANNEL,
                viewport={"width": 1280, "height": 800"},
                args=["--disable-blink-features=AutomationControlled"],
            )
            page = context.pages[0] if context.pages else await context.new_page()

            try:
                await page.goto("https://www.perplexity.ai", wait_until="domcontentloaded", timeout=30000)

                # Check login
                if "login" in page.url.lower():
                    print(f"  Message {i+1}/3: ✗ Not logged in")
                    await context.close()
                    return None

                print(f"  Message {i+1}/3...")

                # Wait for input
                await page.wait_for_selector("[role='textbox'], textarea", timeout=15000)

                # Get the input element
                textbox = await page.query_selector("[role='textbox'], textarea")
                if not textbox:
                    errors.append(f"Message {i+1}: No textbox found")
                    print(f"    ✗ No textbox found")
                    await context.close()
                    continue

                # Type message
                await textbox.fill(PROMPT)
                await asyncio.sleep(1)

                # Submit
                await textbox.press("Enter")
                print("    sent, waiting...", end="", flush=True)

                # Wait for response
                await asyncio.sleep(20)

                # Capture response - try multiple selectors
                captured = False
                selectors = [
                    "div.thread-message",
                    "div[class*='answer']",
                    "div[class*='prose']",
                ]

                for selector in selectors:
                    if captured:
                        break
                    try:
                        elements = await page.query_selector_all(selector)
                        if elements:
                            # Get last response
                            text = await elements[-1].inner_text()
                            if len(text) > 30:
                                responses.append({
                                    "iteration": i + 1,
                                    "content": text,
                                    "length": len(text),
                                    "hash": hashlib.md5(text.encode()).hexdigest(),
                                })
                                print(f" ✓ {len(text)} chars")
                                captured = True
                                break
                    except:
                        continue

                if not captured:
                    errors.append(f"Message {i+1}: No response captured")
                    print(" ✗ No response captured")

            except Exception as e:
                errors.append(f"Message {i+1}: {str(e)}")
                print(f"    ✗ Error: {e}")

            await context.close()

    # Calculate similarities
    if len(responses) >= 2:
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
    """Generate test report."""
    lines = []
    lines.append("# Gemini & Perplexity 재현성 평가 보고서")
    lines.append("")
    lines.append(f"**평가 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**평가 방식**: Playwright 웹 브라우저 접속")
    lines.append(f"**반복 횟수**: 3회")
    lines.append(f"**참고**: Claude는 인증 문제로 제외")
    lines.append("")

    # Summary
    lines.append("## 1. 평가 개요")
    lines.append("")
    lines.append("| AI | 상태 | 성공 | 평균 유사도 |")
    lines.append("|----|------|------|-----------|")

    for r in results:
        if r and "avg_similarity" in r:
            status = "✅ 완료"
            success = f"{len(r['responses'])}/3"
            avg_sim = f"{r['avg_similarity']['overall']*100:.1f}%"
        elif r and r.get("responses"):
            status = "⚠️ 부분 완료"
            success = f"{len(r['responses'])}/3"
            avg_sim = "N/A (응답 < 2)"
        else:
            status = "❌ 실패"
            success = "0/3"
            avg_sim = "N/A"

        lines.append(f"| {r['provider']} | {status} | {success} | {avg_sim} |")

    lines.append("")

    # Detailed results
    lines.append("## 2. 상세 결과")
    lines.append("")

    for r in results:
        if r:
            lines.append(f"### {r['provider'].upper()}")
            lines.append("")
            lines.append(f"- **상태**: {'완료' if len(r.get('responses', [])) >= 2 else '부분 완료' if r.get('responses') else '실패'}")

            if r.get("errors"):
                lines.append(f"- **오류**: {', '.join(r['errors'][:3])}")  # First 3 errors

            if r.get("responses"):
                lines.append("")
                lines.append("**응답 요약**:")
                for resp in r["responses"]:
                    preview = resp["content"][:100].replace("\n", " ")
                    lines.append(f"  - 반복 {resp['iteration']}: {resp['length']}자, 해시={resp['hash'][:12]}...")
                    lines.append(f"    내용: {preview}...")

            if "avg_similarity" in r:
                avg = r["avg_similarity"]
                lines.append("")
                lines.append("**유사도 분석**:")
                lines.append(f"- 길이 유사도: {avg['length']*100:.1f}%")
                lines.append(f"- 단어 중첩도: {avg['jaccard']*100:.1f}%")
                lines.append(f"- 문자 일치: {avg['character']*100:.1f}%")
                lines.append(f"- 해시 일치: {avg['hash']*100:.1f}%")
                lines.append(f"- **종합 유사도: {avg['overall']*100:.1f}%**")

            lines.append("")

    # Overall assessment
    lines.append("## 3. 종합 평가")
    lines.append("")

    completed = [r for r in results if r and "avg_similarity" in r]

    if completed:
        overall_sim = sum(r["avg_similarity"]["overall"] for r in completed) / len(completed)
        lines.append(f"- **평가 완료**: {len(completed)}/{len(results)}개 AI")
        lines.append(f"- **평균 유사도**: {overall_sim*100:.1f}%")

        if overall_sim >= 0.9:
            grade = "A+"
            assessment = "매우 우수한 재현성"
        elif overall_sim >= 0.8:
            grade = "A"
            assessment = "우수한 재현성"
        elif overall_sim >= 0.7:
            grade = "B"
            assessment = "양호한 재현성"
        elif overall_sim >= 0.5:
            grade = "C"
            assessment = "보통 수준"
        else:
            grade = "D"
            assessment = "개선 필요"

        lines.append(f"- **품질 등급**: {grade} ({assessment})")

    lines.append("")
    lines.append("**참고**:")
    lines.append("- Claude.ai는 인증 확인 창 무한 반복 문제로 제외")
    lines.append("- Claude 인증 해결 후 별도 평가 필요")
    lines.append("")
    lines.append("*보고서 생성일: " + datetime.now().strftime('%Y-%m-%d %H:%M'))

    return "\\n".join(lines)


async def main():
    """Main function."""
    print("\n" + "="*60)
    print("GEMINI & PERPLEXITY REPRODUCIBILITY TEST")
    print("="*60)
    print("\\nClaude excluded due to auth issue")
    print("Testing Gemini and Perplexity...\\n")

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
        report_path = Path("docs/ai-reproducibility-results/actual/gemini-perplexity-reproducibility.md")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding="utf-8")

        print(f"\n{'='*60}")
        print(f"📄 보고서: {report_path}")
        print(f"{'='*60}")
    else:
        print("\\nNo successful tests completed.")


if __name__ == "__main__":
    asyncio.run(main())
