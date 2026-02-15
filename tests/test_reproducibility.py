"""
Template Reproducibility Evaluation Script.
Evaluates consistency of template rendering across 10 iterations.
"""

import hashlib
import statistics
from pathlib import Path
from typing import Any

from src.templates.manager import TemplateManager
from src.agents.router import PhaseTask
from src.pipeline.orchestrator import PipelineOrchestrator


class ReproducibilityEvaluator:
    """Evaluate template rendering reproducibility."""

    def __init__(self):
        self.template_manager = TemplateManager()
        self.orchestrator = PipelineOrchestrator(template_manager=self.template_manager)
        self.iterations = 10

    def get_base_context(self) -> dict[str, Any]:
        """Standard context for template rendering."""
        return {
            "topic": "AI 기반 스마트폰 관리 시스템",
            "doc_type": "bizplan",
            "language": "ko",
            "validated_ideas": "검증된 아이디어",
            "brainstormed_results": "브레인스토밍 결과",
            "research_results": "시장 조사 결과",
            "swot_results": "SWOT 분석 결과",
            "narrative_results": "전략 서사",
            "business_plan_content": "사업계획서 내용",
            "document_draft": "문서 초안",
            "fact_check_results": "팩트체크 결과",
            "review_feedback": "리뷰 피드백",
        }

    def render_template(self, template_name: str, context: dict[str, Any]) -> str:
        """Render a single template."""
        return self.template_manager.render_prompt(template_name, context)

    def calculate_hash(self, content: str) -> str:
        """Calculate MD5 hash of content."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def evaluate_template(self, template_name: str) -> dict[str, Any]:
        """Evaluate a single template across 10 iterations."""
        context = self.get_base_context()
        results = []
        hashes = []
        lengths = []

        for i in range(self.iterations):
            result = self.render_template(template_name, context)
            results.append(result)
            hashes.append(self.calculate_hash(result))
            lengths.append(len(result))

        # Calculate reproducibility metrics
        unique_hashes = set(hashes)
        # 100% = all identical (1 unique hash), 0% = all different
        hash_consistency = 100 if len(unique_hashes) == 1 else 0

        # Length statistics
        avg_length = statistics.mean(lengths)
        min_length = min(lengths)
        max_length = max(lengths)
        length_variance = statistics.variance(lengths) if len(lengths) > 1 else 0
        length_cv = (statistics.stdev(lengths) / avg_length * 100) if avg_length > 0 and len(lengths) > 1 else 0

        return {
            "template_name": template_name,
            "iterations": self.iterations,
            "unique_hashes": len(unique_hashes),
            "total_hashes": len(hashes),
            "hash_consistency_score": hash_consistency,  # 100% = all identical
            "all_identical": len(unique_hashes) == 1,
            "avg_length": avg_length,
            "min_length": min_length,
            "max_length": max_length,
            "length_variance": length_variance,
            "length_cv_percent": length_cv,
            "first_hash": hashes[0],
            "all_hashes": hashes,
        }

    def run_all_evaluations(self) -> list[dict[str, Any]]:
        """Evaluate all 12 templates."""
        template_mappings = [
            (1, PhaseTask.BRAINSTORM_CHATGPT, "phase_1_brainstorm_chatgpt"),
            (1, PhaseTask.VALIDATE_CLAUDE, "phase_1_validate_claude"),
            (2, PhaseTask.DEEP_SEARCH_GEMINI, "phase_2_deep_search_gemini"),
            (2, PhaseTask.FACT_CHECK_PERPLEXITY, "phase_2_fact_check_perplexity"),
            (3, PhaseTask.SWOT_CHATGPT, "phase_3_swot_chatgpt"),
            (3, PhaseTask.NARRATIVE_CLAUDE, "phase_3_narrative_claude"),
            (4, PhaseTask.BUSINESS_PLAN_CLAUDE, "phase_4_business_plan_claude"),
            (4, PhaseTask.OUTLINE_CHATGPT, "phase_4_outline_chatgpt"),
            (4, PhaseTask.CHARTS_GEMINI, "phase_4_charts_gemini"),
            (5, PhaseTask.VERIFY_PERPLEXITY, "phase_5_verify_perplexity"),
            (5, PhaseTask.FINAL_REVIEW_CLAUDE, "phase_5_final_review_claude"),
            (5, PhaseTask.POLISH_CLAUDE, "phase_5_polish_claude"),
        ]

        results = []
        for phase, task, name in template_mappings:
            template_name = self.orchestrator._build_template_name(phase, task)
            result = self.evaluate_template(template_name)
            result["friendly_name"] = name
            result["phase"] = phase
            results.append(result)

        return results

    def generate_report(self, results: list[dict[str, Any]]) -> str:
        """Generate reproducibility evaluation report."""
        lines = []
        lines.append("# 템플릿 재현성 평가 보고서")
        lines.append("")
        lines.append(f"**평가 일시**: 2026-02-15")
        lines.append(f"**평가 반복 횟수**: {self.iterations}회")
        lines.append(f"**대상 템플릿 수**: {len(results)}개")
        lines.append("")

        # Summary statistics
        all_identical_count = sum(1 for r in results if r["all_identical"])
        lines.append("## 1. 종합 평가 요약")
        lines.append("")
        lines.append("| 평가 항목 | 결과 |")
        lines.append("|-----------|------|")
        lines.append(f"| 전체 템플릿 수 | {len(results)}개 |")
        lines.append(f"| 100% 재현성 템플릿 | {all_identical_count}개 ({all_identical_count/len(results)*100:.1f}%) |")
        lines.append(f"| 평균 일관성 점수 | {statistics.mean([r['hash_consistency_score'] for r in results]):.2f}% |")
        lines.append("")

        # Individual template results
        lines.append("## 2. 템플릿별 평가 결과")
        lines.append("")
        lines.append("| Phase | 템플릿 | 재현성 | 평균 길이 | 길이 편차(%) |")
        lines.append("|-------|--------|--------|----------|-------------|")

        for r in sorted(results, key=lambda x: x["phase"]):
            consistency_status = "100%" if r["all_identical"] else f"{r['hash_consistency_score']:.0f}%"
            lines.append(f"| {r['phase']} | `{r['friendly_name']}` | {consistency_status} | {r['avg_length']:.0f}자 | {r['length_cv_percent']:.2f}% |")

        lines.append("")

        # Detailed results
        lines.append("## 3. 상세 평가 데이터")
        lines.append("")

        for r in sorted(results, key=lambda x: x["phase"]):
            lines.append(f"### {r['phase']}. {r['friendly_name']}")
            lines.append("")
            lines.append(f"- **재현성 점수**: {r['hash_consistency_score']:.1f}%")
            lines.append(f"- **전체 동일 여부**: {'예' if r['all_identical'] else '아니오'}")
            lines.append(f"- **고유 해시 수**: {r['unique_hashes']}/{r['total_hashes']}")
            lines.append(f"- **평균 길이**: {r['avg_length']:.0f}자")
            lines.append(f"- **길이 범위**: {r['min_length']} ~ {r['max_length']}자")
            lines.append(f"- **길이 변동계수(CV)**: {r['length_cv_percent']:.3f}%")
            lines.append(f"- **해시 값**: `{r['first_hash']}`")
            lines.append("")

        # Quality assessment
        lines.append("## 4. 품질 평가 기준")
        lines.append("")
        lines.append("| 등급 | 재현성 점수 | 평가 |")
        lines.append("|------|------------|------|")
        lines.append("| A+ | 100% | 완벽한 재현성 |")
        lines.append("| A | 90-99% | 우수한 재현성 |")
        lines.append("| B | 70-89% | 양호한 재현성 |")
        lines.append("| C | 50-69% | 보통 수준 |")
        lines.append("| D | < 50% | 개선 필요 |")
        lines.append("")

        # Conclusion
        lines.append("## 5. 결론")
        lines.append("")

        if all_identical_count == len(results):
            lines.append("- **평가**: 모든 템플릿이 100% 재현성을 달성")
            lines.append("- **품질**: 템플릿 시스템이 결정론적(deterministic)으로 동작")
            lines.append("- **신뢰도**: 매우 높음 - 동일 입력에 항상 동일한 출력 보장")
        else:
            lines.append(f"- **평가**: {all_identical_count}/{len(results)}개 템플릿이 100% 재현성")
            lines.append("- **품질**: 일부 템플릿에서 비결정론적 동작 확인")
            lines.append("- **권장**: 재현성이 낮은 템플릿에 대한 원인 분석 필요")

        lines.append("")
        lines.append("*보고서 생성일: 2026-02-15*")

        return "\n".join(lines)


def main():
    """Main evaluation function."""
    print("🔍 템플릿 재현성 평가 시작...")
    print(f"   반복 횟수: 10회")
    print(f"   대상 템플릿: 12개")
    print("")

    evaluator = ReproducibilityEvaluator()
    results = evaluator.run_all_evaluations()

    # Print summary
    print("📊 평가 결과 요약:")
    print("-" * 50)

    for r in results:
        status = "✅ 100%" if r["all_identical"] else f"⚠️ {r['hash_consistency_score']:.0f}%"
        print(f"  Phase {r['phase']:1d} | {r['friendly_name']:35s} | {status}")

    print("-" * 50)
    print(f"  전체 재현성: {sum(1 for r in results if r['all_identical'])}/{len(results)}개 템플릿이 100% 재현성")

    # Generate and save report
    report = evaluator.generate_report(results)
    report_path = Path("docs/template-reproducibility-report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    print(f"")
    print(f"📄 상세 보고서 저장됨: {report_path}")

    return results


if __name__ == "__main__":
    main()
