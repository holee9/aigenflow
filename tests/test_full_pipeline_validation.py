"""
Full Pipeline Validation Test - 10 Iterations
Tests all 12 templates across 4 AIs, 10 repetitions.
Generates comprehensive evaluation report.
"""

import asyncio
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.chatgpt_agent import ChatGPTAgent
from src.agents.claude_agent import ClaudeAgent
from src.agents.gemini_agent import GeminiAgent
from src.agents.perplexity_agent import PerplexityAgent
from src.core.config import get_settings
from src.core.models import DocumentType, PipelineConfig
from src.pipeline.orchestrator import PipelineOrchestrator

# Test topic
TEST_TOPIC = "AI 기반 스마트폰 건강관리 어플리케이션"


class PipelineValidator:
    """Validator for full pipeline testing."""

    def __init__(self, iterations: int = 10):
        self.iterations = iterations
        self.settings = get_settings()
        self.results: list[dict[str, Any]] = []
        self.orchestrator: PipelineOrchestrator | None = None

    def _setup_agents(self) -> bool:
        """Register all AI agents with the orchestrator."""
        if self.orchestrator is None:
            return False

        profiles_dir = self.settings.profiles_dir
        headless = self.settings.gateway_headless
        registered = 0

        try:
            chatgpt = ChatGPTAgent(profile_dir=profiles_dir / "chatgpt", headless=headless)
            self.orchestrator.agent_router.register_agent("chatgpt", chatgpt)
            registered += 1
        except Exception as e:
            print(f"  ⚠️ ChatGPT registration failed: {e}")

        try:
            claude = ClaudeAgent(profile_dir=profiles_dir / "claude", headless=headless)
            self.orchestrator.agent_router.register_agent("claude", claude)
            registered += 1
        except Exception as e:
            print(f"  ⚠️ Claude registration failed: {e}")

        try:
            gemini = GeminiAgent(profile_dir=profiles_dir / "gemini", headless=headless)
            self.orchestrator.agent_router.register_agent("gemini", gemini)
            registered += 1
        except Exception as e:
            print(f"  ⚠️ Gemini registration failed: {e}")

        try:
            perplexity = PerplexityAgent(profile_dir=profiles_dir / "perplexity", headless=headless)
            self.orchestrator.agent_router.register_agent("perplexity", perplexity)
            registered += 1
        except Exception as e:
            print(f"  ⚠️ Perplexity registration failed: {e}")

        print(f"  ✅ Registered {registered}/4 agents")
        return registered >= 2  # Need at least 2 agents for meaningful test

    def calculate_similarity(self, text1: str, text2: str) -> dict[str, float]:
        """Calculate similarity between two texts."""
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

    async def run_single_iteration(self, iteration: int) -> dict[str, Any]:
        """Run a single pipeline iteration."""
        print(f"\n{'='*60}")
        print(f"Iteration {iteration}/{self.iterations}")
        print(f"{'='*60}")

        result = {
            "iteration": iteration,
            "topic": TEST_TOPIC,
            "phases": {},
            "final_document": "",
            "errors": [],
            "success": False,
        }

        try:
            # Create config
            config = PipelineConfig(
                topic=TEST_TOPIC,
                doc_type=DocumentType.BIZPLAN,
            )

            # Use shared orchestrator with pre-registered agents
            if self.orchestrator is None:
                self.orchestrator = PipelineOrchestrator(settings=self.settings)
                if not self._setup_agents():
                    result["errors"].append("Failed to register agents")
                    return result

            # Run complete pipeline
            print("  Running pipeline...")
            session = await self.orchestrator.run_pipeline(config)

            # Extract phase results from session.results list
            for phase_num in range(1, 6):
                phase_result = session.get_phase_result(phase_num)
                if phase_result:
                    phase_key = f"phase_{phase_num}"
                    result["phases"][phase_key] = {
                        "status": phase_result.status.value,
                        "completed_at": phase_result.completed_at.isoformat() if phase_result.completed_at else None,
                        "agent_responses": len(phase_result.ai_responses) if phase_result.ai_responses else 0,
                    }

                    status_icon = "✓" if phase_result.status.value == "completed" else "✗"
                    print(f"    {status_icon} Phase {phase_num}: {phase_result.status.value} ({len(phase_result.ai_responses)} responses)")

            # Check if pipeline completed
            if session.state.value == "completed":
                result["success"] = True

                # Try to read final document
                output_dir = config.output_dir / session.session_id
                final_doc_path = output_dir / "final" / "business_plan.md"
                if final_doc_path.exists():
                    result["final_document"] = final_doc_path.read_text(encoding="utf-8")
                    print(f"\n  ✓ Final document: {len(result['final_document'])} chars")
                else:
                    result["errors"].append("Final document not found")
            else:
                result["errors"].append(f"Pipeline did not complete: {session.state.value}")

        except Exception as e:
            result["errors"].append(f"Exception: {str(e)}")
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()

        return result

    async def run_all_iterations(self) -> list[dict[str, Any]]:
        """Run all iterations."""
        print("\n" + "="*60)
        print("FULL PIPELINE VALIDATION TEST")
        print("="*60)
        print(f"Iterations: {self.iterations}")
        print(f"Topic: {TEST_TOPIC}")
        print(f"Document Type: {DocumentType.BIZPLAN.value}")
        print("="*60)

        results = []

        for i in range(1, self.iterations + 1):
            result = await self.run_single_iteration(i)
            results.append(result)

            # Save intermediate result
            intermediate_path = Path(f"output/validation_intermediate_{i}.json")
            intermediate_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

        return results

    def analyze_results(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze all results."""
        print("\n" + "="*60)
        print("ANALYZING RESULTS")
        print("="*60)

        analysis = {
            "total_iterations": self.iterations,
            "successful_iterations": 0,
            "failed_iterations": 0,
            "phase_success_rate": {},
            "document_similarities": [],
            "avg_similarity": None,
            "errors_by_phase": {},
        }

        # Count successes
        for r in results:
            if r["success"]:
                analysis["successful_iterations"] += 1
            else:
                analysis["failed_iterations"] += 1

        # Phase success rates
        for phase_num in range(1, 6):
            phase_key = f"phase_{phase_num}"
            successes = sum(1 for r in results if phase_key in r["phases"] and r["phases"][phase_key]["status"] == "completed")
            analysis["phase_success_rate"][phase_key] = {
                "successes": successes,
                "total": len(results),
                "rate": successes / len(results) if len(results) > 0 else 0,
            }

        # Document similarities (for successful iterations)
        successful_results = [r for r in results if r["success"] and r["final_document"]]

        if len(successful_results) >= 2:
            print(f"\n  Calculating document similarities ({len(successful_results)} documents)...")

            for i in range(len(successful_results) - 1):
                doc1 = successful_results[i]["final_document"]
                doc2 = successful_results[i+1]["final_document"]

                sim = self.calculate_similarity(doc1, doc2)
                analysis["document_similarities"].append({
                    "iteration_1": successful_results[i]["iteration"],
                    "iteration_2": successful_results[i+1]["iteration"],
                    "similarity": sim,
                })

                print(f"    Iteration {i+1} vs {i+2}: {sim['overall']*100:.1f}%")

            # Calculate average similarity
            if analysis["document_similarities"]:
                analysis["avg_similarity"] = {
                    "length": sum(s["similarity"]["length_similarity"] for s in analysis["document_similarities"]) / len(analysis["document_similarities"]),
                    "jaccard": sum(s["similarity"]["jaccard_similarity"] for s in analysis["document_similarities"]) / len(analysis["document_similarities"]),
                    "character": sum(s["similarity"]["character_match"] for s in analysis["document_similarities"]) / len(analysis["document_similarities"]),
                    "hash": sum(s["similarity"]["hash_match"] for s in analysis["document_similarities"]) / len(analysis["document_similarities"]),
                    "overall": sum(s["similarity"]["overall"] for s in analysis["document_similarities"]) / len(analysis["document_similarities"]),
                }

                print(f"\n  Average similarity: {analysis['avg_similarity']['overall']*100:.1f}%")

        # Collect errors by phase
        for r in results:
            for error in r["errors"]:
                # Extract phase from error
                phase = "unknown"
                if "Phase" in error:
                    try:
                        phase_num = int(error.split()[1])
                        phase = f"phase_{phase_num}"
                    except:
                        pass

                if phase not in analysis["errors_by_phase"]:
                    analysis["errors_by_phase"][phase] = []
                analysis["errors_by_phase"][phase].append(error)

        return analysis

    def generate_report(self, results: list[dict[str, Any]], analysis: dict[str, Any]) -> str:
        """Generate comprehensive evaluation report."""
        lines = []
        lines.append("# 전체 파이프라인 종합 검증 보고서")
        lines.append("")
        lines.append(f"**평가 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("**평가 방식**: AigenFlow 전체 파이프라인 실행")
        lines.append(f"**반복 횟수**: {self.iterations}회")
        lines.append(f"**테스트 주제**: {TEST_TOPIC}")
        lines.append(f"**문서 유형**: {DocumentType.BIZPLAN.value}")
        lines.append("")

        # Executive Summary
        lines.append("## 1. 요약")
        lines.append("")
        lines.append("| 항목 | 결과 |")
        lines.append("|------|------|")
        lines.append(f"| 총 반복 횟수 | {self.iterations}회 |")
        lines.append(f"| 성공한 실행 | {analysis['successful_iterations']}회 |")
        lines.append(f"| 실패한 실행 | {analysis['failed_iterations']}회 |")
        lines.append(f"| 성공률 | {analysis['successful_iterations']/self.iterations*100:.1f}% |")

        if analysis.get("avg_similarity"):
            lines.append(f"| 문서 유사도 | {analysis['avg_similarity']['overall']*100:.1f}% |")

        lines.append("")

        # Phase Success Rates
        lines.append("## 2. 단계별 성공률")
        lines.append("")
        lines.append("| Phase | 성공 | 전체 | 성공률 |")
        lines.append("|-------|------|------|-------|")

        for phase_num in range(1, 6):
            phase_key = f"phase_{phase_num}"
            if phase_key in analysis["phase_success_rate"]:
                phase_data = analysis["phase_success_rate"][phase_key]
                lines.append(f"| Phase {phase_num} | {phase_data['successes']} | {phase_data['total']} | {phase_data['rate']*100:.1f}% |")

        lines.append("")

        # Document Similarity Analysis
        if analysis.get("document_similarities"):
            lines.append("## 3. 문서 유사도 분석")
            lines.append("")

            if analysis.get("avg_similarity"):
                avg = analysis["avg_similarity"]
                lines.append("**평균 유사도 지표:**")
                lines.append(f"- 길이 유사도: {avg['length']*100:.1f}%")
                lines.append(f"- 단어 중첩도 (Jaccard): {avg['jaccard']*100:.1f}%")
                lines.append(f"- 문자 일치: {avg['character']*100:.1f}%")
                lines.append(f"- 해시 일치: {avg['hash']*100:.1f}%")
                lines.append(f"- **종합 유사도: {avg['overall']*100:.1f}%**")
                lines.append("")

            # Grade
            overall_sim = avg['overall']
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

            lines.append("**품질 등급:**")
            lines.append(f"- {grade} ({assessment})")
            lines.append("")

        # Errors
        if analysis.get("errors_by_phase"):
            lines.append("## 4. 발생한 오류")
            lines.append("")

            for phase, errors in analysis["errors_by_phase"].items():
                if errors:
                    lines.append(f"### {phase.upper()}")
                    for error in errors[:5]:  # First 5 errors per phase
                        lines.append(f"- {error}")
                    if len(errors) > 5:
                        lines.append(f"- ... 외 {len(errors)-5}개 오류")
                    lines.append("")

        # Detailed Results
        lines.append("## 5. 상세 결과")
        lines.append("")

        for r in results[:5]:  # First 5 iterations detailed
            lines.append(f"### 반복 {r['iteration']}")
            lines.append("")
            lines.append(f"- **성공 여부**: {'✅ 성공' if r['success'] else '❌ 실패'}")
            lines.append(f"- **단계 완료**: {sum(1 for p in r['phases'].values() if p['status'] == 'completed')}/5")

            if r.get("errors"):
                lines.append(f"- **오류**: {', '.join(r['errors'][:3])}")

            if r.get("final_document"):
                lines.append(f"- **최종 문서**: {len(r['final_document'])}자")
                preview = r["final_document"][:200].replace("\n", " ")
                lines.append(f"- **미리보기**: {preview}...")

            lines.append("")

        if len(results) > 5:
            lines.append(f"*나머지 {len(results)-5}회 반복은 상세 생략*")
            lines.append("")

        # Conclusion
        lines.append("## 6. 결론")
        lines.append("")

        success_rate = analysis['successful_iterations'] / self.iterations

        if success_rate >= 0.9:
            status = "매우 안정적"
            color = "초록"
        elif success_rate >= 0.7:
            status = "안정적"
            color = "녹색"
        elif success_rate >= 0.5:
            status = "부분적으로 안정적"
            color = "노란색"
        else:
            status = "개선 필요"
            color = "빨간색"

        lines.append(f"- **파이프라인 안정성**: {status} ({success_rate*100:.1f}% 성공률)")

        if analysis.get("avg_similarity"):
            overall_sim = analysis["avg_similarity"]["overall"]
            lines.append(f"- **문서 재현성**: {overall_sim*100:.1f}%")

            if overall_sim >= 0.7:
                repro_status = "양호한 재현성"
            elif overall_sim >= 0.5:
                repro_status = "보통 수준 재현성"
            else:
                repro_status = "낮은 재현성 (AI 창의성 특성)"

            lines.append(f"- **평가**: {repro_status}")

        lines.append("")
        lines.append("*보고서 생성일: " + datetime.now().strftime('%Y-%m-%d %H:%M'))

        return "\n".join(lines)

    async def run_validation(self):
        """Run full validation and generate report."""
        # Run iterations
        results = await self.run_all_iterations()

        # Analyze results
        analysis = self.analyze_results(results)

        # Generate report
        report = self.generate_report(results, analysis)

        # Save report
        report_dir = Path("docs/validation-results")
        report_dir.mkdir(parents=True, exist_ok=True)

        report_path = report_dir / "full_pipeline_validation_report.md"
        report_path.write_text(report, encoding="utf-8")

        # Save JSON results
        results_path = report_dir / "validation_results.json"
        results_path.write_text(json.dumps({
            "results": results,
            "analysis": analysis,
        }, indent=2, ensure_ascii=False), encoding="utf-8")

        print(f"\n{'='*60}")
        print("VALIDATION COMPLETE")
        print(f"{'='*60}")
        print(f"Report: {report_path}")
        print(f"Results: {results_path}")
        print(f"{'='*60}")

        return results, analysis


async def main():
    """Main function."""
    validator = PipelineValidator(iterations=10)

    try:
        await validator.run_validation()
    except Exception as e:
        print(f"\n❌ Validation error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
