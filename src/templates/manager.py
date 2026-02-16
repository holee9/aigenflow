"""
Template management modules.
"""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, Template
from pydantic import BaseModel, ConfigDict

from core.logger import get_logger

logger = get_logger(__name__)


class TemplateManager(BaseModel):
    """Manages prompt templates using Jinja2."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    template_dir: Path = Path("src/templates/prompts")
    env: Environment = None

    def __init__(self, **data):
        """Initialize TemplateManager with Jinja2 environment."""
        super().__init__(**data)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=False,
        )

    def get_prompt_template(self, template_name: str) -> Template:
        """Get prompt template by name."""
        try:
            return self.env.get_template(f"{template_name}.jinja2")
        except Exception:
            logger.warning(f"Template {template_name} not found, using default")
            return self.env.from_string("{{ task_description }}")

    def render_prompt(
        self,
        template_name: str,
        context: dict[str, Any],
    ) -> str:
        """Render prompt template with context."""
        template = self.get_prompt_template(template_name)
        return template.render(**context)
