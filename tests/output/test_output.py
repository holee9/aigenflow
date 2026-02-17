"""
Tests for output modules.
"""


from output.formatter import FileExporter, MarkdownFormatter


class TestMarkdownFormatter:
    """Tests for MarkdownFormatter."""

    def test_init(self):
        """Test formatter initialization."""
        formatter = MarkdownFormatter()
        assert formatter is not None

    def test_format_document(self):
        """Test document formatting."""
        formatter = MarkdownFormatter()
        # TODO: Test actual formatting
        # result = formatter.format_document(content="Test", metadata={})
        # assert "Test" in result


class TestFileExporter:
    """Tests for FileExporter."""

    def test_init(self):
        """Test exporter initialization."""
        exporter = FileExporter(output_dir="dummy")
        assert exporter is not None
