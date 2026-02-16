"""
Cookie encryption utilities for secure session storage.

Uses AES-256-GCM via Fernet for encrypting cookies at rest.
"""

import json
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken


class CookieEncryption:
    """
    Handles cookie encryption and decryption using Fernet (AES-256-GCM).

    Provides:
    - Key generation and storage
    - Cookie encryption/decryption
    - Key file management with secure permissions
    """

    ENCRYPTION_VERSION = "1.0"

    def __init__(self, key_path: Path) -> None:
        """
        Initialize cookie encryption with key file path.

        Args:
            key_path: Path to encryption key file (cookies.json.key)
        """
        self.key_path = key_path
        self._cipher: Fernet | None = None

    def _load_or_generate_key(self) -> bytes:
        """
        Load existing encryption key or generate new one.

        Returns:
            Fernet encryption key

        Raises:
            OSError: If key file cannot be created
        """
        if self.key_path.exists():
            # Load existing key
            return self.key_path.read_bytes()

        # Generate new key
        key = Fernet.generate_key()

        # Create parent directories if needed
        self.key_path.parent.mkdir(parents=True, exist_ok=True)

        # Write key with restricted permissions
        self.key_path.write_bytes(key)

        # Set file permissions to 600 (owner read/write only)
        # This works on Unix systems
        try:
            import stat

            self.key_path.chmod(0o600)
        except (OSError, AttributeError):
            # Windows or unsupported platform
            pass

        return key

    @property
    def cipher(self) -> Fernet:
        """Get Fernet cipher instance (lazy loaded)."""
        if self._cipher is None:
            key = self._load_or_generate_key()
            self._cipher = Fernet(key)
        return self._cipher

    def encrypt_cookies(self, cookies: list[dict[str, Any]]) -> str:
        """
        Encrypt cookies to JSON string.

        Args:
            cookies: List of cookie dictionaries

        Returns:
            Encrypted JSON string

        Raises:
            ValueError: If cookies are empty or invalid
        """
        if not cookies:
            raise ValueError("Cannot encrypt empty cookie list")

        # Serialize cookies to JSON
        cookie_json = json.dumps(cookies)

        # Encrypt using Fernet
        encrypted_bytes = self.cipher.encrypt(cookie_json.encode())

        return encrypted_bytes.decode()

    def decrypt_cookies(self, encrypted_data: str) -> list[dict[str, Any]]:
        """
        Decrypt cookies from encrypted string.

        Args:
            encrypted_data: Encrypted cookie string

        Returns:
            List of cookie dictionaries

        Raises:
            InvalidToken: If decryption fails (wrong key or corrupted data)
            ValueError: If decrypted data is invalid JSON
        """
        try:
            # Decrypt using Fernet
            decrypted_bytes = self.cipher.decrypt(encrypted_data.encode())

            # Deserialize from JSON
            cookie_json = decrypted_bytes.decode()
            cookies = json.loads(cookie_json)

            if not isinstance(cookies, list):
                raise ValueError("Decrypted cookies must be a list")

            return cookies

        except InvalidToken as exc:
            raise InvalidToken(
                "Failed to decrypt cookies. Key may be incorrect or data corrupted."
            ) from exc
        except json.JSONDecodeError as exc:
            raise ValueError(f"Decrypted data is not valid JSON: {exc}") from exc

    def rotate_key(self) -> None:
        """
        Rotate encryption key and generate new one.

        Warning: Old encrypted cookies will become unreadable after rotation.
        """
        # Delete old key
        if self.key_path.exists():
            self.key_path.unlink()

        # Reset cipher to force new key generation
        self._cipher = None

    def key_exists(self) -> bool:
        """Check if encryption key file exists."""
        return self.key_path.exists()

    def delete_key(self) -> None:
        """Delete encryption key file."""
        if self.key_path.exists():
            self.key_path.unlink()
            self._cipher = None
