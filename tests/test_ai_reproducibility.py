"""
AI Reproducibility Evaluation Script.
Evaluates AI response reproducibility across multiple dimensions.

Three Evaluation Dimensions:
1. AI Response Reproducibility: Same prompt → 10 AI responses → Compare
2. End-to-End Pipeline Reproducibility: Full 5-phase pipeline → 10 runs → Compare
3. Temporal Traceability: Same input + same seed → Reproduce anytime
"""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any

# Note: This script requires actual AI API calls
# Current implementation provides framework for evaluation


class AIReproducibilityEvaluator:
    """Evaluate AI response reproducibility."""

    def __init__(self):
        self.iterations = 10
        self.results_dir = Path("docs/ai-reproducibility-results")
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts using multiple metrics."""
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

        # 3. Character-level similarity (simplified)
        # Using hash comparison for exact match
        hash_sim = 1.0 if hashlib.md5(text1.encode()).hexdigest() == hashlib.md5(text2.encode()).hexdigest() else 0.0

        return {
            "length_similarity": len_sim,
            "jaccard_similarity": jaccard,
            "hash_match": hash_sim,
            "overall_score": (len_sim * 0.3 + jaccard * 0.5 + hash_sim * 0.2),
        }

    def evaluate_ai_response_reproducibility(self, prompt: str, ai_model: str) -> dict[str, Any]:
        """
        Dimension 1: AI Response Reproducibility
        Same prompt → 10 AI responses → Compare similarity
        """
        print(f"\n{'='*60}")
        print("Dimension 1: AI Response Reproducibility")
        print(f"AI Model: {ai_model}")
        print(f"Prompt: {prompt[:100]}...")
        print(f"{'='*60}")

        # Note: This requires actual AI API call
        # Framework structure provided below
        results = {
            "dimension": "AI Response Reproducibility",
            "ai_model": ai_model,
            "prompt": prompt,
            "iterations": self.iterations,
            "responses": [],  # To be filled with actual AI responses
            "similarities": [],
            "status": "framework_only",  # Change to "evaluated" when run with actual AI
        }

        # Framework for evaluation:
        # for i in range(self.iterations):
        #     response = call_ai_api(prompt, ai_model)
        #     results["responses"].append(response)
        #
        # # Calculate pairwise similarities
        # for i in range(len(results["responses"])):
        #     for j in range(i+1, len(results["responses"])):
        #         sim = self.calculate_similarity(results["responses"][i], results["responses"][j])
        #         results["similarities"].append(sim)

        return results

    def evaluate_pipeline_reproducibility(self, topic: str, doc_type: str = "bizplan") -> dict[str, Any]:
        """
        Dimension 2: End-to-End Pipeline Reproducibility
        Full 5-phase pipeline → 10 runs → Compare final documents
        """
        print(f"\n{'='*60}")
        print("Dimension 2: End-to-End Pipeline Reproducibility")
        print(f"Topic: {topic}")
        print(f"Document Type: {doc_type}")
        print(f"{'='*60}")

        results = {
            "dimension": "Pipeline Reproducibility",
            "topic": topic,
            "doc_type": doc_type,
            "iterations": self.iterations,
            "final_documents": [],  # To be filled with actual pipeline outputs
            "document_hashes": [],
            "similarity_scores": [],
            "status": "framework_only",
        }

        # Framework for evaluation:
        # for i in range(self.iterations):
        #     pipeline = AigenFlowPipeline()
        #     document = pipeline.run(topic=topic, doc_type=doc_type)
        #     results["final_documents"].append(document)
        #     results["document_hashes"].append(hashlib.md5(document.encode()).hexdigest())
        #
        # # Calculate document similarities
        # for i in range(len(results["final_documents"])):
        #     for j in range(i+1, len(results["final_documents"])):
        #         sim = self.calculate_similarity(results["final_documents"][i], results["final_documents"][j])
        #         results["similarity_scores"].append(sim)

        return results

    def evaluate_temporal_traceability(self, topic: str, seed: int, time_gap_hours: int = 24) -> dict[str, Any]:
        """
        Dimension 3: Temporal Traceability
        Same input + same seed → Run at different times → Compare results
        """
        print(f"\n{'='*60}")
        print("Dimension 3: Temporal Traceability")
        print(f"Topic: {topic}")
        print(f"Seed: {seed}")
        print(f"Time Gap: {time_gap_hours} hours")
        print(f"{'='*60}")

        results = {
            "dimension": "Temporal Traceability",
            "topic": topic,
            "seed": seed,
            "time_gap_hours": time_gap_hours,
            "run_times": [],
            "outputs": [],
            "output_hashes": [],
            "similarity_scores": [],
            "status": "framework_only",
        }

        # Framework for evaluation:
        # Requires running the same pipeline at different times
        # First run:
        # results["run_times"].append(datetime.now().isoformat())
        # output1 = run_with_seed(topic, seed)
        # results["outputs"].append(output1)
        # results["output_hashes"].append(hashlib.md5(output1.encode()).hexdigest())
        #
        # Wait for time_gap_hours
        #
        # Second run:
        # results["run_times"].append(datetime.now().isoformat())
        # output2 = run_with_seed(topic, seed)
        # results["outputs"].append(output2)
        # results["output_hashes"].append(hashlib.md5(output2.encode()).hexdigest())
        #
        # Compare:
        # sim = self.calculate_similarity(output1, output2)
        # results["similarity_scores"].append(sim)

        return results

    def generate_framework_report(self) -> str:
        """Generate comprehensive evaluation framework report."""
        lines = []
        lines.append("# AI 재현성 평가 프레임워크")
        lines.append("")
        lines.append(f"**생성 일시**: {datetime.now().strftime('%Y-%m-%d')}")
        lines.append("**평가 차원**: 3가지")
        lines.append("")

        lines.append("## 1. 평가 차원 개요")
        lines.append("")
        lines.append("| 차원 | 설명 | 평가 방법 | 기대 재현성 |")
        lines.append("|------|------|-----------|-----------|")
        lines.append("| **AI 응답 재현성** | 동일 프롬프트 → AI 응답 | 10회 반복 후 유사도 측정 | 70-90% |")
        lines.append("| **파이프라인 종단 재현성** | 전체 5단계 실행 | 10회 실행 후 문서 비교 | 60-85% |")
        lines.append("| **시간 추적성** | 다른 시점에서 실행 | 동일 입력+시드로 재현 | 80-95% |")
        lines.append("")

        lines.append("## 2. 상세 평가 방법")
        lines.append("")

        lines.append("### 2.1 AI 응답 재현성")
        lines.append("")
        lines.append("**목표**: 동일 프롬프트에 대한 AI 응답의 일관성 측정")
        lines.append("")
        lines.append("**변수 요인**:")
        lines.append("- AI 모델 내부 랜덤성 (Temperature, Top-p)")
        lines.append("- API 서버 상태")
        lines.append("- 네트워크 지연")
        lines.append("- 모델 버전/업데이트")
        lines.append("")
        lines.append("**평가 지표**:")
        lines.append("- 길이 유사도 (Length Similarity)")
        lines.append("- 단어 중첩도 (Jaccard Similarity)")
        lines.append("- 해시 일치 (Exact Match)")
        lines.append("- 종합 유사도 (Overall Score)")
        lines.append("")
        lines.append("**기대 결과**:")
        lines.append("| 설정 | 기대 재현성 | 설명 |")
        lines.append("|------|-------------|------|")
        lines.append("| Temperature=0 | 95-100% | 결정론적 모드 |")
        lines.append("| Temperature=0.7 | 70-85% | 창의성 모드 (일반적) |")
        lines.append("| Temperature=1.0+ | 50-70% | 고변동성 모드 |")
        lines.append("")

        lines.append("### 2.2 파이프라인 종단 재현성")
        lines.append("")
        lines.append("**목표**: 전체 5단계 파이프라인의 재현성 측정")
        lines.append("")
        lines.append("**변수 요인**:")
        lines.append("- 각 단계의 AI 응답 변동성 (누적)")
        lines.append("- 4개 AI 모델 간의 상호작용")
        lines.append("- Phase 간 컨텍스트 전달 차이")
        lines.append("- 외부 요인 (시간, 네트워크)")
        lines.append("")
        lines.append("**평가 지표**:")
        lines.append("- 최종 문서 길이 분산")
        lines.append("- 섹션별 내용 유사도")
        lines.append("- 핵심 주제 보존율")
        lines.append("- 구조적 일관성")
        lines.append("")
        lines.append("**기대 결과**:")
        lines.append("| 구성 | 기대 재현성 | 설명 |")
        lines.append("|------|-------------|------|")
        lines.append("| 모든 AI: Temperature=0 | 85-95% | 최고 일관성 모드 |")
        lines.append("| 혼합: 일부 Temperature>0 | 60-80% | 일반적인 운영 모드 |")
        lines.append("| 모든 AI: Temperature>0.7 | 40-60% | 고창의성 모드 |")
        lines.append("")

        lines.append("### 2.3 시간 추적성")
        lines.append("")
        lines.append("**목표**: 시간이 지난 후 동일 결과 재현 가능성")
        lines.append("")
        lines.append("**변수 요인**:")
        lines.append("- AI 모델 업데이트")
        lines.append("- 템플릿/코드 변경")
        lines.append("- 환경 설정 변경")
        lines.append("- 시드 설정 유효성")
        lines.append("")
        lines.append("**평가 방법**:")
        lines.append("```python")
        lines.append("# 시점 1: 현재 실행")
        lines.append("result1 = run_pipeline(topic, seed=42)")
        lines.append("save_checkpoint(result1, 'checkpoint_v1.json')")
        lines.append("")
        lines.append("# 시점 2: 24시간 후 (또는 1주 후)")
        lines.append("result2 = run_pipeline(topic, seed=42)")
        lines.append("compare_results(result1, result2)")
        lines.append("```")
        lines.append("")
        lines.append("**기대 결과**:")
        lines.append("| 조건 | 기대 재현성 | 설명 |")
        lines.append("|------|-------------|------|")
        lines.append("| 코드/템플릿 동결 | 90-98% | 버전 관리 완료 시 |")
        lines.append("| AI 모델 버전 고정 | 85-95% | 모델 버전 지정 시 |")
        lines.append("| AI 모델 최신 사용 | 70-85% | 업데이트 영향 있음 |")
        lines.append("")

        lines.append("## 3. 실행 방법")
        lines.append("")
        lines.append("### 3.1 현재 상태")
        lines.append("")
        lines.append("```bash")
        lines.append("# 현재는 프레임워크만 제공 (실제 AI 호출 필요)")
        lines.append("python tests/test_ai_reproducibility.py")
        lines.append("# → 프레임워크 구조 출력")
        lines.append("```")
        lines.append("")
        lines.append("### 3.2 실제 평가 실행")
        lines.append("")
        lines.append("```bash")
        lines.append("# 1. API 키 설정")
        lines.append("export OPENAI_API_KEY=\"sk-...\"")
        lines.append("export ANTHROPIC_API_KEY=\"sk-...\"")
        lines.append("export GEMINI_API_KEY=\"...\"")
        lines.append("export PERPLEXITY_API_KEY=\"...\"")
        lines.append("")
        lines.append("# 2. AI 응답 재현성 평가")
        lines.append("python tests/test_ai_reproducibility.py --dimension ai-response \\")
        lines.append("    --prompt \"AI 기반 스마트폰 관리 시스템\" \\")
        lines.append("    --model claude --iterations 10")
        lines.append("")
        lines.append("# 3. 파이프라인 재현성 평가")
        lines.append("python tests/test_ai_reproducibility.py --dimension pipeline \\")
        lines.append("    --topic \"AI SaaS 플랫폼\" --type bizplan --iterations 10")
        lines.append("")
        lines.append("# 4. 시간 추적성 평가")
        lines.append("python tests/test_ai_reproducibility.py --dimension temporal \\")
        lines.append("    --topic \"AI SaaS 플랫폼\" --seed 42 --time-gap 24")
        lines.append("```")
        lines.append("")

        lines.append("## 4. 결과 보고서 형식")
        lines.append("")
        lines.append("### 4.1 AI 응답 재현성 보고서")
        lines.append("")
        lines.append("```markdown")
        lines.append("# AI 응답 재현성 평가 결과")
        lines.append("")
        lines.append("## 평가 개요")
        lines.append("- AI 모델: Claude 3.5 Sonnet")
        lines.append("- 프롬프트: \"[프롬프트 내용]\"")
        lines.append("- 반복 횟수: 10회")
        lines.append("- Temperature: 0.7")
        lines.append("")
        lines.append("## 결과 요약")
        lines.append("| 지표 | 평균 | 최소 | 최대 | 표준편차 |")
        lines.append("|------|------|------|------|----------|")
        lines.append("| 길이 유사도 | 0.95 | 0.90 | 0.98 | 0.02 |")
        lines.append("| Jaccard 유사도 | 0.78 | 0.65 | 0.85 | 0.06 |")
        lines.append("| 해시 일치 | 0/10 | - | - | - |")
        lines.append("| 종합 점수 | 0.82 | - | - | - |")
        lines.append("```")
        lines.append("")

        lines.append("### 4.2 파이프라인 재현성 보고서")
        lines.append("")
        lines.append("```markdown")
        lines.append("# 파이프라인 종단 재현성 평가 결과")
        lines.append("")
        lines.append("## 평가 개요")
        lines.append("- 주제: \"AI 기반 스마트폰 관리 시스템\"")
        lines.append("- 문서 유형: bizplan")
        lines.append("- 반복 횟수: 10회")
        lines.append("")
        lines.append("## 결과 요약")
        lines.append("| Phase | 평균 재현성 | 변동 계수 |")
        lines.append("|-------|-------------|----------|")
        lines.append("| Phase 1: 아이디어 생성 | 85% | 12% |")
        lines.append("| Phase 2: 시장 조사 | 78% | 18% |")
        lines.append("| Phase 3: 전략 분석 | 82% | 15% |")
        lines.append("| Phase 4: 문서 작성 | 75% | 22% |")
        lines.append("| Phase 5: 검증/폴리싱 | 80% | 16% |")
        lines.append("| **종단 재현성** | **72%** | **25%** |")
        lines.append("```")
        lines.append("")

        lines.append("### 4.3 시간 추적성 보고서")
        lines.append("")
        lines.append("```markdown")
        lines.append("# 시간 추적성 평가 결과")
        lines.append("")
        lines.append("## 평가 개요")
        lines.append("- 주제: \"AI 기반 스마트폰 관리 시스템\"")
        lines.append("- 시드: 42")
        lines.append("- 시간 간격: 24시간")
        lines.append("")
        lines.append("## 결과 요약")
        lines.append("| 항목 | 시점 1 | 시점 2 | 유사도 |")
        lines.append("|------|--------|--------|--------|")
        lines.append("| 실행 시간 | 2025-02-15 10:00 | 2025-02-16 10:00 | - |")
        lines.append("| 문서 길이 | 12,345자 | 12,401자 | 99.6% |")
        lines.append("| 섹션 구조 | 동일 | 동일 | 100% |")
        lines.append("| 핵심 주제 | 15개 | 15개 | 100% |")
        lines.append("| 종합 유사도 | - | - | 92% |")
        lines.append("```")
        lines.append("")

        lines.append("## 5. 제한 사항")
        lines.append("")
        lines.append("| 항목 | 설명 |")
        lines.append("|------|------|")
        lines.append("| **API 비용** | 10회 반복 시 실제 API 호출 비용 발생 |")
        lines.append("| **실행 시간** | 파이프라인 10회 실행 시 약 2-3시간 소요 |")
        lines.append("| **모델 변경** | AI 모델 업데이트 시 재현성 저하 가능 |")
        lines.append("| **외부 요인** | 네트워크, 서버 상태 등 통제 불가능 요인 |")
        lines.append("")

        lines.append("## 6. 개선 권장사항")
        lines.append("")
        lines.append("**재현성 향상을 위한 설정**:")
        lines.append("")
        lines.append("1. **Temperature 설정**")
        lines.append("   ```python")
        lines.append("   # 높은 재현성 필요 시")
        lines.append("   temperature = 0  # 결정론적 모드")
        lines.append("")
        lines.append("   # 창의성 필요 시")
        lines.append("   temperature = 0.7  # 일반 모드")
        lines.append("   ```")
        lines.append("")
        lines.append("2. **시드 설정**")
        lines.append("   ```python")
        lines.append("   # 재현성 필요 시 고정 시드 사용")
        lines.append("   seed = 42")
        lines.append("   np.random.seed(seed)")
        lines.append("   ```")
        lines.append("")
        lines.append("3. **버전 고정**")
        lines.append("   ```python")
        lines.append("   # AI 모델 버전 명시")
        lines.append("   model = \"claude-3-5-sonnet-20241022\"  # 특정 버전")
        lines.append("   ```")
        lines.append("")

        lines.append("*문서 버전: 1.0.0*")
        lines.append("*생성일: 2026-02-15*")

        return "\n".join(lines)


def main():
    """Main evaluation function."""
    print("🔍 AI 재현성 평가 프레임워크")
    print("=" * 60)
    print()
    print("현재 상태: 프레임워크 제공 (실제 평가 실행 시 API 키 필요)")
    print()
    print("평가 차원:")
    print("  1. AI 응답 재현성 - 동일 프롬프트 → 10회 AI 응답 비교")
    print("  2. 파이프라인 종단 재현성 - 전체 5단계 → 10회 실행 비교")
    print("  3. 시간 추적성 - 동일 입력+시드 → 시간차 두고 비교")
    print()
    print("=" * 60)

    evaluator = AIReproducibilityEvaluator()

    # Generate framework report
    report = evaluator.generate_framework_report()

    # Save report
    report_path = evaluator.results_dir / "ai-reproducibility-framework.md"
    report_path.write_text(report, encoding="utf-8")

    print(f"\n📄 프레임워크 보고서 저장됨: {report_path}")
    print()
    print("실제 평가 실행 방법:")
    print("  1. API 키 설정 (.env 파일 또는 환경변수)")
    print("  2. 평가 스크립트에서 AI 호출 코드 활성화")
    print("  3. 평가 실행: python tests/test_ai_reproducibility.py --dimension <차원>")


if __name__ == "__main__":
    main()
