"""
Cookie storage manager for encrypted session persistence.

Handles saving, loading, and validation of encrypted cookies with metadata.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from gateway.cookie_encryption import CookieEncryption, InvalidToken


class SessionMetadata(BaseModel):
    """Session metadata for tracking session lifecycle."""

    model_config = {"frozen": False}

    provider_name: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_validated: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_valid: bool = True
    login_method: str = "manual"
    browser_version: str = "chromium-121.0"
    user_agent_hash: str | None = None
    cookie_count: int = 0
    encryption_version: str = "1.0"

    def mark_validated(self) -> None:
        """Update last_validated timestamp to now."""
        self.last_validated = datetime.now(timezone.utc).isoformat()

    def mark_invalid(self) -> None:
        """Mark session as invalid."""
        self.is_valid = False


class CookieStorage:
    """
    Manages encrypted cookie storage with metadata tracking.

    Provides:
    - Encrypted cookie save/load
    - Session metadata management
    - Corrupted file recovery
    - Profile directory management
    """

    COOKIES_FILE = "cookies.json"
    COOKES_KEY_FILE = "cookies.json.key"
    METADATA_FILE = "session_meta.json"

    def __init__(self, profile_dir: Path) -> None:
        """
        Initialize cookie storage for a provider profile.

        Args:
            profile_dir: Provider profile directory (e.g., ~/.aigenflow/profiles/chatgpt/)
        """
        self.profile_dir = Path(profile_dir)
        self.profile_dir.mkdir(parents=True, exist_ok=True)

        # Initialize encryption
        self.encryption = CookieEncryption(self.key_path)

    @property
    def cookies_path(self) -> Path:
        """Get path to cookies file."""
        return self.profile_dir / self.COOKIES_FILE

    @property
    def key_path(self) -> Path:
        """Get path to encryption key file."""
        return self.profile_dir / self.COOKES_KEY_FILE

    @property
    def metadata_path(self) -> Path:
        """Get path to metadata file."""
        return self.profile_dir / self.METADATA_FILE

    def save_cookies(
        self,
        cookies: list[dict[str, Any]],
        metadata: SessionMetadata | None = None,
    ) -> None:
        """
        Save encrypted cookies to disk with metadata.

        Args:
            cookies: List of cookie dictionaries
            metadata: Optional session metadata (created if None)

        Raises:
            OSError: If file cannot be written
            ValueError: If cookies are empty
        """
        if not cookies:
            raise ValueError("Cannot save empty cookie list")

        # Create metadata if not provided
        if metadata is None:
            metadata = SessionMetadata(
                provider_name=self.profile_dir.name,
                cookie_count=len(cookies),
            )
        else:
            metadata.cookie_count = len(cookies)

        # Encrypt cookies
        encrypted_data = self.encryption.encrypt_cookies(cookies)

        # Write encrypted cookies to file
        self.cookies_path.write_text(encrypted_data)

        # Write metadata
        self.save_metadata(metadata)

    def load_cookies(self) -> list[dict[str, Any]]:
        """
        Load and decrypt cookies from disk.

        Returns:
            List of cookie dictionaries

        Raises:
            FileNotFoundError: If cookies file doesn't exist
            InvalidToken: If decryption fails (corrupted or wrong key)
            ValueError: If data is invalid
        """
        if not self.cookies_path.exists():
            raise FileNotFoundError(f"Cookies file not found: {self.cookies_path}")

        # Read encrypted data
        encrypted_data = self.cookies_path.read_text()

        # Decrypt and return
        return self.encryption.decrypt_cookies(encrypted_data)

    def save_metadata(self, metadata: SessionMetadata) -> None:
        """
        Save session metadata to disk.

        Args:
            metadata: SessionMetadata instance
        """
        self.metadata_path.write_text(
            metadata.model_dump_json(indent=2),
        )

    def load_metadata(self) -> SessionMetadata | None:
        """
        Load session metadata from disk.

        Returns:
            SessionMetadata instance, or None if file doesn't exist
        """
        if not self.metadata_path.exists():
            return None

        try:
            data = json.loads(self.metadata_path.read_text())
            return SessionMetadata(**data)
        except (json.JSONDecodeError, ValueError):
            return None

    def update_metadata(self, **updates: Any) -> None:
        """
        Update specific metadata fields.

        Args:
            **updates: Field names and values to update
        """
        metadata = self.load_metadata()
        if metadata is None:
            metadata = SessionMetadata(provider_name=self.profile_dir.name)

        for field, value in updates.items():
            if hasattr(metadata, field):
                setattr(metadata, field, value)

        self.save_metadata(metadata)

    def mark_validated(self) -> None:
        """Mark session as validated (update timestamp)."""
        metadata = self.load_metadata()
        if metadata:
            metadata.mark_validated()
            self.save_metadata(metadata)

    def mark_invalid(self) -> None:
        """Mark session as invalid."""
        metadata = self.load_metadata()
        if metadata:
            metadata.mark_invalid()
            self.save_metadata(metadata)

    def session_exists(self) -> bool:
        """Check if session files exist."""
        return (
            self.cookies_path.exists()
            and self.key_path.exists()
        )

    def delete_session(self) -> None:
        """Delete all session files (cookies, key, metadata)."""
        if self.cookies_path.exists():
            self.cookies_path.unlink()

        if self.key_path.exists():
            self.key_path.unlink()

        if self.metadata_path.exists():
            self.metadata_path.unlink()

    def is_corrupted(self) -> bool:
        """
        Check if session files are corrupted.

        Returns:
            True if files exist but cannot be read/decrypted
        """
        if not self.session_exists():
            return False

        try:
            self.load_cookies()
            return False
        except (InvalidToken, ValueError, json.JSONDecodeError):
            return True

    def cleanup_corrupted(self) -> None:
        """Delete corrupted session files."""
        if self.is_corrupted():
            self.delete_session()
