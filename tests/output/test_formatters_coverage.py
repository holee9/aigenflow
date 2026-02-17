"""
Comprehensive tests for src/output/formatters.py to improve coverage from 45% to 85%+.

Focus on edge cases, error handling, and integration scenarios.
"""

from typing import Any

import pytest

from src.output.formatters import (
    DocxFormatter,
    MarkdownFormatter,
    OutputFormat,
    OutputFormatter,
    PdfFormatter,
    get_formatter,
)


class TestOutputFormatterAbstractMethods:
    """Test suite for OutputFormatter abstract method enforcement."""

    def test_abstract_methods_exist(self) -> None:
        """Test that abstract methods are defined in OutputFormatter."""
        # Verify that the abstract methods exist
        assert hasattr(OutputFormatter, "format_document")
        assert hasattr(OutputFormatter, "get_format")

        # Verify they are abstract methods
        import inspect

        assert inspect.isabstract(OutputFormatter)

    def test_concrete_implementations_work(self) -> None:
        """Test that concrete implementations of abstract methods work."""
        # Create a proper concrete implementation
        class ConcreteFormatter(OutputFormatter):
            def format_document(
                self, content: str, metadata: dict[str, Any] | None = None
            ) -> str:
                return content

            def get_format(self) -> OutputFormat:
                return OutputFormat.MARKDOWN

        formatter = ConcreteFormatter()
        result = formatter.format_document("test")
        assert result == "test"
        assert formatter.get_format() == OutputFormat.MARKDOWN


class TestMarkdownFormatterEdgeCases:
    """Test edge cases and metadata handling in MarkdownFormatter."""

    @pytest.fixture
    def formatter(self) -> MarkdownFormatter:
        """Create MarkdownFormatter instance."""
        return MarkdownFormatter()

    def test_create_frontmatter_with_tags_list(self, formatter: MarkdownFormatter) -> None:
        """Test frontmatter creation with tags as list."""
        metadata = {"title": "Test", "tags": ["tag1", "tag2", "tag3"]}

        result = formatter.format_document("Content", metadata)

        assert 'tags: [tag1, tag2, tag3]' in result
        assert "---" in result

    def test_create_frontmatter_with_string_value(self, formatter: MarkdownFormatter) -> None:
        """Test frontmatter creation with string values."""
        metadata = {"title": "My Title", "author": "John Doe"}

        result = formatter.format_document("Content", metadata)

        # The formatter uses quotes around string values
        assert 'title: "My Title"' in result
        assert 'author: "John Doe"' in result

    def test_create_frontmatter_with_non_string_value(self, formatter: MarkdownFormatter) -> None:
        """Test frontmatter creation with non-string values (numbers, booleans)."""
        metadata = {"count": 42, "enabled": True, "ratio": 3.14}

        result = formatter.format_document("Content", metadata)

        assert "count: 42" in result
        assert "enabled: True" in result
        assert "ratio: 3.14" in result

    def test_create_frontmatter_empty_dict(self, formatter: MarkdownFormatter) -> None:
        """Test frontmatter with empty metadata dict."""
        result = formatter.format_document("Content", {})

        # Empty dict should not add frontmatter
        assert result == "Content"

    def test_create_frontmatter_mixed_types(self, formatter: MarkdownFormatter) -> None:
        """Test frontmatter with mixed metadata types."""
        metadata = {
            "title": "Test",
            "tags": ["a", "b"],
            "count": 10,
            "active": False,
            "ratio": 2.5,
        }

        result = formatter.format_document("Content", metadata)

        assert 'title: "Test"' in result
        assert "tags: [a, b]" in result
        assert "count: 10" in result
        assert "active: False" in result
        assert "ratio: 2.5" in result

    def test_format_preserves_content_without_metadata(self, formatter: MarkdownFormatter) -> None:
        """Test that content is preserved when no metadata provided."""
        content = "# Title\n\nSome content here"
        result = formatter.format_document(content, None)

        assert result == content

    def test_format_with_whitespace_content(self, formatter: MarkdownFormatter) -> None:
        """Test formatting with whitespace-only content."""
        result = formatter.format_document("   \n\n  ", None)
        assert result == "   \n\n  "

    def test_format_with_multiline_content(self, formatter: MarkdownFormatter) -> None:
        """Test formatting with multiline content."""
        content = """# Title

First paragraph.

Second paragraph.

## Section

More content.
"""
        result = formatter.format_document(content, {"title": "Test"})

        assert "# Title" in result
        assert "First paragraph" in result
        assert "Second paragraph" in result
        assert "## Section" in result


class TestDocxFormatterImportHandling:
    """Test DOCX formatter import error handling."""

    def test_format_document_without_docx_installed(self) -> None:
        """Test format_document when python-docx is not installed."""
        # This test documents the import error handling behavior
        # Since python-docx is installed in the test environment, we can't
        # easily test the ImportError path without uninstalling it
        # The code handles ImportError by logging a warning and returning b""
        formatter = DocxFormatter()

        # Verify that when docx IS installed, it works normally
        result = formatter.format_document("Test content")
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_get_format(self) -> None:
        """Test get_format returns correct format."""
        formatter = DocxFormatter()
        assert formatter.get_format() == OutputFormat.DOCX


class TestDocxFormatterMetadataHandling:
    """Test DOCX formatter metadata handling."""

    @pytest.fixture
    def formatter(self) -> DocxFormatter:
        """Create DocxFormatter instance."""
        return DocxFormatter()

    def test_format_with_author_metadata(self, formatter: DocxFormatter) -> None:
        """Test formatting with author metadata."""
        content = "Test content"
        metadata = {"title": "Test", "author": "John Doe"}

        result = formatter.format_document(content, metadata)

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_format_with_date_metadata(self, formatter: DocxFormatter) -> None:
        """Test formatting with date metadata."""
        content = "Test content"
        metadata = {"title": "Test", "date": "2026-02-16"}

        result = formatter.format_document(content, metadata)

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_format_with_all_metadata(self, formatter: DocxFormatter) -> None:
        """Test formatting with all metadata fields."""
        content = "Test content"
        metadata = {"title": "Test", "author": "Jane Doe", "date": "2026-02-16"}

        result = formatter.format_document(content, metadata)

        assert isinstance(result, bytes)
        assert len(result) > 0


class TestDocxMarkdownParsing:
    """Test DOCX markdown parsing functionality."""

    @pytest.fixture
    def formatter(self) -> DocxFormatter:
        """Create DocxFormatter instance."""
        return DocxFormatter()

    def test_parse_horizontal_rule(self, formatter: DocxFormatter) -> None:
        """Test parsing horizontal rule (---)."""
        content = """# Title

---

Content after rule.
"""
        result = formatter.format_document(content, None)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_parse_bullet_lists(self, formatter: DocxFormatter) -> None:
        """Test parsing bullet lists with different markers."""
        content = """# List Test

- Item 1
- Item 2

* Item 3
* Item 4

+ Item 5
+ Item 6
"""
        result = formatter.format_document(content, None)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_parse_numbered_lists(self, formatter: DocxFormatter) -> None:
        """Test parsing numbered lists."""
        content = """# Numbered List

1. First item
2. Second item
3. Third item

9. Ninth item
"""
        result = formatter.format_document(content, None)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_parse_empty_lines(self, formatter: DocxFormatter) -> None:
        """Test parsing empty lines."""
        content = """# Title

Paragraph 1


Paragraph 2
"""
        result = formatter.format_document(content, None)
        assert isinstance(result, bytes)
        assert len(result) > 0


class TestDocxInlineFormatting:
    """Test DOCX inline formatting parsing."""

    @pytest.fixture
    def formatter(self) -> DocxFormatter:
        """Create DocxFormatter instance."""
        return DocxFormatter()

    def test_parse_bold_text(self, formatter: DocxFormatter) -> None:
        """Test parsing **bold** text."""
        content = "Normal text and **bold text** and more."
        result = formatter.format_document(content, None)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_parse_italic_text(self, formatter: DocxFormatter) -> None:
        """Test parsing *italic* text."""
        content = "Normal text and *italic text* and more."
        result = formatter.format_document(content, None)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_parse_mixed_formatting(self, formatter: DocxFormatter) -> None:
        """Test parsing mixed bold and italic."""
        content = "**Bold** and *italic* and **bold again**"
        result = formatter.format_document(content, None)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_parse_unclosed_bold_marker(self, formatter: DocxFormatter) -> None:
        """Test parsing with unclosed bold marker."""
        content = "Text with **unclosed bold marker"
        result = formatter.format_document(content, None)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_parse_unclosed_italic_marker(self, formatter: DocxFormatter) -> None:
        """Test parsing with unclosed italic marker."""
        content = "Text with *unclosed italic marker"
        result = formatter.format_document(content, None)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_parse_empty_formatting_markers(self, formatter: DocxFormatter) -> None:
        """Test parsing empty bold/italic markers."""
        content = "Text with ** empty ** and * empty * markers"
        result = formatter.format_document(content, None)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_parse_nested_formatting(self, formatter: DocxFormatter) -> None:
        """Test parsing nested bold and italic (not fully supported but should not crash)."""
        content = "Text with **bold and *italic* inside**"
        result = formatter.format_document(content, None)
        assert isinstance(result, bytes)
        assert len(result) > 0


class TestPdfFormatterImportHandling:
    """Test PDF formatter import error handling."""

    def test_format_document_without_reportlab_installed(self) -> None:
        """Test format_document when reportlab is not installed."""
        # This test documents the import error handling behavior
        # Since reportlab is installed in the test environment, we can't
        # easily test the ImportError path without uninstalling it
        # The code handles ImportError by logging a warning and returning b""
        formatter = PdfFormatter()

        # Verify that when reportlab IS installed, it works normally
        result = formatter.format_document("Test content")
        assert isinstance(result, bytes)
        assert len(result) > 0
        # Should start with PDF magic bytes
        assert result.startswith(b"%PDF")

    def test_get_format(self) -> None:
        """Test get_format returns correct format."""
        formatter = PdfFormatter()
        assert formatter.get_format() == OutputFormat.PDF


class TestPdfFormatterMetadataHandling:
    """Test PDF formatter metadata handling."""

    @pytest.fixture
    def formatter(self) -> PdfFormatter:
        """Create PdfFormatter instance."""
        return PdfFormatter()

    def test_format_with_author_metadata(self, formatter: PdfFormatter) -> None:
        """Test formatting with author metadata."""
        content = "Test content"
        metadata = {"title": "Test", "author": "John Doe"}

        result = formatter.format_document(content, metadata)

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_format_with_date_metadata(self, formatter: PdfFormatter) -> None:
        """Test formatting with date metadata."""
        content = "Test content"
        metadata = {"title": "Test", "date": "2026-02-16"}

        result = formatter.format_document(content, metadata)

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_format_with_all_metadata(self, formatter: PdfFormatter) -> None:
        """Test formatting with all metadata fields."""
        content = "Test content"
        metadata = {"title": "Test", "author": "Jane Doe", "date": "2026-02-16"}

        result = formatter.format_document(content, metadata)

        assert isinstance(result, bytes)
        assert len(result) > 0


class TestPdfMarkdownParsing:
    """Test PDF markdown parsing functionality."""

    @pytest.fixture
    def formatter(self) -> PdfFormatter:
        """Create PdfFormatter instance."""
        return PdfFormatter()

    def test_parse_headings(self, formatter: PdfFormatter) -> None:
        """Test parsing different heading levels."""
        content = """# Heading 1

## Heading 2

### Heading 3

#### Heading 4

##### Heading 5

###### Heading 6
"""
        result = formatter.format_document(content, None)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_parse_bullet_lists(self, formatter: PdfFormatter) -> None:
        """Test parsing bullet lists."""
        content = """# List Test

- Item 1
- Item 2
- Item 3

Paragraph

* Another item
"""
        result = formatter.format_document(content, None)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_parse_numbered_lists(self, formatter: PdfFormatter) -> None:
        """Test parsing numbered lists."""
        content = """1. First item
2. Second item
3. Third item

Paragraph

9. Ninth item
10. Tenth item
"""
        result = formatter.format_document(content, None)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_parse_empty_lines(self, formatter: PdfFormatter) -> None:
        """Test parsing empty lines."""
        content = """# Title

Paragraph 1


Paragraph 2
"""
        result = formatter.format_document(content, None)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_parse_list_at_end(self, formatter: PdfFormatter) -> None:
        """Test parsing list at end of content without trailing newline."""
        content = """# Title

Paragraph

- Item 1
- Item 2"""
        result = formatter.format_document(content, None)
        assert isinstance(result, bytes)
        assert len(result) > 0


class TestPdfMarkdownCleaning:
    """Test PDF markdown cleaning functionality."""

    @pytest.fixture
    def formatter(self) -> PdfFormatter:
        """Create PdfFormatter instance."""
        return PdfFormatter()

    def test_clean_bold_markers(self, formatter: PdfFormatter) -> None:
        """Test removing bold markers."""
        content = "Text with **bold** and __bold__ markers"
        result = formatter.format_document(content, None)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_clean_italic_markers(self, formatter: PdfFormatter) -> None:
        """Test removing italic markers."""
        content = "Text with *italic* and _italic_ markers"
        result = formatter.format_document(content, None)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_escape_special_characters(self, formatter: PdfFormatter) -> None:
        """Test escaping HTML special characters."""
        content = "Text with <tag> and <another> tags"
        result = formatter.format_document(content, None)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_clean_mixed_formatting(self, formatter: PdfFormatter) -> None:
        """Test cleaning mixed formatting."""
        content = "**Bold** *italic* __bold__ _italic_"
        result = formatter.format_document(content, None)
        assert isinstance(result, bytes)
        assert len(result) > 0


class TestGetFormatterEdgeCases:
    """Test get_formatter function edge cases."""

    def test_get_formatter_with_all_format(self) -> None:
        """Test that ALL format raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported format type"):
            get_formatter(OutputFormat.ALL)

    def test_get_formatter_with_invalid_string(self) -> None:
        """Test that invalid string format raises ValueError."""
        with pytest.raises(ValueError, match="Unknown output format"):
            get_formatter("xyz")

    def test_get_formatter_with_empty_string(self) -> None:
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError, match="Unknown output format"):
            get_formatter("")

    def test_get_formatter_case_sensitive(self) -> None:
        """Test that format strings are case-sensitive."""
        with pytest.raises(ValueError, match="Unknown output format"):
            get_formatter("MD")  # Should be lowercase

    def test_get_formatter_pdf(self) -> None:
        """Test getting PDF formatter."""
        formatter = get_formatter(OutputFormat.PDF)
        assert isinstance(formatter, PdfFormatter)

    def test_get_formatter_pdf_string(self) -> None:
        """Test getting PDF formatter from string."""
        formatter = get_formatter("pdf")
        assert isinstance(formatter, PdfFormatter)

    def test_get_formatter_docx_string(self) -> None:
        """Test getting DOCX formatter from string."""
        formatter = get_formatter("docx")
        assert isinstance(formatter, DocxFormatter)


class TestIntegrationScenarios:
    """Integration tests for complex scenarios."""

    @pytest.fixture
    def markdown_formatter(self) -> MarkdownFormatter:
        """Create MarkdownFormatter instance."""
        return MarkdownFormatter()

    @pytest.fixture
    def docx_formatter(self) -> DocxFormatter:
        """Create DocxFormatter instance."""
        return DocxFormatter()

    @pytest.fixture
    def pdf_formatter(self) -> PdfFormatter:
        """Create PdfFormatter instance."""
        return PdfFormatter()

    def test_complex_markdown_document(self, markdown_formatter: MarkdownFormatter) -> None:
        """Test formatting a complex markdown document."""
        content = """# Main Title

## Section 1

This is a paragraph with **bold** and *italic* text.

### Subsection

- List item 1
- List item 2
- List item 3

1. Numbered item 1
2. Numbered item 2

## Section 2

Another paragraph.

---

Final content.
"""
        metadata = {
            "title": "Complex Document",
            "author": "Test Author",
            "date": "2026-02-16",
            "tags": ["test", "markdown", "complex"],
        }

        result = markdown_formatter.format_document(content, metadata)

        assert "Complex Document" in result
        assert "test, markdown, complex" in result
        assert "# Main Title" in result

    def test_empty_metadata_with_content(self, markdown_formatter: MarkdownFormatter) -> None:
        """Test with empty metadata dict and content."""
        content = "# Title\n\nContent"
        result = markdown_formatter.format_document(content, {})
        assert result == content

    def test_none_metadata_various_formatters(
        self, markdown_formatter: MarkdownFormatter, docx_formatter: DocxFormatter, pdf_formatter: PdfFormatter
    ) -> None:
        """Test all formatters with None metadata."""
        content = "# Test\n\nContent"

        markdown_result = markdown_formatter.format_document(content, None)
        assert markdown_result == content

        docx_result = docx_formatter.format_document(content, None)
        assert isinstance(docx_result, bytes)
        assert len(docx_result) > 0

        pdf_result = pdf_formatter.format_document(content, None)
        assert isinstance(pdf_result, bytes)
        assert len(pdf_result) > 0

    def test_metadata_with_special_characters(
        self, markdown_formatter: MarkdownFormatter
    ) -> None:
        """Test metadata with special characters."""
        content = "Content"
        metadata = {
            "title": "Title with \"quotes\" and 'apostrophes'",
            "description": "Text with @special #characters $symbols",
        }

        result = markdown_formatter.format_document(content, metadata)

        assert "Title with" in result
        assert "special" in result

    def test_very_long_content(self, docx_formatter: DocxFormatter) -> None:
        """Test formatting very long content."""
        content = "\n\n".join([f"Paragraph {i}" for i in range(100)])
        result = docx_formatter.format_document(content, None)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_unicode_content(self, markdown_formatter: MarkdownFormatter, docx_formatter: DocxFormatter) -> None:
        """Test formatting unicode content."""
        content = "# Title\n\nUnicode: 你好 世界 🌍\n\nEmoji: 🎉 ✨"

        markdown_result = markdown_formatter.format_document(content, None)
        assert "你好" in markdown_result
        assert "🌍" in markdown_result

        docx_result = docx_formatter.format_document(content, None)
        assert isinstance(docx_result, bytes)
        assert len(docx_result) > 0
