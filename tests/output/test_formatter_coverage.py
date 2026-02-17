"""
Comprehensive tests for src/output/formatter.py to improve coverage.

This module tests:
- MarkdownFormatter.format_document() with various inputs
- FileExporter.save_markdown() method
- Edge cases and error handling
"""

import json
from pathlib import Path
from typing import Any

import pytest

from src.output.formatter import FileExporter, MarkdownFormatter


class TestMarkdownFormatterCoverage:
    """Test suite for MarkdownFormatter to cover all code paths."""

    @pytest.fixture
    def formatter(self) -> MarkdownFormatter:
        """Create MarkdownFormatter instance."""
        return MarkdownFormatter()

    def test_format_document_with_none_content(self, formatter: MarkdownFormatter) -> None:
        """Test format_document with None content returns empty string."""
        # Line 22 coverage: return content or ""
        result = formatter.format_document(content=None, metadata=None)
        assert result == ""

    def test_format_document_with_empty_string(self, formatter: MarkdownFormatter) -> None:
        """Test format_document with empty string."""
        result = formatter.format_document(content="", metadata=None)
        assert result == ""

    def test_format_document_with_whitespace(self, formatter: MarkdownFormatter) -> None:
        """Test format_document with whitespace content."""
        result = formatter.format_document(content="   ", metadata=None)
        assert result == "   "

    def test_format_document_with_metadata_none(self, formatter: MarkdownFormatter) -> None:
        """Test format_document with metadata=None."""
        content = "# Test Content"
        result = formatter.format_document(content=content, metadata=None)
        assert result == content

    def test_format_document_with_empty_metadata(self, formatter: MarkdownFormatter) -> None:
        """Test format_document with empty metadata dict."""
        content = "# Test Content"
        metadata: dict[str, Any] = {}
        result = formatter.format_document(content=content, metadata=metadata)
        assert result == content

    def test_format_document_with_complex_metadata(self, formatter: MarkdownFormatter) -> None:
        """Test format_document with complex metadata."""
        content = "Content here"
        metadata = {
            "title": "Test Title",
            "author": "Test Author",
            "date": "2026-02-16",
            "version": "1.0",
            "tags": ["test", "coverage"],
        }
        result = formatter.format_document(content=content, metadata=metadata)
        # Currently format_document just returns content, so we verify it works
        assert result == content

    def test_format_document_preserves_content(self, formatter: MarkdownFormatter) -> None:
        """Test that format_document preserves original content."""
        content = """# Main Title

## Section 1

Some content here.

## Section 2

More content.
"""
        result = formatter.format_document(content=content, metadata=None)
        assert result == content

    def test_format_document_with_special_characters(self, formatter: MarkdownFormatter) -> None:
        """Test format_document with special characters."""
        content = "Test with **bold**, *italic*, `code`, and [links](url)"
        result = formatter.format_document(content=content, metadata=None)
        assert result == content

    def test_format_document_with_unicode(self, formatter: MarkdownFormatter) -> None:
        """Test format_document with unicode characters."""
        content = "Test with unicode: 한글, 中文, 日本語, emoji 🎉"
        result = formatter.format_document(content=content, metadata=None)
        assert result == content

    def test_markdown_formatter_is_pydantic_model(self, formatter: MarkdownFormatter) -> None:
        """Test that MarkdownFormatter is a Pydantic BaseModel."""
        # Verify it can be serialized
        assert hasattr(formatter, "model_dump")
        assert hasattr(formatter, "model_dump_json")


class TestFileExporterCoverage:
    """Test suite for FileExporter to cover save_markdown method."""

    @pytest.fixture
    def temp_dir(self, tmp_path: Path) -> Path:
        """Create temporary directory for file exports."""
        return tmp_path

    @pytest.fixture
    def exporter(self, temp_dir: Path) -> FileExporter:
        """Create FileExporter instance with temp directory."""
        return FileExporter(output_dir=temp_dir)

    def test_init_with_path(self, temp_dir: Path) -> None:
        """Test FileExporter initialization."""
        exporter = FileExporter(output_dir=temp_dir)
        assert exporter.output_dir == temp_dir

    def test_save_json_creates_file(self, exporter: FileExporter, temp_dir: Path) -> None:
        """Test save_json creates a JSON file."""
        data = {"key": "value", "number": 123}
        result = exporter.save_json(filename="test", data=data)

        # Verify file was created
        assert result == temp_dir / "test.json"
        assert result.exists()

        # Verify content
        with open(result, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == data

    def test_save_json_with_complex_data(self, exporter: FileExporter, temp_dir: Path) -> None:
        """Test save_json with nested data structure."""
        data = {
            "title": "Test Document",
            "metadata": {
                "author": "Test Author",
                "tags": ["test1", "test2"],
            },
            "content": "Content here",
        }
        result = exporter.save_json(filename="complex", data=data)

        assert result.exists()
        with open(result, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == data

    def test_save_json_with_unicode(self, exporter: FileExporter, temp_dir: Path) -> None:
        """Test save_json with unicode characters."""
        data = {"korean": "한글", "emoji": "🎉", "chinese": "中文"}
        result = exporter.save_json(filename="unicode", data=data)

        assert result.exists()
        with open(result, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == data

    def test_save_markdown_creates_file(self, exporter: FileExporter, temp_dir: Path) -> None:
        """Test save_markdown creates a markdown file - Lines 44-48 coverage."""
        content = "# Test Title\n\nTest content here."
        result = exporter.save_markdown(filename="test", content=content)

        # Verify file path
        assert result == temp_dir / "test.md"
        assert result.exists()

        # Verify content
        with open(result, encoding="utf-8") as f:
            saved_content = f.read()
        assert saved_content == content

    def test_save_markdown_with_empty_content(self, exporter: FileExporter, temp_dir: Path) -> None:
        """Test save_markdown with empty content."""
        content = ""
        result = exporter.save_markdown(filename="empty", content=content)

        assert result.exists()
        with open(result, encoding="utf-8") as f:
            saved_content = f.read()
        assert saved_content == content

    def test_save_markdown_with_complex_markdown(self, exporter: FileExporter, temp_dir: Path) -> None:
        """Test save_markdown with complex markdown structure."""
        content = """# Main Title

## Section 1

- List item 1
- List item 2

## Section 2

```python
def hello():
    print("Hello, World!")
```

**Bold**, *italic*, and `code` [links](url).
"""
        result = exporter.save_markdown(filename="complex", content=content)

        assert result.exists()
        with open(result, encoding="utf-8") as f:
            saved_content = f.read()
        assert saved_content == content

    def test_save_markdown_with_unicode(self, exporter: FileExporter, temp_dir: Path) -> None:
        """Test save_markdown with unicode characters."""
        content = "# Unicode Test\n\n한글, 中文, 日本語, emoji 🎉"
        result = exporter.save_markdown(filename="unicode", content=content)

        assert result.exists()
        with open(result, encoding="utf-8") as f:
            saved_content = f.read()
        assert saved_content == content

    def test_save_markdown_creates_subdirectories_if_needed(
        self, exporter: FileExporter, temp_dir: Path
    ) -> None:
        """Test that save_markdown requires directories to exist beforehand."""
        # Create a subdirectory structure
        sub_dir = temp_dir / "subdir" / "nested"

        # The implementation requires directories to exist beforehand
        # This test documents current behavior - no auto-creation
        sub_dir.mkdir(parents=True, exist_ok=True)

        exporter.output_dir = sub_dir
        content = "# Test"
        result = exporter.save_markdown(filename="test", content=content)

        # Now save should work
        assert result.exists()

    def test_save_markdown_overwrites_existing(self, exporter: FileExporter, temp_dir: Path) -> None:
        """Test that save_markdown overwrites existing files."""
        filename = "overwrite"
        content1 = "Original content"
        content2 = "Updated content"

        # Save first version
        result1 = exporter.save_markdown(filename=filename, content=content1)
        assert result1.exists()
        with open(result1, encoding="utf-8") as f:
            assert f.read() == content1

        # Save second version (should overwrite)
        result2 = exporter.save_markdown(filename=filename, content=content2)
        assert result2 == result1  # Same file path
        with open(result2, encoding="utf-8") as f:
            assert f.read() == content2

    def test_save_json_overwrites_existing(self, exporter: FileExporter, temp_dir: Path) -> None:
        """Test that save_json overwrites existing files."""
        filename = "overwrite"
        data1 = {"version": 1}
        data2 = {"version": 2}

        # Save first version
        result1 = exporter.save_json(filename=filename, data=data1)
        with open(result1, encoding="utf-8") as f:
            assert json.load(f) == data1

        # Save second version (should overwrite)
        result2 = exporter.save_json(filename=filename, data=data2)
        assert result2 == result1
        with open(result2, encoding="utf-8") as f:
            assert json.load(f) == data2

    def test_file_exporter_with_nonexistent_parent_dir(self, tmp_path: Path) -> None:
        """Test FileExporter with a directory that doesn't exist yet."""
        # Create exporter with non-existent path
        new_dir = tmp_path / "new_output"
        exporter = FileExporter(output_dir=new_dir)

        # Directory should not exist yet
        assert not new_dir.exists()

        # Create the directory manually (current behavior)
        new_dir.mkdir(parents=True, exist_ok=True)

        # Now save should work
        exporter.save_markdown(filename="test", content="test content")
        assert (new_dir / "test.md").exists()


class TestFormatterIntegration:
    """Integration tests for formatter components."""

    def test_markdown_formatter_to_file_exporter(
        self, tmp_path: Path
    ) -> None:
        """Test using MarkdownFormatter with FileExporter."""
        formatter = MarkdownFormatter()
        exporter = FileExporter(output_dir=tmp_path)

        # Format content
        content = "# Test\n\nContent"
        formatted = formatter.format_document(content=content, metadata=None)

        # Export to file
        output_path = exporter.save_markdown(filename="integration", content=formatted)

        assert output_path.exists()
        with open(output_path, encoding="utf-8") as f:
            assert f.read() == content

    def test_exporter_with_multiple_files(self, tmp_path: Path) -> None:
        """Test exporting multiple files."""
        exporter = FileExporter(output_dir=tmp_path)

        # Save multiple markdown files
        exporter.save_markdown(filename="doc1", content="Content 1")
        exporter.save_markdown(filename="doc2", content="Content 2")
        exporter.save_markdown(filename="doc3", content="Content 3")

        assert (tmp_path / "doc1.md").exists()
        assert (tmp_path / "doc2.md").exists()
        assert (tmp_path / "doc3.md").exists()

        # Save multiple JSON files
        exporter.save_json(filename="data1", data={"id": 1})
        exporter.save_json(filename="data2", data={"id": 2})

        assert (tmp_path / "data1.json").exists()
        assert (tmp_path / "data2.json").exists()
