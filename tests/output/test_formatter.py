"""
Tests for OutputFormatter interface and formatters.

Tests follow TDD principles: written before implementation.
"""

from pathlib import Path

import pytest

from src.output.formatters import (
    DocxFormatter,
    MarkdownFormatter,
    OutputFormat,
    OutputFormatter,
)


class TestOutputFormat:
    """Test suite for OutputFormat enum."""

    def test_format_values(self) -> None:
        """Test format enum values."""
        assert OutputFormat.MARKDOWN.value == "md"
        assert OutputFormat.DOCX.value == "docx"
        assert OutputFormat.PDF.value == "pdf"
        assert OutputFormat.ALL.value == "all"


class TestOutputFormatter:
    """Test suite for OutputFormatter abstract interface."""

    def test_cannot_instantiate(self) -> None:
        """Test that OutputFormatter cannot be instantiated directly."""
        with pytest.raises(TypeError):
            OutputFormatter()  # type: ignore

    def test_subclass_must_implement_format_document(self, tmp_path: Path) -> None:
        """Test that subclasses must implement format_document."""
        # This test verifies the abstract method exists
        # Actual enforcement happens at runtime when calling the method
        assert hasattr(OutputFormatter, "format_document")

    def test_subclass_must_implement_get_format(self, tmp_path: Path) -> None:
        """Test that subclasses must implement get_format."""
        assert hasattr(OutputFormatter, "get_format")


class TestMarkdownFormatter:
    """Test suite for MarkdownFormatter."""

    @pytest.fixture
    def formatter(self) -> MarkdownFormatter:
        """Create MarkdownFormatter instance."""
        return MarkdownFormatter()

    def test_get_format(self, formatter: MarkdownFormatter) -> None:
        """Test get_format returns correct format."""
        assert formatter.get_format() == OutputFormat.MARKDOWN

    def test_format_document_basic(self, formatter: MarkdownFormatter) -> None:
        """Test basic document formatting."""
        content = "# Title\n\nSome content"
        metadata = {"title": "Test Document"}

        result = formatter.format_document(content, metadata)

        assert "# Title" in result
        assert "Some content" in result

    def test_format_document_with_metadata(self, formatter: MarkdownFormatter) -> None:
        """Test formatting with metadata."""
        content = "Content here"
        metadata = {
            "title": "Test Title",
            "author": "Test Author",
            "date": "2026-02-16",
        }

        result = formatter.format_document(content, metadata)

        # Should include title in output
        assert "Test Title" in result

    def test_format_empty_content(self, formatter: MarkdownFormatter) -> None:
        """Test formatting empty content."""
        result = formatter.format_document("", None)
        assert result == ""


class TestDocxFormatter:
    """Test suite for DocxFormatter."""

    @pytest.fixture
    def formatter(self) -> DocxFormatter:
        """Create DocxFormatter instance."""
        return DocxFormatter()

    def test_get_format(self, formatter: DocxFormatter) -> None:
        """Test get_format returns correct format."""
        assert formatter.get_format() == OutputFormat.DOCX

    def test_format_document_returns_bytes(self, formatter: DocxFormatter) -> None:
        """Test that format_document returns bytes."""
        content = "# Test Title\n\nTest content."

        result = formatter.format_document(content, None)

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_format_document_with_title(self, formatter: DocxFormatter, tmp_path: Path) -> None:
        """Test formatting document with title."""
        content = "# Test Title\n\nThis is test content."
        metadata = {"title": "Test Title"}

        result = formatter.format_document(content, metadata)

        # Write to file for verification
        output_file = tmp_path / "test.docx"
        output_file.write_bytes(result)

        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_format_preserves_structure(self, formatter: DocxFormatter) -> None:
        """Test that document structure is preserved."""
        content = """# Main Title

## Section 1

Content for section 1.

## Section 2

Content for section 2.

### Subsection

Subsection content.
"""

        result = formatter.format_document(content, None)
        assert isinstance(result, bytes)
        assert len(result) > 1000  # DOCX should have some content


class TestOutputFormatterFactory:
    """Test suite for output formatter factory function."""

    def test_get_formatter_markdown(self) -> None:
        """Test getting markdown formatter."""
        from src.output.formatters import get_formatter

        formatter = get_formatter(OutputFormat.MARKDOWN)
        assert isinstance(formatter, MarkdownFormatter)

    def test_get_formatter_docx(self) -> None:
        """Test getting docx formatter."""
        from src.output.formatters import get_formatter

        formatter = get_formatter(OutputFormat.DOCX)
        assert isinstance(formatter, DocxFormatter)

    def test_get_formatter_from_string(self) -> None:
        """Test getting formatter from string value."""
        from src.output.formatters import get_formatter

        formatter = get_formatter("md")
        assert isinstance(formatter, MarkdownFormatter)

    def test_get_formatter_invalid_string(self) -> None:
        """Test getting formatter with invalid string raises error."""
        from src.output.formatters import get_formatter

        with pytest.raises(ValueError, match="Unknown output format"):
            get_formatter("invalid")
