"""
Tests for cookie storage functionality.
"""

import json
from pathlib import Path

import pytest

from gateway.cookie_storage import CookieStorage, SessionMetadata


@pytest.fixture
def temp_profile_dir(tmp_path: Path) -> Path:
    """Create a temporary profile directory."""
    profile_dir = tmp_path / "test_provider"
    profile_dir.mkdir(parents=True, exist_ok=True)
    return profile_dir


@pytest.fixture
def sample_cookies() -> list[dict]:
    """Create sample cookies for testing."""
    return [
        {
            "name": "session_token",
            "value": "test_token_value",
            "domain": ".example.com",
            "path": "/",
            "expires": -1,
            "httpOnly": True,
            "secure": True,
            "sameSite": "Lax",
        },
        {
            "name": "user_id",
            "value": "user123",
            "domain": ".example.com",
            "path": "/",
            "expires": -1,
            "httpOnly": False,
            "secure": True,
            "sameSite": "Lax",
        },
    ]


class TestSessionMetadata:
    """Test suite for SessionMetadata model."""

    def test_default_values(self) -> None:
        """Test SessionMetadata default values."""
        metadata = SessionMetadata(provider_name="test_provider")

        assert metadata.provider_name == "test_provider"
        assert metadata.is_valid is True
        assert metadata.login_method == "manual"
        assert metadata.cookie_count == 0

    def test_mark_validated(self) -> None:
        """Test mark_validated updates timestamp."""
        import time

        metadata = SessionMetadata(provider_name="test")

        original_timestamp = metadata.last_validated
        time.sleep(0.001)  # Small delay to ensure timestamp changes
        metadata.mark_validated()

        assert metadata.last_validated != original_timestamp
        assert metadata.last_validated > original_timestamp

    def test_mark_invalid(self) -> None:
        """Test mark_invalid sets is_valid to False."""
        metadata = SessionMetadata(provider_name="test")

        assert metadata.is_valid is True
        metadata.mark_invalid()
        assert metadata.is_valid is False

    def test_serialization(self) -> None:
        """Test SessionMetadata can be serialized to JSON."""
        metadata = SessionMetadata(
            provider_name="test",
            cookie_count=5,
            login_method="auto",
        )

        # Serialize
        json_str = metadata.model_dump_json()

        # Deserialize
        data = json.loads(json_str)
        assert data["provider_name"] == "test"
        assert data["cookie_count"] == 5
        assert data["login_method"] == "auto"


class TestCookieStorage:
    """Test suite for CookieStorage class."""

    def test_initialization(self, temp_profile_dir: Path) -> None:
        """Test CookieStorage initialization."""
        storage = CookieStorage(temp_profile_dir)

        assert storage.profile_dir == temp_profile_dir
        assert storage.cookies_path == temp_profile_dir / "cookies.json"
        assert storage.key_path == temp_profile_dir / "cookies.json.key"
        assert storage.metadata_path == temp_profile_dir / "session_meta.json"

    def test_save_cookies(self, temp_profile_dir: Path, sample_cookies: list[dict]) -> None:
        """Test saving encrypted cookies."""
        storage = CookieStorage(temp_profile_dir)

        metadata = SessionMetadata(provider_name="test_provider", cookie_count=len(sample_cookies))
        storage.save_cookies(sample_cookies, metadata)

        # Verify files were created
        assert storage.cookies_path.exists()
        assert storage.key_path.exists()
        assert storage.metadata_path.exists()

        # Verify cookies are encrypted (not plaintext)
        cookies_content = storage.cookies_path.read_text()
        assert "session_token" not in cookies_content
        assert "test_token_value" not in cookies_content

    def test_load_cookies(self, temp_profile_dir: Path, sample_cookies: list[dict]) -> None:
        """Test loading and decrypting cookies."""
        storage = CookieStorage(temp_profile_dir)

        # Save cookies
        metadata = SessionMetadata(provider_name="test_provider", cookie_count=len(sample_cookies))
        storage.save_cookies(sample_cookies, metadata)

        # Load cookies
        loaded_cookies = storage.load_cookies()

        # Verify loaded cookies match original
        assert loaded_cookies == sample_cookies

    def test_save_load_roundtrip(self, temp_profile_dir: Path, sample_cookies: list[dict]) -> None:
        """Test save and load cycle preserves cookie data."""
        storage = CookieStorage(temp_profile_dir)

        # Save
        metadata = SessionMetadata(provider_name="test_provider")
        storage.save_cookies(sample_cookies, metadata)

        # Load
        loaded = storage.load_cookies()

        # Verify all fields preserved
        assert len(loaded) == len(sample_cookies)
        for original, restored in zip(sample_cookies, loaded):
            assert original == restored

    def test_load_nonexistent_cookies_fails(self, temp_profile_dir: Path) -> None:
        """Test loading non-existent cookies raises FileNotFoundError."""
        storage = CookieStorage(temp_profile_dir)

        with pytest.raises(FileNotFoundError):
            storage.load_cookies()

    def test_save_metadata(self, temp_profile_dir: Path) -> None:
        """Test saving session metadata."""
        storage = CookieStorage(temp_profile_dir)

        metadata = SessionMetadata(
            provider_name="test_provider",
            cookie_count=10,
            login_method="auto",
        )
        storage.save_metadata(metadata)

        # Verify file exists
        assert storage.metadata_path.exists()

        # Verify content
        loaded = storage.load_metadata()
        assert loaded.provider_name == "test_provider"
        assert loaded.cookie_count == 10
        assert loaded.login_method == "auto"

    def test_load_metadata(self, temp_profile_dir: Path) -> None:
        """Test loading session metadata."""
        storage = CookieStorage(temp_profile_dir)

        # Save metadata
        metadata = SessionMetadata(
            provider_name="test_provider",
            is_valid=False,
            cookie_count=5,
        )
        storage.save_metadata(metadata)

        # Load metadata
        loaded = storage.load_metadata()

        assert loaded is not None
        assert loaded.provider_name == "test_provider"
        assert loaded.is_valid is False
        assert loaded.cookie_count == 5

    def test_load_metadata_nonexistent(self, temp_profile_dir: Path) -> None:
        """Test loading non-existent metadata returns None."""
        storage = CookieStorage(temp_profile_dir)

        assert storage.load_metadata() is None

    def test_update_metadata(self, temp_profile_dir: Path) -> None:
        """Test updating specific metadata fields."""
        storage = CookieStorage(temp_profile_dir)

        # Create initial metadata
        metadata = SessionMetadata(provider_name="test_provider", cookie_count=5)
        storage.save_metadata(metadata)

        # Update specific fields
        storage.update_metadata(cookie_count=10, is_valid=False)

        # Verify updates
        loaded = storage.load_metadata()
        assert loaded.cookie_count == 10
        assert loaded.is_valid is False
        assert loaded.provider_name == "test_provider"  # Unchanged

    def test_mark_validated(self, temp_profile_dir: Path) -> None:
        """Test mark_validated updates timestamp."""
        storage = CookieStorage(temp_profile_dir)

        # Create initial metadata
        metadata = SessionMetadata(provider_name="test_provider")
        storage.save_metadata(metadata)

        original_timestamp = metadata.last_validated

        # Mark as validated
        storage.mark_validated()

        # Verify timestamp updated
        loaded = storage.load_metadata()
        assert loaded.last_validated > original_timestamp

    def test_mark_invalid(self, temp_profile_dir: Path) -> None:
        """Test mark_invalid sets session to invalid."""
        storage = CookieStorage(temp_profile_dir)

        # Create initial metadata
        metadata = SessionMetadata(provider_name="test_provider")
        storage.save_metadata(metadata)

        # Mark as invalid
        storage.mark_invalid()

        # Verify flag updated
        loaded = storage.load_metadata()
        assert loaded.is_valid is False

    def test_session_exists(self, temp_profile_dir: Path, sample_cookies: list[dict]) -> None:
        """Test session_exists checks for required files."""
        storage = CookieStorage(temp_profile_dir)

        # Initially no session
        assert not storage.session_exists()

        # Save cookies
        metadata = SessionMetadata(provider_name="test_provider")
        storage.save_cookies(sample_cookies, metadata)

        # Now session exists
        assert storage.session_exists()

    def test_delete_session(self, temp_profile_dir: Path, sample_cookies: list[dict]) -> None:
        """Test delete_session removes all session files."""
        storage = CookieStorage(temp_profile_dir)

        # Save session
        metadata = SessionMetadata(provider_name="test_provider")
        storage.save_cookies(sample_cookies, metadata)

        assert storage.session_exists()

        # Delete session
        storage.delete_session()

        # Verify files removed
        assert not storage.cookies_path.exists()
        assert not storage.key_path.exists()
        assert not storage.metadata_path.exists()

    def test_is_corrupted(self, temp_profile_dir: Path) -> None:
        """Test is_corrupted detects corrupted session files."""
        storage = CookieStorage(temp_profile_dir)

        # No session - not corrupted
        assert not storage.is_corrupted()

        # Create invalid cookie file
        storage.cookies_path.write_text("corrupted data")

        # Missing key file - not considered corrupted (just incomplete)
        assert not storage.is_corrupted()

    def test_cleanup_corrupted(self, temp_profile_dir: Path) -> None:
        """Test cleanup_corrupted removes corrupted files."""
        storage = CookieStorage(temp_profile_dir)

        # Create corrupted session
        storage.cookies_path.write_text("corrupted data")
        storage.key_path.write_text("invalid key")

        # Verify corrupted
        assert storage.is_corrupted()

        # Cleanup
        storage.cleanup_corrupted()

        # Verify files removed
        assert not storage.cookies_path.exists()
        assert not storage.key_path.exists()

    def test_save_empty_cookies_fails(self, temp_profile_dir: Path) -> None:
        """Test saving empty cookies raises ValueError."""
        storage = CookieStorage(temp_profile_dir)

        with pytest.raises(ValueError, match="Cannot save empty cookie list"):
            storage.save_cookies([])
