"""
Tests for template manager.
"""


from templates.manager import TemplateManager


class TestTemplateManager:
    """Tests for TemplateManager."""

    def test_init(self):
        """Test manager initialization."""
        manager = TemplateManager(settings=None)
        assert manager is not None

    def test_get_prompt_template(self):
        """Test getting prompt template."""
        manager = TemplateManager(settings=None)
        template = manager.get_prompt_template("phase1")

        assert template is not None
