"""
Simple test to verify all 12 template files exist and load correctly (no fixtures).
"""

import sys
from pathlib import Path

# 프로젝트 루트 디렉토리 경로
root_dir = Path(__file__).parent.parent
src_dir = root_dir / "src"

# src 폴더를 Python 경로에 추가
sys.path.insert(0, str(src_dir))

from templates.manager import TemplateManager
from pipeline.orchestrator import PipelineOrchestrator
from agents.router import PhaseTask


def test_all_template_files_exist():
    """All 12 template files should exist."""
    template_dir = Path("src/templates/prompts")

    expected_files = [
        # Phase 1
        "phase_1/brainstorm_chatgpt.jinja2",
        "phase_1/validate_claude.jinja2",
        # Phase 2
        "phase_2/deep_search_gemini.jinja2",
        "phase_2/fact_check_perplexity.jinja2",
        # Phase 3
        "phase_3/swot_chatgpt.jinja2",
        "phase_3/narrative_claude.jinja2",
        # Phase 4
        "phase_4/business_plan_claude.jinja2",
        "phase_4/outline_chatgpt.jinja2",
        "phase_4/charts_gemini.jinja2",
        # Phase 5
        "phase_5/verify_perplexity.jinja2",
        "phase_5/final_review_claude.jinja2",
        "phase_5/polish_claude.jinja2",
    ]

    for file_path in expected_files:
        full_path = template_dir / file_path
        assert full_path.exists(), f"Template file {file_path} should exist"

    print("✅ All 12 template files exist!")


def test_jinja2_environment_lists_all_templates():
    """Jinja2 environment should list all 12 templates."""
    tm = TemplateManager()
    all_templates = tm.env.list_templates()
    assert len(all_templates) == 12, f"Should have 12 templates, got {len(all_templates)}"
    print(f"✅ Jinja2 lists all {len(all_templates)} templates")


def test_all_templates_loadable():
    """All 12 templates should be loadable without errors."""
    tm = TemplateManager()
    orch = PipelineOrchestrator(template_manager=tm)

    test_cases = [
        (1, PhaseTask.BRAINSTORM_CHATGPT, "Phase 1 Brainstorm"),
        (1, PhaseTask.VALIDATE_CLAUDE, "Phase 1 Validate"),
        (2, PhaseTask.DEEP_SEARCH_GEMINI, "Phase 2 Deep Search"),
        (2, PhaseTask.FACT_CHECK_PERPLEXITY, "Phase 2 Fact Check"),
        (3, PhaseTask.SWOT_CHATGPT, "Phase 3 SWOT"),
        (3, PhaseTask.NARRATIVE_CLAUDE, "Phase 3 Narrative"),
        (4, PhaseTask.BUSINESS_PLAN_CLAUDE, "Phase 4 Business Plan"),
        (4, PhaseTask.OUTLINE_CHATGPT, "Phase 4 Outline"),
        (4, PhaseTask.CHARTS_GEMINI, "Phase 4 Charts"),
        (5, PhaseTask.VERIFY_PERPLEXITY, "Phase 5 Verify"),
        (5, PhaseTask.FINAL_REVIEW_CLAUDE, "Phase 5 Final Review"),
        (5, PhaseTask.POLISH_CLAUDE, "Phase 5 Polish"),
    ]

    base_context = {
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

    passed = 0
    failed = 0

    for phase, task, name in test_cases:
        template_name = f"phase_{phase}/{task.value.lower()}"
        try:
            result = tm.render_prompt(template_name, base_context)
            if len(result) > 50:  # Template rendered successfully
                passed += 1
                print(f"✅ {name}: {len(result)} chars")
            else:
                failed += 1
                print(f"❌ {name}: rendered too short ({len(result)} chars)")
        except Exception as e:
            failed += 1
            print(f"❌ {name}: {type(e).__name__}: {e}")

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed out of 12 tests")
    print(f"{'='*60}")

    assert failed == 0, f"{failed} templates failed to render"


if __name__ == "__main__":
    test_all_template_files_exist()
    test_jinja2_environment_lists_all_templates()
    test_all_templates_loadable()
