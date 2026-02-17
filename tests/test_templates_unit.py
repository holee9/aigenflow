"""
Unit tests for all template files (API key not required).
"""


import pytest

from src.agents.router import PhaseTask
from src.pipeline.orchestrator import PipelineOrchestrator
from src.templates.manager import TemplateManager


class TestAllTemplates:
    """Test all 12 template files can be loaded and rendered."""

    @pytest.fixture
    def template_manager(self):
        return TemplateManager()

    @pytest.fixture
    def orchestrator(self, template_manager):
        return PipelineOrchestrator(template_manager=template_manager)

    @pytest.fixture
    def base_context(self):
        """Base context for template rendering."""
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

    # Phase 1 Tests
    def test_phase_1_brainstorm_template(self, orchestrator, base_context):
        """Phase 1 Brainstorm template loads and renders."""
        template_name = f"phase_1/{PhaseTask.BRAINSTORM_CHATGPT.value.lower()}"
        result = orchestrator.template_manager.render_prompt(template_name, base_context)
        assert len(result) > 100, "Brainstorm template should render substantial content"
        assert "AI assistant" in result or "AI 어시스턴트" in result

    def test_phase_1_validate_template(self, orchestrator, base_context):
        """Phase 1 Validate template loads and renders."""
        template_name = f"phase_1/{PhaseTask.VALIDATE_CLAUDE.value.lower()}"
        result = orchestrator.template_manager.render_prompt(template_name, base_context)
        assert len(result) > 200, "Validate template should render substantial content"
        assert "Review" in result or "검토" in result

    # Phase 2 Tests
    def test_phase_2_deep_search_template(self, orchestrator, base_context):
        """Phase 2 Deep Search template loads and renders."""
        template_name = f"phase_2/{PhaseTask.DEEP_SEARCH_GEMINI.value.lower()}"
        result = orchestrator.template_manager.render_prompt(template_name, base_context)
        assert len(result) > 300, "Deep Search template should render substantial content"
        assert "research" in result.lower() or "조사" in result

    def test_phase_2_fact_check_template(self, orchestrator, base_context):
        """Phase 2 Fact Check template loads and renders."""
        template_name = f"phase_2/{PhaseTask.FACT_CHECK_PERPLEXITY.value.lower()}"
        result = orchestrator.template_manager.render_prompt(template_name, base_context)
        assert len(result) > 200, "Fact Check template should render substantial content"
        assert "fact" in result.lower() or "팩트" in result

    # Phase 3 Tests
    def test_phase_3_swot_template(self, orchestrator, base_context):
        """Phase 3 SWOT template loads and renders."""
        template_name = f"phase_3/{PhaseTask.SWOT_CHATGPT.value.lower()}"
        result = orchestrator.template_manager.render_prompt(template_name, base_context)
        assert len(result) > 200, "SWOT template should render substantial content"
        assert "SWOT" in result or "스웟트" in result

    def test_phase_3_narrative_template(self, orchestrator, base_context):
        """Phase 3 Narrative template loads and renders."""
        template_name = f"phase_3/{PhaseTask.NARRATIVE_CLAUDE.value.lower()}"
        result = orchestrator.template_manager.render_prompt(template_name, base_context)
        assert len(result) > 200, "Narrative template should render substantial content"
        assert "strategic" in result.lower() or "전략" in result

    # Phase 4 Tests
    def test_phase_4_business_plan_template(self, orchestrator, base_context):
        """Phase 4 Business Plan template loads and renders."""
        template_name = f"phase_4/{PhaseTask.BUSINESS_PLAN_CLAUDE.value.lower()}"
        context = {**base_context, "narrative_results": "전략 서사"}
        result = orchestrator.template_manager.render_prompt(template_name, context)
        assert len(result) > 300, "Business Plan template should render substantial content"
        assert "Executive Summary" in result or "경영진 요약" in result

    def test_phase_4_outline_template(self, orchestrator, base_context):
        """Phase 4 Outline template loads and renders."""
        template_name = f"phase_4/{PhaseTask.OUTLINE_CHATGPT.value.lower()}"
        context = {**base_context, "business_plan_content": "사업계획 내용"}
        result = orchestrator.template_manager.render_prompt(template_name, context)
        assert len(result) > 200, "Outline template should render substantial content"
        assert "outline" in result.lower() or "개요" in result

    def test_phase_4_charts_template(self, orchestrator, base_context):
        """Phase 4 Charts template loads and renders."""
        template_name = f"phase_4/{PhaseTask.CHARTS_GEMINI.value.lower()}"
        context = {**base_context, "business_plan_content": "사업계획 내용"}
        result = orchestrator.template_manager.render_prompt(template_name, context)
        assert len(result) > 200, "Charts template should render substantial content"
        assert "chart" in result.lower() or "차트" in result

    # Phase 5 Tests
    def test_phase_5_verify_template(self, orchestrator, base_context):
        """Phase 5 Verify template loads and renders."""
        template_name = f"phase_5/{PhaseTask.VERIFY_PERPLEXITY.value.lower()}"
        context = {**base_context, "document_draft": "문서 초안"}
        result = orchestrator.template_manager.render_prompt(template_name, context)
        assert len(result) > 200, "Verify template should render substantial content"
        assert "fact" in result.lower() or "팩트" in result

    def test_phase_5_final_review_template(self, orchestrator, base_context):
        """Phase 5 Final Review template loads and renders."""
        template_name = f"phase_5/{PhaseTask.FINAL_REVIEW_CLAUDE.value.lower()}"
        context = {**base_context, "document_draft": "문서 초안", "fact_check_results": "팩트체크 결과"}
        result = orchestrator.template_manager.render_prompt(template_name, context)
        assert len(result) > 200, "Final Review template should render substantial content"
        assert "review" in result.lower() or "리뷰" in result

    def test_phase_5_polish_template(self, orchestrator, base_context):
        """Phase 5 Polish template loads and renders."""
        template_name = f"phase_5/{PhaseTask.POLISH_CLAUDE.value.lower()}"
        context = {**base_context, "document_draft": "문서 초안", "review_feedback": "리뷰 피드백"}
        result = orchestrator.template_manager.render_prompt(template_name, context)
        assert len(result) > 150, "Polish template should render substantial content"
        assert "polish" in result.lower() or "폴리시" in result
