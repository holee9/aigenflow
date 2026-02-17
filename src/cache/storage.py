"""
File system cache storage following FR-2 requirements.

Implements:
- File system based cache storage at ~/.aigenflow/cache/
- LRU (Least Recently Used) eviction policy
- TTL (Time-To-Live) based expiration
- Cache statistics tracking

Reference: SPEC-ENHANCE-004 FR-2
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from gateway.models import GatewayResponse


class CacheEntry(BaseModel):
    """A single cache entry with metadata."""

    key: str
    response: Any  # Store as dict during load, validate when accessed
    created_at: datetime
    expires_at: datetime
    access_count: int = 0
    last_accessed: datetime | None = None
    size_bytes: int = 0

    model_config = {"protected_namespaces": (), "arbitrary_types_allowed": True}

    def get_response(self) -> GatewayResponse:
        """Get response as GatewayResponse, converting if needed."""
        if isinstance(self.response, GatewayResponse):
            return self.response
        if isinstance(self.response, dict):
            return GatewayResponse(**self.response)
        return GatewayResponse(content=str(self.response), success=True)


class CacheStats(BaseModel):
    """Cache statistics."""

    total_entries: int = 0
    total_size_bytes: int = 0
    hit_count: int = 0
    miss_count: int = 0
    hit_rate: float = 0.0

    @property
    def total_size_mb(self) -> float:
        """Get total size in megabytes."""
        return self.total_size_bytes / (1024 * 1024)


class CacheStorage:
    """
    File system based cache storage with LRU eviction.

    Storage structure:
    cache_dir/
    ├── responses/
    │   ├── {cache_key}.json
    │   └── ...
    └── stats.json
    """

    DEFAULT_MAX_SIZE_MB = 500

    def __init__(
        self,
        cache_dir: Path,
        max_size_mb: int = DEFAULT_MAX_SIZE_MB,
    ) -> None:
        """
        Initialize cache storage.

        Args:
            cache_dir: Root cache directory
            max_size_mb: Maximum cache size in megabytes
        """
        self.cache_dir = cache_dir
        self.responses_dir = cache_dir / "responses"
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.stats_file = cache_dir / "stats.json"

        # Create directories
        self.responses_dir.mkdir(parents=True, exist_ok=True)

        # Load or initialize stats
        self._load_stats()

    def _load_stats(self) -> None:
        """Load statistics from file or initialize."""
        if self.stats_file.exists():
            try:
                with open(self.stats_file) as f:
                    data = json.load(f)
                    self._stats = CacheStats(**data)
            except (json.JSONDecodeError, ValueError):
                self._stats = CacheStats()
        else:
            self._stats = CacheStats()

    def _save_stats(self) -> None:
        """Save statistics to file."""
        with open(self.stats_file, "w") as f:
            json.dump(self._stats.model_dump(), f, indent=2, default=str)

    def _get_entry_path(self, key: str) -> Path:
        """Get file path for cache entry."""
        return self.responses_dir / f"{key}.json"

    def _calculate_entry_size(self, entry: CacheEntry) -> int:
        """Calculate size of entry in bytes."""
        return len(json.dumps(entry.model_dump(), default=str).encode())

    def save(
        self,
        key: str,
        response: GatewayResponse,
        ttl_hours: int = 24,
    ) -> None:
        """
        Save response to cache.

        Args:
            key: Cache key
            response: Response to cache
            ttl_hours: Time-to-live in hours
        """
        now = datetime.now()
        expires_at = now + timedelta(hours=ttl_hours)

        entry = CacheEntry(
            key=key,
            response=response,
            created_at=now,
            expires_at=expires_at,
            size_bytes=0,  # Will be calculated
        )

        # Calculate size
        entry.size_bytes = self._calculate_entry_size(entry)

        # Save to file
        entry_path = self._get_entry_path(key)
        with open(entry_path, "w") as f:
            json.dump(entry.model_dump(mode='json'), f)

        # Update stats
        self._stats.total_entries += 1
        self._stats.total_size_bytes += entry.size_bytes
        self._save_stats()

        # Evict if over size limit
        self._evict_if_needed()

    def get(self, key: str) -> GatewayResponse | None:
        """
        Get response from cache if exists and not expired.

        Args:
            key: Cache key

        Returns:
            Cached response or None if not found/expired
        """
        entry_path = self._get_entry_path(key)

        if not entry_path.exists():
            self._stats.miss_count += 1
            self._save_stats()
            return None

        try:
            with open(entry_path) as f:
                data = json.load(f)
                entry = CacheEntry(**data)

            # Check expiration
            if datetime.now() > entry.expires_at:
                # Delete expired entry
                self.delete(key)
                self._stats.miss_count += 1
                self._save_stats()
                return None

            # Update access tracking
            entry.access_count += 1
            entry.last_accessed = datetime.now()

            # Save updated entry
            with open(entry_path, "w") as f:
                json.dump(entry.model_dump(mode='json'), f)

            # Update stats
            self._stats.hit_count += 1
            self._update_hit_rate()
            self._save_stats()

            return entry.get_response()

        except (json.JSONDecodeError, ValueError):
            # Corrupted entry, delete it
            self.delete(key)
            self._stats.miss_count += 1
            self._save_stats()
            return None

    def delete(self, key: str) -> None:
        """
        Delete entry from cache.

        Args:
            key: Cache key
        """
        entry_path = self._get_entry_path(key)

        if entry_path.exists():
            # Read entry to get size
            try:
                with open(entry_path) as f:
                    data = json.load(f)
                    entry = CacheEntry(**data)
                    size = entry.size_bytes
            except (json.JSONDecodeError, ValueError):
                size = 0

            # Delete file
            entry_path.unlink()

            # Update stats
            self._stats.total_entries -= 1
            self._stats.total_size_bytes -= size
            self._save_stats()

    def clear(self) -> int:
        """
        Clear all cache entries.

        Returns:
            Number of entries deleted
        """
        count = 0
        for entry_file in self.responses_dir.glob("*.json"):
            entry_file.unlink()
            count += 1

        # Reset stats
        self._stats = CacheStats()
        self._save_stats()

        return count

    def list(self) -> list[CacheEntry]:
        """
        List all cache entries.

        Returns:
            List of cache entries (excluding expired)
        """
        entries = []
        now = datetime.now()

        for entry_file in self.responses_dir.glob("*.json"):
            try:
                with open(entry_file) as f:
                    data = json.load(f)
                    entry = CacheEntry(**data)

                    # Skip expired entries
                    if now > entry.expires_at:
                        continue

                    entries.append(entry)
            except (json.JSONDecodeError, ValueError):
                # Skip corrupted entries
                continue

        # Sort by last accessed (most recently used first)
        entries.sort(key=lambda e: e.last_accessed or e.created_at, reverse=True)

        return entries

    def get_stats(self) -> CacheStats:
        """
        Get current cache statistics.

        Returns:
            Cache statistics
        """
        # Recalculate from disk to ensure accuracy
        self._recalculate_stats()
        return self._stats

    def _update_hit_rate(self) -> None:
        """Update hit rate calculation."""
        total = self._stats.hit_count + self._stats.miss_count
        if total > 0:
            self._stats.hit_rate = self._stats.hit_count / total

    def _recalculate_stats(self) -> None:
        """Recalculate statistics from disk."""
        entries = self.list()
        self._stats.total_entries = len(entries)
        self._stats.total_size_bytes = sum(e.size_bytes for e in entries)
        self._update_hit_rate()
        self._save_stats()

    def _evict_if_needed(self) -> None:
        """
        Evict least recently used entries if over size limit.

        Implements LRU eviction policy.
        """
        while self._stats.total_size_bytes > self.max_size_bytes:
            # Get all entries sorted by LRU
            entries = self.list()

            if not entries:
                break

            # Evict least recently used (last in list)
            lru_entry = entries[-1]
            self.delete(lru_entry.key)

            # Update stats
            self._stats.total_entries = len(entries) - 1
            self._stats.total_size_bytes -= lru_entry.size_bytes
