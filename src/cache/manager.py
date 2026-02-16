"""
Cache manager following US-1 and US-5 requirements.

Provides high-level cache management interface:
- Get/Set cache entries
- Cache invalidation
- Statistics tracking
- Integration with agent router

Reference: SPEC-ENHANCE-004 US-1, US-5
"""

from collections.abc import Awaitable, Callable
from pathlib import Path

from cache.key_generator import CacheKeyGenerator
from cache.storage import CacheStats, CacheStorage
from gateway.models import GatewayResponse


class CacheManager:
    """
    High-level cache management for AI responses.

    Responsibilities:
    - Cache key generation and lookup
    - TTL-based expiration management
    - LRU deletion policy
    - Statistics collection
    """

    DEFAULT_TTL_HOURS = 24
    DEFAULT_MAX_SIZE_MB = 500

    def __init__(
        self,
        cache_dir: Path | None = None,
        max_size_mb: int = DEFAULT_MAX_SIZE_MB,
        default_ttl_hours: int = DEFAULT_TTL_HOURS,
    ) -> None:
        """
        Initialize cache manager.

        Args:
            cache_dir: Cache directory path (default: ~/.aigenflow/cache)
            max_size_mb: Maximum cache size in megabytes
            default_ttl_hours: Default TTL for cache entries
        """
        # Set default cache directory
        if cache_dir is None:
            home = Path.home()
            cache_dir = home / ".aigenflow" / "cache"

        self.cache_dir = cache_dir
        self.max_size_mb = max_size_mb
        self.default_ttl_hours = default_ttl_hours

        # Initialize components
        self.key_generator = CacheKeyGenerator()
        self.storage = CacheStorage(cache_dir=cache_dir, max_size_mb=max_size_mb)

    async def get(self, key: str) -> GatewayResponse | None:
        """
        Get cached response by key.

        Args:
            key: Cache key

        Returns:
            Cached response or None if not found/expired
        """
        return self.storage.get(key)

    async def set(
        self,
        key: str,
        response: GatewayResponse,
        ttl_hours: int | None = None,
    ) -> None:
        """
        Cache a response.

        Args:
            key: Cache key
            response: Response to cache
            ttl_hours: Time-to-live in hours (default: default_ttl_hours)
        """
        ttl = ttl_hours if ttl_hours is not None else self.default_ttl_hours
        self.storage.save(key=key, response=response, ttl_hours=ttl)

    async def invalidate(self, key: str) -> None:
        """
        Invalidate (delete) a cache entry.

        Args:
            key: Cache key to invalidate
        """
        self.storage.delete(key)

    async def get_or_compute(
        self,
        key: str,
        compute_fn: Callable[[], Awaitable[GatewayResponse]],
    ) -> GatewayResponse:
        """
        Get cached response or compute and cache.

        Args:
            key: Cache key
            compute_fn: Async function to compute response if cache miss

        Returns:
            Cached or newly computed response
        """
        # Try to get from cache
        cached = await self.get(key)
        if cached is not None:
            return cached

        # Cache miss - compute and cache
        response = await compute_fn()
        await self.set(key=key, response=response)

        return response

    def get_stats(self) -> CacheStats:
        """
        Get cache statistics.

        Returns:
            Current cache statistics
        """
        return self.storage.get_stats()

    async def clear(self) -> int:
        """
        Clear all cache entries.

        Returns:
            Number of entries deleted
        """
        return self.storage.clear()

    def list_entries(self) -> list[str]:
        """
        List all cache entry keys.

        Returns:
            List of cache keys
        """
        entries = self.storage.list()
        return [e.key for e in entries]
