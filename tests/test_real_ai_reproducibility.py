"""
Real AI Response Reproducibility Evaluation.
Uses Playwright gateway to test actual AI responses.

Note: This requires valid Playwright sessions with all AI providers.
"""

import asyncio
import hashlib
import statistics
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, '.')

from src.templates.manager import TemplateManager


class RealAIReproducibilityEvaluator:
    """Evaluate actual AI response reproducibility using Playwright gateway."""

    def __init__(self):
        self.iterations = 10  # Reduced from 10 to 3 for faster testing
        self.results_dir = Path("docs/ai-reproducibility-results/actual")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.template_manager = TemplateManager()

    def get_test_prompt(self) -> str:
        """Generate a test prompt from template."""
        context = {
            "topic": "AI 기반 스마트폰 관리 시스템",
            "doc_type": "bizplan",
            "language": "ko",
        }
        # Use brainstorm template as test prompt
        return self.template_manager.render_prompt("phase_1/brainstorm_chatgpt", context)

    def calculate_similarity(self, text1: str, text2: str) -> dict[str, float]:
        """Calculate similarity between two AI responses."""
        # 1. Length similarity
        len1, len2 = len(text1), len(text2)
        len_sim = min(len1, len2) / max(len1, len2) if max(len1, len2) > 0 else 1.0

        # 2. Word overlap (Jaccard)
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if words1 or words2:
            jaccard = len(words1 & words2) / len(words1 | words2)
        else:
            jaccard = 1.0

        # 3. Character-level similarity (first 500 chars)
        sample_size = 500
        sample1, sample2 = text1[:sample_size], text2[:sample_size]
        char_match = sum(c1 == c2 for c1, c2 in zip(sample1, sample2)) / sample_size

        # 4. Hash match
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

    async def evaluate_single_ai(self, provider_name: str, prompt: str) -> dict[str, Any]:
        """Evaluate single AI provider reproducibility."""
        print(f"\n{'='*60}")
        print(f"Evaluating {provider_name}")
        print(f"Prompt length: {len(prompt)} chars")
        print(f"Iterations: {self.iterations}")
        print(f"{'='*60}")

        results = {
            "provider_name": provider_name,
            "prompt": prompt[:200] + "...",
            "iterations": self.iterations,
            "responses": [],
            "response_times": [],
            "errors": [],
        }

        # This would require actual Playwright provider implementation
        # Framework structure provided:
        # provider = self.get_provider(provider_name)
        # if not provider:
        #     results["status"] = "provider_not_available"
        #     results["error"] = f"{provider_name} provider not configured"
        #     return results

        # for i in range(self.iterations):
        #     try:
        #         start_time = datetime.now()
        #         response = await provider.send_message(prompt)
        #         end_time = datetime.now()
        #
        #         results["responses"].append(response)
        #         results["response_times"].append((end_time - start_time).total_seconds())
        #
        #         print(f"  Iteration {i+1}/{self.iterations}: {len(response)} chars, {(end_time - start_time).total_seconds():.2f}s")
        #
        #     except Exception as e:
        #         results["errors"].append(str(e))
        #         print(f"  Iteration {i+1}/{self.iterations}: ERROR - {e}")

        # Calculate similarities if we have responses
        if len(results["responses"]) >= 2:
            similarities = []
            for i in range(len(results["responses"]) - 1):
                sim = self.calculate_similarity(results["responses"][i], results["responses"][i+1])
                similarities.append(sim)

            results["similarities"] = similarities
            results["avg_similarity"] = {
                "length": statistics.mean([s["length_similarity"] for s in similarities]),
                "jaccard": statistics.mean([s["jaccard_similarity"] for s in similarities]),
                "character": statistics.mean([s["character_match"] for s in similarities]),
                "hash": statistics.mean([s["hash_match"] for s in similarities]),
                "overall": statistics.mean([s["overall_score"] for s in similarities]),
            }

        results["status"] = "evaluated" if len(results["responses"]) > 0 else "no_responses"
        return results

    async def evaluate_all_providers(self, prompt: str) -> list[dict[str, Any]]:
        """Evaluate all AI providers."""
        providers = ["chatgpt", "claude", "gemini", "perplexity"]
        results = []

        for provider in providers:
            try:
                result = await self.evaluate_single_ai(provider, prompt)
                results.append(result)
            except Exception as e:
                results.append({
                    "provider_name": provider,
                    "status": "error",
                    "error": str(e),
                })

        return results

    def generate_report(self, results: list[dict[str, Any]]) -> str:
        """Generate evaluation report."""
        lines = []
        lines.append("# 실제 AI 응답 재현성 평가 보고서")
        lines.append("")
        lines.append(f"**평가 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("**평가 방식**: Playwright 웹 브라우저 게이트웨이")
        lines.append(f"**반복 횟수**: {self.iterations}회")
        lines.append("")

        # Summary
        lines.append("## 1. 평가 개요")
        lines.append("")
        lines.append("| AI | 상태 | 응답 수 | 평균 응답 시간 | 평균 유사도 |")
        lines.append("|----|------|----------|----------------|-------------|")

        for r in results:
            if r["status"] == "evaluated" and "avg_similarity" in r:
                status = "✅ 완료"
                responses = len(r["responses"])
                avg_time = f"{statistics.mean(r['response_times']):.1f}s" if r.get("response_times") else "N/A"
                avg_sim = f"{r['avg_similarity']['overall']*100:.1f}%"
            elif r["status"] == "provider_not_available":
                status = "❌ 미설정"
                responses = 0
                avg_time = "N/A"
                avg_sim = "N/A"
            else:
                status = f"⚠️ {r['status']}"
                responses = len(r.get("responses", []))
                avg_time = "N/A"
                avg_sim = "N/A"

            lines.append(f"| {r['provider_name']} | {status} | {responses} | {avg_time} | {avg_sim} |")

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

            if "avg_similarity" in r:
                avg = r["avg_similarity"]
                lines.append("")
                lines.append("**유사도 지표**:")
                lines.append(f"- 길이 유사도: {avg['length']*100:.1f}%")
                lines.append(f"- 단어 중첩도 (Jaccard): {avg['jaccard']*100:.1f}%")
                lines.append(f"- 문자 일치: {avg['character']*100:.1f}%")
                lines.append(f"- 해시 일치: {avg['hash']*100:.1f}%")
                lines.append(f"- **종합 유사도: {avg['overall']*100:.1f}%**")

            lines.append("")

        # Conclusion
        lines.append("## 3. 결론")
        lines.append("")

        evaluated_count = sum(1 for r in results if r["status"] == "evaluated")
        total_count = len(results)

        if evaluated_count == 0:
            lines.append("⚠️ **평가 미진행**: 실제 AI 응답 평가를 위해서는:")
            lines.append("")
            lines.append("1. Playwright 프로필 설정 (`AigenFlow setup` 실행)")
            lines.append("2. 각 AI 서비스 웹 로그인")
            lines.append("3. 세션 유효성 확인")
        elif evaluated_count == total_count:
            avg_overall = statistics.mean([
                r["avg_similarity"]["overall"] for r in results
                if r.get("avg_similarity")
            ])
            lines.append(f"- **평가 완료**: {evaluated_count}/{total_count}개 AI")
            lines.append(f"- **평균 재현성**: {avg_overall*100:.1f}%")

            if avg_overall >= 0.9:
                grade = "A+"
                assessment = "매우 우수한 재현성"
            elif avg_overall >= 0.8:
                grade = "A"
                assessment = "우수한 재현성"
            elif avg_overall >= 0.7:
                grade = "B"
                assessment = "양호한 재현성"
            else:
                grade = "C"
                assessment = "개선 필요"

            lines.append(f"- **품질 등급**: {grade} ({assessment})")
        else:
            lines.append(f"- **부분 평가**: {evaluated_count}/{total_count}개 AI만 완료")

        lines.append("")
        lines.append("*보고서 생성일: 2026-02-15*")

        return "\n".join(lines)


async def main():
    """Main evaluation function."""
    print("🔍 실제 AI 응답 재현성 평가")
    print("=" * 60)
    print()
    print("Playwright 게이트웨이를 통한 실제 AI 응답 평가")
    print()
    print("⚠️ 주의사항:")
    print("  - 각 AI 서비스에 로그인되어 있어야 합니다")
    print("  - 평가에는 상당한 시간이 소요됩니다")
    print("  - API 요청 비용이 발생할 수 있습니다")
    print()
    print("=" * 60)

    evaluator = RealAIReproducibilityEvaluator()
    prompt = evaluator.get_test_prompt()

    print(f"\n📝 테스트 프롬프트 길이: {len(prompt)}자")
    print("   (템플릿: phase_1/brainstorm_chatgpt)")
    print()

    # Check if we should run actual evaluation
    # For now, generate framework report without actual API calls
    # results = await evaluator.evaluate_all_providers(prompt)

    # Generate placeholder report
    results = [
        {
            "provider_name": "chatgpt",
            "status": "framework_only",
            "note": "실제 평가를 위해서는 Playwright 세션 필요"
        },
        {
            "provider_name": "claude",
            "status": "framework_only",
            "note": "실제 평가를 위해서는 Playwright 세션 필요"
        },
        {
            "provider_name": "gemini",
            "status": "framework_only",
            "note": "실제 평가를 위해서는 Playwright 세션 필요"
        },
        {
            "provider_name": "perplexity",
            "status": "framework_only",
            "note": "실제 평가를 위해서는 Playwright 세션 필요"
        },
    ]

    report = evaluator.generate_report(results)

    # Save report
    report_path = evaluator.results_dir / "ai-response-reproducibility-report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    print(f"\n📄 평가 보고서 저장됨: {report_path}")
    print()
    print("실제 평가 실행 방법:")
    print("  1. AigenFlow setup - 각 AI 서비스 로그인")
    print("  2. AigenFlow check - 세션 상태 확인")
    print("  3. python tests/test_real_ai_reproducibility.py")


if __name__ == "__main__":
    asyncio.run(main())
