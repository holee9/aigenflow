"""
Simple test to verify all 12 template files exist and load correctly.
"""

from pathlib import Path

import pytest

from src.pipeline.orchestrator import PipelineOrchestrator
from src.templates.manager import TemplateManager


@pytest.fixture
def template_manager():
    return TemplateManager()


@pytest.fixture
def orchestrator(template_manager):
    return PipelineOrchestrator(template_manager=template_manager)


class TestTemplatesExist:
    """Verify all 12 template files exist and load."""

    def test_all_12_templates_exist(self):
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

    def test_jinja2_environment_lists_all_templates(self, template_manager):
        """Jinja2 environment should list all 12 templates."""
        all_templates = template_manager.env.list_templates()
        assert len(all_templates) == 12, f"Should have 12 templates, got {len(all_templates)}"

        expected = [
            "phase_1/brainstorm_chatgpt.jinja2",
            "phase_1/validate_claude.jinja2",
            "phase_2/deep_search_gemini.jinja2",
            "phase_2/fact_check_perplexity.jinja2",
            "phase_3/swot_chatgpt.jinja2",
            "phase_3/narrative_claude.jinja2",
            "phase_4/business_plan_claude.jinja2",
            "phase_4/outline_chatgpt.jinja2",
            "phase_4/charts_gemini.jinja2",
            "phase_5/verify_perplexity.jinja2",
            "phase_5/final_review_claude.jinja2",
            "phase_5/polish_claude.jinja2",
        ]

        for template in expected:
            assert template in all_templates, f"Template {template} should be in list"
