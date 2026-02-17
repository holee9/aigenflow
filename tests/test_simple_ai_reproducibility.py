"""
Simple AI Reproducibility Test using PoC method.
Direct Playwright approach without provider abstraction.
"""

import asyncio
import hashlib
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright

PROFILE_DIR = Path.home() / ".aigenflow" / "profiles"
BROWSER_CHANNEL = "chrome"


class SimpleAIReproducibilityTest:
    """Simple direct Playwright test for AI reproducibility."""

    def __init__(self):
        self.iterations = 3

    def get_test_prompt(self) -> str:
        """Simple test prompt."""
        return """AI 기반 스마트폰 관리 시스템에 대한 창의적인 아이디어 2개를 제안해주세요.
각 아이디어는 1-2문장으로 설명해주세요.

답변은 한국어로 작성해주세요."""

    def calculate_similarity(self, text1: str, text2: str) -> dict:
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

    async def test_single_ai_simple(self, provider: str, url: str, selector: str, prompt: str) -> dict:
        """Test single AI with direct Playwright."""
        print(f"\n{'='*60}")
        print(f"Testing {provider.upper()}")
        print(f"{'='*60}")

        result = {
            "provider": provider,
            "iterations": self.iterations,
            "responses": [],
            "success_count": 0,
            "errors": [],
        }

        profile_path = PROFILE_DIR / provider

        if not profile_path.exists():
            result["status"] = "no_profile"
            result["error"] = f"No profile found at {profile_path}"
            return result

        try:
            async with async_playwright() as p:
                context = await p.chromium.launch_persistent_context(
                    str(profile_path),
                    headless=False,  # Use headed to see progress
                    channel=BROWSER_CHANNEL,
                    viewport={"width": 1280, "height": 800},
                    args=["--disable-blink-features=AutomationControlled"],
                )
                page = context.pages[0] if context.pages else await context.new_page()

                # Navigate to AI service
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)

                # Quick session check
                current_url = page.url
                is_login = any(kw in current_url.lower() for kw in ["login", "signin", "auth"])

                if is_login:
                    result["status"] = "not_logged_in"
                    result["error"] = "Login required"
                    await context.close()
                    return result

                print("  Session validated ✓")

                # Send messages
                for i in range(self.iterations):
                    try:
                        print(f"  Message {i+1}/{self.iterations}...", end="", flush=True)

                        # Wait for input selector
                        await page.wait_for_selector(selector, timeout=10000)

                        # Type prompt
                        await page.fill(selector, prompt)
                        await asyncio.sleep(1)  # Brief pause

                        # Submit
                        await page.press(selector, "Enter")
                        print(" sent", end="", flush=True)

                        # Wait for response - longer wait for AI generation
                        print(" waiting...", end="", flush=True)
                        await asyncio.sleep(15)  # Wait 15 seconds for AI response

                        # Capture response with multiple fallback selectors
                        await asyncio.sleep(3)  # Additional wait for rendering

                        # Enhanced response capture with multiple selectors
                        captured = False

                        # Try multiple selectors per provider
                        if provider == "claude":
                            selectors = [
                                "div[data-testid='message-content']",
                                "div[data-message-author-role='assistant']",
                                "article[class*='message']",
                                ".font-claude-message",
                                "[class*='assistant']",
                            ]
                        elif provider == "gemini":
                            selectors = [
                                "div.model-response",
                                "div[data-test-id='chat-turn']",
                                "markdown",
                                ".text-content",
                                "[class*='response']",
                            ]
                        elif provider == "perplexity":
                            selectors = [
                                "div.thread-message",
                                "div[class*='answer']",
                                "div[class*='prose']",
                                "[class*='response']",
                            ]
                        else:
                            selectors = ["*"]

                        # Try each selector
                        for selector in selectors:
                            if captured:
                                break
                            try:
                                elements = await page.query_selector_all(selector)
                                if elements:
                                    # Get last substantial message
                                    for elem in reversed(elements[-5:]):  # Check last 5
                                        try:
                                            text = await elem.inner_text()
                                            # Filter out user messages and empty content
                                            if len(text) > 30 and "You" not in text[:50]:
                                                result["responses"].append({
                                                    "iteration": i + 1,
                                                    "content": text,
                                                    "length": len(text),
                                                    "hash": hashlib.md5(text.encode()).hexdigest(),
                                                })
                                                result["success_count"] += 1
                                                print(f" ✓ {len(text)} chars")
                                                captured = True
                                                break
                                        except:
                                            continue
                            except:
                                continue

                        if not captured and len(result["responses"]) <= i:
                            result["errors"].append(f"Iteration {i+1}: No content captured")
                            print(" ✗ No content")

                    except Exception as e:
                        result["errors"].append(f"Iteration {i+1}: {str(e)}")
                        print(f" ✗ Error: {e}")

                await context.close()

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            print(f"  Error: {e}")
            return result

        # Calculate similarities
        if len(result["responses"]) >= 2:
            print("\n  Calculating similarities...")
            similarities = []
            hashes = [r["hash"] for r in result["responses"]]

            for i in range(len(result["responses"]) - 1):
                sim = self.calculate_similarity(
                    result["responses"][i]["content"],
                    result["responses"][i+1]["content"]
                )
                similarities.append(sim)
                print(f"    Response {i+1} vs {i+2}: {sim['overall']*100:.1f}%")

            result["similarities"] = similarities
            result["unique_hashes"] = len(set(hashes))
            result["total_hashes"] = len(hashes)

            result["avg_similarity"] = {
                "length": sum(s["length_similarity"] for s in similarities) / len(similarities),
                "jaccard": sum(s["jaccard_similarity"] for s in similarities) / len(similarities),
                "character": sum(s["character_match"] for s in similarities) / len(similarities),
                "hash": sum(s["hash_match"] for s in similarities) / len(similarities),
                "overall": sum(s["overall"] for s in similarities) / len(similarities),
            }

        result["status"] = "completed" if result["success_count"] > 0 else "failed"
        return result

    async def run_test(self) -> list:
        """Run reproducibility test."""
        prompt = self.get_test_prompt()

        print(f"\n{'='*60}")
        print("SIMPLE AI REPRODUCIBILITY TEST")
        print(f"{'='*60}")
        print(f"Iterations: {self.iterations}")
        print(f"Prompt: {len(prompt)} chars")
        print(f"{'='*60}")

        # Test only logged-in AIs (from PoC verification)
        tests = [
            ("claude", "https://claude.ai", "div[contenteditable='true'], [contenteditable='true']"),
            ("gemini", "https://gemini.google.com", ".ql-editor"),
            ("perplexity", "https://www.perplexity.ai", "[role='textbox']"),
        ]

        results = []

        for provider, url, selector in tests:
            result = await self.test_single_ai_simple(provider, url, selector, prompt)
            results.append(result)

        return results

    def generate_report(self, results: list) -> str:
        """Generate test report."""
        lines = []
        lines.append("# 실제 AI 응답 재현성 평가 보고서")
        lines.append("")
        lines.append(f"**평가 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("**평가 방식**: Playwright 직접 접속 (PoC 방식)")
        lines.append(f"**반복 횟수**: {self.iterations}회")
        lines.append("")

        # Summary
        lines.append("## 1. 평가 개요")
        lines.append("")
        lines.append("| AI | 상태 | 성공 | 평균 길이 | 유사도 | 해시 |")
        lines.append("|----|------|------|----------|--------|------|")

        for r in results:
            if r["status"] == "completed" and "avg_similarity" in r:
                status = "✅ 완료"
                success = f"{r['success_count']}/{r['iterations']}"
                avg_len = f"{sum(resp['length'] for resp in r['responses']) / len(r['responses']):.0f}"
                avg_sim = f"{r['avg_similarity']['overall']*100:.1f}%"
                hash_info = f"{r['unique_hashes']}/{r['total_hashes']}"
            elif r["status"] == "not_logged_in":
                status = "❌ 로그인 필요"
                success = "0/0"
                avg_len = "N/A"
                avg_sim = "N/A"
                hash_info = "N/A"
            else:
                status = f"⚠️ {r.get('status', 'unknown')}"
                success = f"{r.get('success_count', 0)}/{r['iterations']}"
                avg_len = "N/A"
                avg_sim = "N/A"
                hash_info = "N/A"

            lines.append(f"| {r['provider']} | {status} | {success} | {avg_len} | {avg_sim} | {hash_info} |")

        lines.append("")

        # Detailed results
        lines.append("## 2. 상세 결과")
        lines.append("")

        for r in results:
            lines.append(f"### {r['provider'].upper()}")
            lines.append("")
            lines.append(f"- **상태**: {r['status']}")

            if r.get("errors"):
                lines.append(f"- **오류**: {', '.join(r['errors'])}")

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
                lines.append(f"- 해시 다양성: {r['unique_hashes']}/{r['total_hashes']}")

            lines.append("")

        # Overall assessment
        lines.append("## 3. 종합 평가")
        lines.append("")

        completed = [r for r in results if "avg_similarity" in r]
        failed = [r for r in results if "avg_similarity" not in r]

        if completed:
            overall_sim = sum(r["avg_similarity"]["overall"] for r in completed) / len(completed)
            lines.append(f"- **평가 완료**: {len(completed)}/{len(results)}개 AI")
            lines.append(f"- **평균 유사도**: {overall_sim*100:.1f}%")

            if overall_sim >= 0.9:
                grade = "A+"
                assessment = "매우 우수한 재현성 (결정론적 모드)"
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
            lines.append("**해석**:")
            lines.append(f"- 평균 재현성 {overall_sim*100:.1f}%는 ")
            if overall_sim >= 0.8:
                lines.append("  - AI 응답이 일관적이며 재현성이 높음")
                lines.append("  - Temperature 설정이 낮거나 결정론적 모드 사용")
            elif overall_sim >= 0.6:
                lines.append("  - AI 응답에 일부 변동성 있음")
                lines.append("  - 일관성과 창의성의 균형 유지")
            else:
                lines.append("  - AI 응답의 변동성이 큼")
                lines.append("  - 높은 창의성 설정 (Temperature > 0.7)")

        if failed:
            lines.append("")
            lines.append(f"- **실패/미완료**: {', '.join([r['provider'] for r in failed])}")

        lines.append("")
        lines.append("*보고서 생성일: " + datetime.now().strftime('%Y-%m-%d %H:%M') + "*")

        return "\n".join(lines)


async def main():
    """Main function."""
    tester = SimpleAIReproducibilityTest()

    try:
        results = await tester.run_test()
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        results = []

    # Generate report
    report = tester.generate_report(results)

    # Save report
    report_path = Path("docs/ai-reproducibility-results/actual/simple-reproducibility-test.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    print(f"\n{'='*60}")
    print(f"📄 보고서: {report_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
