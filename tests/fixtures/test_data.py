"""
Test data fixtures for pipeline testing.

Provides test topics, configurations, and helper functions.
"""

from pathlib import Path

from src.core.models import (
    DocumentType,
    PipelineConfig,
    PipelineSession,
    TemplateType,
)

# Test topics with minimum 10 characters
TEST_TOPICS = {
    "minimal": "AI SaaS Platform",  # Exactly 16 chars - meets minimum
    "startup": "AI-powered SaaS platform for enterprise workflow automation",
    "rd": "Quantum computing applications for secure communication protocols",
    "strategy": "Market expansion strategy for AI-driven healthcare diagnostics",
    "long": "A" * 1000,  # Very long topic for edge case testing
    "korean": "AI 기반 스마트폰 관리 시스템",
}

# Test configurations
TEST_CONFIGS = {
    "minimal": PipelineConfig(topic=TEST_TOPICS["minimal"]),
    "startup": PipelineConfig(
        topic=TEST_TOPICS["startup"],
        doc_type=DocumentType.BIZPLAN,
        template=TemplateType.STARTUP,
    ),
    "rd": PipelineConfig(
        topic=TEST_TOPICS["rd"],
        doc_type=DocumentType.RD,
        template=TemplateType.RD,
    ),
    "strategy": PipelineConfig(
        topic=TEST_TOPICS["strategy"],
        doc_type=DocumentType.BIZPLAN,
        template=TemplateType.STRATEGY,
    ),
    "korean": PipelineConfig(
        topic=TEST_TOPICS["korean"],
        doc_type=DocumentType.BIZPLAN,
        language="ko",
    ),
}

# Test template directory for testing
TEMPLATES_DIR = Path("src/templates/prompts")


def create_test_config(
    topic: str = TEST_TOPICS["startup"],
    doc_type: DocumentType = DocumentType.BIZPLAN,
    template: TemplateType = TemplateType.STARTUP,
    language: str = "en",
) -> PipelineConfig:
    """
    Create a test PipelineConfig with defaults.

    Args:
        topic: Pipeline topic
        doc_type: Document type
        template: Template type
        language: Output language

    Returns:
        PipelineConfig for testing
    """
    return PipelineConfig(
        topic=topic,
        doc_type=doc_type,
        template=template,
        language=language,
    )


def create_test_session(
    topic: str = TEST_TOPICS["startup"],
    doc_type: DocumentType = DocumentType.BIZPLAN,
) -> PipelineSession:
    """
    Create a test PipelineSession with defaults.

    Args:
        topic: Pipeline topic
        doc_type: Document type

    Returns:
        PipelineSession for testing
    """
    config = create_test_config(topic=topic, doc_type=doc_type)
    return PipelineSession(config=config)


def get_invalid_topics() -> list[tuple[str, str]]:
    """
    Get invalid topic strings for validation testing.

    Returns:
        List of (topic, expected_error) tuples
    """
    return [
        ("", "topic cannot be empty"),
        ("   ", "topic cannot be empty"),
        ("short", "topic must be at least 10 characters"),
        ("a" * 9, "topic must be at least 10 characters"),
    ]


def get_phase_task_mapping() -> dict[int, list[tuple[str, str]]]:
    """
    Get expected phase-to-task-to-agent mapping.

    Returns:
        Dict mapping phase_number to list of (task_name, agent_type) tuples
    """
    return {
        1: [
            ("brainstorm_chatgpt", "chatgpt"),
            ("validate_claude", "claude"),
        ],
        2: [
            ("deep_search_gemini", "gemini"),
            ("fact_check_perplexity", "perplexity"),
        ],
        3: [
            ("swot_chatgpt", "chatgpt"),
            ("narrative_claude", "claude"),
        ],
        4: [
            ("business_plan_claude", "claude"),
            ("outline_chatgpt", "chatgpt"),
            ("charts_gemini", "gemini"),
        ],
        5: [
            ("verify_perplexity", "perplexity"),
            ("final_review_claude", "claude"),
            ("polish_claude", "claude"),
        ],
    }
