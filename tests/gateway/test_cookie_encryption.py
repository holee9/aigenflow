"""
Tests for cookie encryption functionality.
"""

from pathlib import Path

import pytest
from cryptography.fernet import InvalidToken

from gateway.cookie_encryption import CookieEncryption


@pytest.fixture
def temp_key_path(tmp_path: Path) -> Path:
    """Create a temporary key file path."""
    return tmp_path / "test_key.key"


@pytest.fixture
def sample_cookies() -> list[dict]:
    """Create sample cookies for testing."""
    return [
        {
            "name": "__Secure-next-auth.session-token",
            "value": "test_session_token_value_12345",
            "domain": ".chat.openai.com",
            "path": "/",
            "expires": -1,
            "httpOnly": True,
            "secure": True,
            "sameSite": "Lax",
        },
        {
            "name": "_puid",
            "value": "user_id_12345",
            "domain": ".chat.openai.com",
            "path": "/",
            "expires": -1,
            "httpOnly": False,
            "secure": True,
            "sameSite": "Lax",
        },
    ]


class TestCookieEncryption:
    """Test suite for CookieEncryption class."""

    def test_key_generation(self, temp_key_path: Path) -> None:
        """Test that encryption key is generated and saved."""
        encryption = CookieEncryption(temp_key_path)

        # Access cipher property to trigger key generation
        _ = encryption.cipher

        # Verify key file was created
        assert temp_key_path.exists()

        # Verify key is valid Fernet key (44 bytes base64)
        key_data = temp_key_path.read_bytes()
        assert len(key_data) == 44

    def test_encrypt_cookies(self, temp_key_path: Path, sample_cookies: list[dict]) -> None:
        """Test cookie encryption."""
        encryption = CookieEncryption(temp_key_path)

        # Encrypt cookies
        encrypted = encryption.encrypt_cookies(sample_cookies)

        # Verify result is string
        assert isinstance(encrypted, str)

        # Verify encrypted data is not plaintext
        assert "session-token" not in encrypted
        assert "test_session_token" not in encrypted

        # Verify it's valid base64-like Fernet token
        assert len(encrypted) > 100

    def test_decrypt_cookies(self, temp_key_path: Path, sample_cookies: list[dict]) -> None:
        """Test cookie decryption."""
        encryption = CookieEncryption(temp_key_path)

        # Encrypt then decrypt
        encrypted = encryption.encrypt_cookies(sample_cookies)
        decrypted = encryption.decrypt_cookies(encrypted)

        # Verify decrypted cookies match original
        assert decrypted == sample_cookies

    def test_encrypt_decrypt_roundtrip(
        self,
        temp_key_path: Path,
        sample_cookies: list[dict],
    ) -> None:
        """Test full encrypt-decrypt cycle."""
        encryption = CookieEncryption(temp_key_path)

        # Encrypt
        encrypted = encryption.encrypt_cookies(sample_cookies)

        # Decrypt
        decrypted = encryption.decrypt_cookies(encrypted)

        # Verify all cookie fields are preserved
        assert len(decrypted) == len(sample_cookies)

        for original, restored in zip(sample_cookies, decrypted):
            assert original["name"] == restored["name"]
            assert original["value"] == restored["value"]
            assert original["domain"] == restored["domain"]

    def test_decrypt_with_wrong_key_fails(self, temp_key_path: Path, sample_cookies: list[dict]) -> None:
        """Test that decryption fails with wrong key."""
        # Encrypt with first key
        encryption1 = CookieEncryption(temp_key_path)
        encrypted = encryption1.encrypt_cookies(sample_cookies)

        # Try to decrypt with different key
        temp_key_path.unlink()  # Delete original key
        encryption2 = CookieEncryption(temp_key_path)  # Generates new key

        with pytest.raises(InvalidToken):
            encryption2.decrypt_cookies(encrypted)

    def test_key_persistence(self, temp_key_path: Path, sample_cookies: list[dict]) -> None:
        """Test that key persists across CookieEncryption instances."""
        # Encrypt with first instance
        encryption1 = CookieEncryption(temp_key_path)
        encrypted = encryption1.encrypt_cookies(sample_cookies)

        # Decrypt with second instance (should use same key)
        encryption2 = CookieEncryption(temp_key_path)
        decrypted = encryption2.decrypt_cookies(encrypted)

        assert decrypted == sample_cookies

    def test_key_exists(self, temp_key_path: Path) -> None:
        """Test key_exists method."""
        encryption = CookieEncryption(temp_key_path)

        # Initially key doesn't exist
        assert not encryption.key_exists()

        # Access cipher to generate key
        _ = encryption.cipher

        # Now key exists
        assert encryption.key_exists()

    def test_delete_key(self, temp_key_path: Path) -> None:
        """Test delete_key method."""
        encryption = CookieEncryption(temp_key_path)

        # Generate key
        _ = encryption.cipher
        assert encryption.key_exists()

        # Delete key
        encryption.delete_key()
        assert not encryption.key_exists()

    def test_rotate_key(self, temp_key_path: Path, sample_cookies: list[dict]) -> None:
        """Test key rotation."""
        encryption = CookieEncryption(temp_key_path)

        # Encrypt with original key
        encrypted1 = encryption.encrypt_cookies(sample_cookies)

        # Rotate key
        encryption.rotate_key()

        # Old encrypted data cannot be decrypted
        with pytest.raises(InvalidToken):
            encryption.decrypt_cookies(encrypted1)

        # New encryption works with new key
        encrypted2 = encryption.encrypt_cookies(sample_cookies)
        decrypted2 = encryption.decrypt_cookies(encrypted2)
        assert decrypted2 == sample_cookies

    def test_encrypt_empty_cookies_fails(self, temp_key_path: Path) -> None:
        """Test that encrypting empty cookies list raises ValueError."""
        encryption = CookieEncryption(temp_key_path)

        with pytest.raises(ValueError, match="Cannot encrypt empty cookie list"):
            encryption.encrypt_cookies([])

    def test_decrypt_invalid_json_fails(self, temp_key_path: Path) -> None:
        """Test that decrypting invalid JSON fails."""
        encryption = CookieEncryption(temp_key_path)

        # Encrypt valid data first to generate key
        valid_cookies = [{"name": "test", "value": "value"}]
        encrypted = encryption.encrypt_cookies(valid_cookies)

        # Corrupt the encrypted data
        corrupted = encrypted[:-10] + "corrupted"

        with pytest.raises(InvalidToken, match="Failed to decrypt"):
            encryption.decrypt_cookies(corrupted)
