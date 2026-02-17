"""
Tests for CLI status command.

Uses TDD approach: tests written before implementation.
"""

import json
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from cli.status import app as status_app

runner = CliRunner()


class TestStatusCommand:
    """Test suite for status command."""

    @pytest.fixture
    def mock_session_file(self, tmp_path):
        """Create a mock session file."""
        session_file = tmp_path / "session_abc123.json"
        session_data = {
            "session_id": "abc123",
            "phase": "research",
            "status": "in_progress",
            "created_at": "2026-02-16T00:00:00",
            "updated_at": "2026-02-16T01:00:00",
        }
        session_file.write_text(json.dumps(session_data))
        return session_file

    def test_status_no_sessions(self, tmp_path):
        """Test status command when no sessions exist."""
        with patch("cli.status.SESSIONS_DIR", tmp_path):
            result = runner.invoke(status_app)
            assert result.exit_code == 0
            assert "no pipeline sessions" in result.stdout.lower() or "start a new pipeline" in result.stdout.lower()

    def test_status_with_sessions(self, mock_session_file, tmp_path):
        """Test status command with active sessions."""
        with patch("cli.status.SESSIONS_DIR", tmp_path):
            result = runner.invoke(status_app)
            assert result.exit_code == 0
            assert "abc123" in result.stdout

    def test_status_specific_session(self, mock_session_file, tmp_path):
        """Test status command for specific session."""
        with patch("cli.status.SESSIONS_DIR", tmp_path):
            result = runner.invoke(status_app, ["abc123"])
            assert result.exit_code == 0
            assert "abc123" in result.stdout
            assert "research" in result.stdout.lower()
