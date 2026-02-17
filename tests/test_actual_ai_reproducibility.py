"""
Actual AI Response Reproducibility Test (3 iterations).
Tests Claude, Gemini, Perplexity (already logged in).
"""

import asyncio
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright

PROFILE_DIR = Path.home() / ".aigenflow" / "profiles"
BROWSER_CHANNEL = "chrome"


class ActualAIReproducibilityTest:
    """Test actual AI response reproducibility."""

    def __init__(self):
        self.iterations = 3
        self.results = []

    def get_test_prompt(self) -> str:
        """Test prompt for AI."""
        return """You are an AI assistant specializing in business ideation.

Please provide 2-3 creative business ideas for the following topic:

"AI-based smartphone management systems"

Respond in Korean. Keep it brief (3-5 sentences total)."""

    def calculate_similarity(self, text1: str, text2: str) -> dict[str, float]:
        """Calculate similarity between responses."""
        # Length similarity
        len1, len2 = len(text1), len(text2)
        len_sim = min(len1, len2) / max(len1, len2) if max(len1, len2) > 0 else 1.0

        # Word overlap (Jaccard)
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if words1 or words2:
            jaccard = len(words1 & words2) / len(words1 | words2)
        else:
            jaccard = 1.0

        # Character match
        sample_size = min(500, len(text1), len(text2))
        sample1, sample2 = text1[:sample_size], text2[:sample_size]
        char_match = sum(c1 == c2 for c1, c2 in zip(sample1, sample2)) / sample_size if sample_size > 0 else 1.0

        # Hash match
        hash_match = 1.0 if hashlib.md5(text1.encode()).hexdigest() == hashlib.md5(text2.encode()).hexdigest() else 0.0

        return {
            "length_similarity": len_sim,
            "jaccard_similarity": jaccard,
            "character_match": char_match,
            "hash_match": hash_match,
            "overall_score": (len_sim * 0.2 + jaccard * 0.4 + char_match * 0.3 + hash_match * 0.1),
        }

    async def test_single_ai(self, provider: str, url: str, prompt: str, selector: str) -> dict[str, Any]:
        """Test single AI provider reproducibility."""
        print(f"\n{'='*60}")
        print(f"Testing {provider.upper()}")
        print(f"{'='*60}")

        result = {
            "provider": provider,
            "iterations": self.iterations,
            "responses": [],
            "errors": [],
            "success_count": 0,
        }

        profile_path = PROFILE_DIR / provider

        if not profile_path.exists():
            result["status"] = "no_profile"
            result["error"] = "No profile directory found"
            return result

        try:
            async with async_playwright() as p:
                context = await p.chromium.launch_persistent_context(
                    str(profile_path),
                    headless=False,  # Use headed to avoid blocking
                    channel=BROWSER_CHANNEL,
                    viewport={"width": 1280, "height": 800},
                    args=["--disable-blink-features=AutomationControlled"],
                )
                page = context.pages[0] if context.pages else await context.new_page()

                # Navigate to AI service
                print(f"  Navigating to {url}...")
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)

                # Check session
                current_url = page.url
                is_login = any(kw in current_url.lower() for kw in ["login", "signin", "auth"])

                if is_login:
                    result["status"] = "not_logged_in"
                    result["error"] = "Login required"
                    await context.close()
                    return result

                # Send messages
                for i in range(self.iterations):
                    try:
                        print(f"  Sending message {i+1}/{self.iterations}...", end=" ", flush=True)

                        # Wait for page to be ready
                        await page.wait_for_selector(selector, timeout=10000)

                        # Type message
                        start_time = datetime.now()
                        await page.fill(selector, prompt, timeout=5000)

                        # Submit (send by pressing Enter)
                        await page.press(selector, "Enter")

                        # Wait for response
                        await page.wait_for_timeout(8000)  # Wait 8 seconds for response

                        # Get response (implementation varies by AI)
                        if provider == "claude":
                            # Claude: Wait for response to appear
                            try:
                                await page.wait_for_selector("div[data-testid='message-content']", timeout=15000)
                                elements = await page.query_selector_all("div[data-testid='message-content']")
                                # Get the last message (AI response)
                                if elements:
                                    content = await elements[-1].inner_text()
                                else:
                                    content = ""
                            except:
                                content = ""

                        elif provider == "gemini":
                            # Gemini: Wait for response
                            try:
                                await page.wait_for_selector(".model-response", timeout=15000)
                                elements = await page.query_selector_all(".model-response")
                                if elements:
                                    content = await elements[-1].inner_text()
                                else:
                                    content = ""
                            except:
                                content = ""

                        elif provider == "perplexity":
                            # Perplexity: Wait for response
                            try:
                                await page.wait_for_selector(".thread-message", timeout=15000)
                                elements = await page.query_selector_all(".thread-message")
                                if elements:
                                    content = await elements[-1].inner_text()
                                else:
                                    content = ""
                            except:
                                content = ""

                        else:
                            content = ""

                        end_time = datetime.now()
                        response_time = (end_time - start_time).total_seconds()

                        if content and len(content) > 50:  # Minimum content check
                            result["responses"].append({
                                "iteration": i + 1,
                                "content": content,
                                "length": len(content),
                                "response_time": response_time,
                                "hash": hashlib.md5(content.encode()).hexdigest(),
                            })
                            result["success_count"] += 1
                            print(f"✅ {len(content)} chars, {response_time:.1f}s")
                        else:
                            result["errors"].append(f"Iteration {i+1}: No content received")
                            print("❌ No content received")

                    except Exception as e:
                        result["errors"].append(f"Iteration {i+1}: {str(e)}")
                        print(f"❌ Error: {e}")

                await context.close()

        except Exception as e:
            result["status"] = "provider_error"
            result["error"] = str(e)
            print(f"  Provider error: {e}")
            return result

        # Calculate similarities
        if len(result["responses"]) >= 2:
            print("\n  Calculating similarities...")
            similarities = []
            hashes = [r["hash"] for r in result["responses"]]

            for i in range(len(result["responses"]) - 1):
                for j in range(i + 1, len(result["responses"])):
                    sim = self.calculate_similarity(
                        result["responses"][i]["content"],
                        result["responses"][j]["content"]
                    )
                    similarities.append(sim)
                    print(f"    Response {i+1} vs {j+1}: {sim['overall_score']*100:.1f}%")

            result["similarities"] = similarities
            result["unique_hashes"] = len(set(hashes))
            result["total_hashes"] = len(hashes)

            result["avg_similarity"] = {
                "length": sum(s["length_similarity"] for s in similarities) / len(similarities),
                "jaccard": sum(s["jaccard_similarity"] for s in similarities) / len(similarities),
                "character": sum(s["character_match"] for s in similarities) / len(similarities),
                "hash": sum(s["hash_match"] for s in similarities) / len(similarities),
                "overall": sum(s["overall_score"] for s in similarities) / len(similarities),
            }

        result["status"] = "completed" if result["success_count"] > 0 else "failed"
        return result

    async def run_tests(self) -> list[dict[str, Any]]:
        """Run reproducibility tests."""
        prompt = self.get_test_prompt()

        print(f"\n{'='*60}")
        print("ACTUAL AI REPRODUCIBILITY TEST")
        print(f"{'='*60}")
        print(f"Iterations: {self.iterations}")
        print(f"Test prompt: {len(prompt)} chars")
        print(f"{'='*60}")

        # AI providers (excluding ChatGPT - needs login)
        providers = [
            ("claude", "https://claude.ai", "div[contenteditable='true'], [contenteditable='true']"),
            ("gemini", "https://gemini.google.com", ".ql-editor"),
            ("perplexity", "https://www.perplexity.ai", "[role='textbox']"),
        ]

        results = []

        for provider, url, selector in providers:
            result = await self.test_single_ai(provider, url, prompt, selector)
            results.append(result)

        return results

    def generate_report(self, results: list[dict[str, Any]]) -> str:
        """Generate evaluation report."""
        lines = []
        lines.append("# 실제 AI 응답 재현성 평가 보고서")
        lines.append("")
        lines.append(f"**평가 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("**평가 방식**: Playwright 웹 브라우저 실제 접속")
        lines.append(f"**반복 횟수**: {self.iterations}회")
        lines.append("")

        # Summary
        lines.append("## 1. 평가 개요")
        lines.append("")
        lines.append("| AI | 상태 | 성공 | 평균 길이 | 평균 시간 | 유사도 | 해시 |")
        lines.append("|----|------|------|----------|----------|--------|------|")

        for r in results:
            if r["status"] == "completed" and "avg_similarity" in r:
                status = "✅ 완료"
                success = f"{r['success_count']}/{r['iterations']}"
                avg_len = f"{sum(resp['length'] for resp in r['responses']) / len(r['responses']):.0f}"
                avg_time = f"{sum(resp['response_time'] for resp in r['responses']) / len(r['responses']):.1f}s"
                avg_sim = f"{r['avg_similarity']['overall']*100:.1f}%"
                hash_info = f"{r['unique_hashes']}/{r['total_hashes']}"

            elif r["status"] == "not_logged_in":
                status = "❌ 로그인 필요"
                success = "0/0"
                avg_len = "N/A"
                avg_time = "N/A"
                avg_sim = "N/A"
                hash_info = "N/A"

            else:
                status = f"⚠️ {r['status']}"
                success = f"{r.get('success_count', 0)}/{r['iterations']}"
                avg_len = "N/A"
                avg_time = "N/A"
                avg_sim = "N/A"
                hash_info = "N/A"

            lines.append(f"| {r['provider']} | {status} | {success} | {avg_len} | {avg_time} | {avg_sim} | {hash_info} |")

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
                    preview = resp["content"][:80].replace("\n", " ")
                    lines.append(f"  - 반복 {resp['iteration']}: {resp['length']}자, {resp['response_time']:.1f}초")
                    lines.append(f"    해시: {resp['hash'][:16]}...")
                    lines.append(f"    내용: {preview}...")

            if "avg_similarity" in r:
                avg = r["avg_similarity"]
                lines.append("")
                lines.append("**유사도 지표**:")
                lines.append(f"- 길이 유사도: {avg['length']*100:.1f}%")
                lines.append(f"- 단어 중첩도 (Jaccard): {avg['jaccard']*100:.1f}%")
                lines.append(f"- 문자 일치: {avg['character']*100:.1f}%")
                lines.append(f"- 해시 일치: {avg['hash']*100:.1f}%")
                lines.append(f"- **종합 유사도: {avg['overall']*100:.1f}%**")
                lines.append(f"- 해시 다양성: {r['unique_hashes']}/{r['total_hashes']} ({r['total_hashes']-r['unique_hashes']}개 다름)")

            lines.append("")

        # Conclusion
        lines.append("## 3. 종합 평가")
        lines.append("")

        completed = [r for r in results if r["status"] == "completed"]
        not_logged_in = [r for r in results if r["status"] == "not_logged_in"]
        failed = [r for r in results if r["status"] not in ["completed", "not_logged_in"]]

        if completed:
            overall_sim = sum(r["avg_similarity"]["overall"] for r in completed) / len(completed)
            lines.append(f"- **완료된 AI**: {len(completed)}/{len(results)}개")
            lines.append(f"- **평균 유사도**: {overall_sim*100:.1f}%")
            lines.append(f"- **전체 해시 일치**: {sum(1 for r in completed if r['unique_hashes'] == 1)}/{len(completed)}개")

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

        if not_logged_in:
            lines.append("")
            lines.append("- **로그인 필요**: ChatGPT")

        lines.append("")
        lines.append("## 4. 결론")
        lines.append("")

        if completed:
            lines.append("**실제 AI 응답 재현성 평가 완료**")
            lines.append("")
            lines.append(f"- 평가된 AI: {', '.join([r['provider'] for r in completed])}")
            lines.append(f"- 평균 유사도: {overall_sim*100:.1f}%")
            lines.append("")
            lines.append("**해석**:")
            if overall_sim >= 0.9:
                lines.append("- AI 응답이 매우 일관적임")
                lines.append("- Temperature 설정이 낮음 (결정론적 모드)")
            elif overall_sim >= 0.7:
                lines.append("- AI 응답이 상당히 일관적임")
                lines.append("- 일부 창의적 변동성이 있음")
            else:
                lines.append("- AI 응답의 변동성이 큼")
                lines.append("- 창의성을 위해 높은 Temperature 설정")

        lines.append("")
        lines.append("*보고서 생성일: " + datetime.now().strftime('%Y-%m-%d %H:%M') + "*")

        return "\n".join(lines)


async def main():
    """Main test function."""
    tester = ActualAIReproducibilityTest()

    try:
        results = await tester.run_tests()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Generate report
    report = tester.generate_report(results)

    # Save report
    report_path = Path("docs/ai-reproducibility-results/actual/ai-reproducibility-test-report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    print(f"\n{'='*60}")
    print(f"📄 보고서 저장됨: {report_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
