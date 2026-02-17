"""
Quick AI Connection Test (3 iterations per AI).
Tests actual AI response collection using Playwright gateway.
"""

import asyncio
import hashlib
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, '.')

from src.core.config import get_settings
from src.gateway.base import GatewayRequest
from src.gateway.chatgpt_provider import ChatGPTProvider
from src.gateway.claude_provider import ClaudeProvider
from src.gateway.gemini_provider import GeminiProvider
from src.gateway.perplexity_provider import PerplexityProvider


class QuickAIConnectionTest:
    """Quick connection test for AI providers."""

    def __init__(self):
        self.iterations = 3
        self.config = get_settings()
        self.profile_dir = self.config.profiles_dir if hasattr(self.config, 'profiles_dir') else Path("profiles")
        self.results = []

    def get_test_prompt(self) -> str:
        """Simple test prompt."""
        return """You are an AI assistant. Please provide a brief response (2-3 sentences) about the following topic:

"AI-based smartphone management systems"

Respond in Korean."""

    def calculate_similarity(self, text1: str, text2: str) -> dict[str, float]:
        """Calculate similarity between two responses."""
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

        # Character match (first 300 chars)
        sample_size = 300
        sample1, sample2 = text1[:sample_size], text2[:sample_size]
        char_match = sum(c1 == c2 for c1, c2 in zip(sample1, sample2)) / sample_size

        # Hash match
        hash1 = hashlib.md5(text1.encode()).hexdigest()
        hash2 = hashlib.md5(text2.encode()).hexdigest()
        hash_match = 1.0 if hash1 == hash2 else 0.0

        return {
            "length_similarity": len_sim,
            "jaccard_similarity": jaccard,
            "character_match": char_match,
            "hash_match": hash_match,
            "overall_score": (len_sim * 0.2 + jaccard * 0.4 + char_match * 0.3 + hash_match * 0.1),
        }

    async def test_single_provider(self, provider_class, provider_name: str, prompt: str) -> dict[str, Any]:
        """Test a single AI provider."""
        print(f"\n{'='*60}")
        print(f"Testing {provider_name.upper()}")
        print(f"{'='*60}")

        result = {
            "provider_name": provider_name,
            "iterations": self.iterations,
            "responses": [],
            "errors": [],
            "success_count": 0,
        }

        try:
            # Initialize provider
            provider = provider_class(profile_dir=self.profile_dir, headless=False)

            # Check session
            print("  Checking session...")
            is_logged_in = await provider.check_session()
            print(f"  Session status: {'✅ Logged in' if is_logged_in else '❌ Not logged in'}")

            if not is_logged_in:
                result["status"] = "not_logged_in"
                result["error"] = "Provider not logged in. Run 'AigenFlow setup' first."
                return result

            # Send messages
            for i in range(self.iterations):
                try:
                    print(f"  Sending message {i+1}/{self.iterations}...", end=" ", flush=True)

                    request = GatewayRequest(
                        task_name="reproducibility_test",
                        prompt=prompt,
                        timeout=60
                    )

                    start_time = datetime.now()
                    response = await provider.send_message(request)
                    end_time = datetime.now()

                    if response.success:
                        result["responses"].append({
                            "iteration": i + 1,
                            "content": response.content,
                            "length": len(response.content),
                            "response_time": (end_time - start_time).total_seconds(),
                            "tokens_used": response.tokens_used,
                            "hash": hashlib.md5(response.content.encode()).hexdigest(),
                        })
                        result["success_count"] += 1
                        print(f"✅ {len(response.content)} chars, {response.tokens_used} tokens, {(end_time - start_time).total_seconds():.1f}s")
                    else:
                        error_msg = response.error or "Unknown error"
                        result["errors"].append(f"Iteration {i+1}: {error_msg}")
                        print(f"❌ {error_msg}")

                except Exception as e:
                    result["errors"].append(f"Iteration {i+1}: {str(e)}")
                    print(f"❌ Exception: {e}")

        except Exception as e:
            result["status"] = "provider_error"
            result["error"] = str(e)
            print(f"  Provider error: {e}")
            return result

        # Calculate similarities if we have multiple responses
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

            # Calculate averages
            result["avg_similarity"] = {
                "length": sum(s["length_similarity"] for s in similarities) / len(similarities),
                "jaccard": sum(s["jaccard_similarity"] for s in similarities) / len(similarities),
                "character": sum(s["character_match"] for s in similarities) / len(similarities),
                "hash": sum(s["hash_match"] for s in similarities) / len(similarities),
                "overall": sum(s["overall_score"] for s in similarities) / len(similarities),
            }

        result["status"] = "completed" if result["success_count"] > 0 else "failed"
        return result

    async def run_all_tests(self) -> list[dict[str, Any]]:
        """Run tests for all AI providers."""
        prompt = self.get_test_prompt()

        print(f"\n{'='*60}")
        print("QUICK AI CONNECTION TEST")
        print(f"{'='*60}")
        print(f"Iterations per AI: {self.iterations}")
        print(f"Profile directory: {self.profile_dir}")
        print(f"Test prompt length: {len(prompt)} chars")
        print(f"{'='*60}")

        # Provider classes
        providers = [
            (ChatGPTProvider, "chatgpt"),
            (ClaudeProvider, "claude"),
            (GeminiProvider, "gemini"),
            (PerplexityProvider, "perplexity"),
        ]

        results = []

        for provider_class, provider_name in providers:
            result = await self.test_single_provider(provider_class, provider_name, prompt)
            results.append(result)

        return results

    def generate_report(self, results: list[dict[str, Any]]) -> str:
        """Generate test report."""
        lines = []
        lines.append("# 빠른 AI 연결 테스트 결과")
        lines.append("")
        lines.append(f"**테스트 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("**테스트 방식**: Playwright 웹 브라우저 게이트웨이")
        lines.append(f"**반복 횟수**: {self.iterations}회")
        lines.append("")

        # Summary table
        lines.append("## 1. 테스트 요약")
        lines.append("")
        lines.append("| AI | 상태 | 성공 | 응답 길이 | 응답 시간 | 유사도 |")
        lines.append("|----|------|------|-----------|-----------|--------|")

        for r in results:
            if r["status"] == "completed" and "avg_similarity" in r:
                status = "✅ 완료"
                success = f"{r['success_count']}/{r['iterations']}"

                # Calculate averages
                avg_len = sum(resp["length"] for resp in r["responses"]) / len(r["responses"])
                avg_time = sum(resp["response_time"] for resp in r["responses"]) / len(r["responses"])
                avg_sim = f"{r['avg_similarity']['overall']*100:.1f}%"
                hash_info = f"{r['unique_hashes']}/{r['total_hashes']} hash"

            elif r["status"] == "not_logged_in":
                status = "❌ 로그인 필요"
                success = "0/0"
                avg_len = "N/A"
                avg_time = "N/A"
                avg_sim = "N/A"
            else:
                status = f"⚠️ {r['status']}"
                success = f"{r.get('success_count', 0)}/{r['iterations']}"
                avg_len = "N/A"
                avg_time = "N/A"
                avg_sim = "N/A"

            lines.append(f"| {r['provider_name']} | {status} | {success} | {avg_len} | {avg_time} | {avg_sim} |")

        lines.append("")

        # Detailed results
        lines.append("## 2. 상세 결과")
        lines.append("")

        for r in results:
            lines.append(f"### {r['provider_name'].upper()}")
            lines.append("")
            lines.append(f"- **상태**: {r['status']}")

            if r.get("errors"):
                lines.append(f"- **오류**: {', '.join(r['errors'])}")

            if r.get("responses"):
                lines.append("")
                lines.append("**응답 요약**:")
                for resp in r["responses"]:
                    preview = resp["content"][:100].replace("\n", " ")
                    lines.append(f"  - 반복 {resp['iteration']}: {resp['length']}자, {resp['tokens_used']}토큰, {resp['response_time']:.1f}초")
                    lines.append(f"    미리보기: {preview}...")

            if "avg_similarity" in r:
                avg = r["avg_similarity"]
                lines.append("")
                lines.append("**유사도 분석**:")
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
            lines.append("**해석**:")
            if overall_sim >= 0.9:
                lines.append("- AI 응답이 매우 일관적임 (Temperature=0에 가까움)")
                lines.append("- 프롬프트 엔지니어링에 활용 가능")
            elif overall_sim >= 0.7:
                lines.append("- AI 응답이 상당히 일관적임")
                lines.append("- 대부분 경우 유사한 응답 기대 가능")
            else:
                lines.append("- AI 응답의 변동성이 큼")
                lines.append("- 창의성을 위해 Temperature가 높게 설정된 것일 수 있음")

        if not_logged_in:
            lines.append("")
            lines.append("- **로그인 필요**: " + ", ".join([r["provider_name"] for r in not_logged_in]))
            lines.append("  - `AigenFlow setup` 명령으로 로그인 필요")

        if failed:
            lines.append("")
            lines.append("- **실패**: " + ", ".join([r["provider_name"] for r in failed]))

        lines.append("")
        lines.append("*테스트 완료일: " + datetime.now().strftime('%Y-%m-%d %H:%M') + "*")

        return "\n".join(lines)


async def main():
    """Main test function."""
    tester = QuickAIConnectionTest()

    try:
        results = await tester.run_all_tests()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return

    # Generate report
    report = tester.generate_report(results)

    # Save report
    report_path = Path("docs/ai-reproducibility-results/actual/quick-connection-test.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    print(f"\n{'='*60}")
    print(f"📄 테스트 보고서 저장됨: {report_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
