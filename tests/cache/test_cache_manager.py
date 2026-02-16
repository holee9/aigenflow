"""
Tests for cache module following SPEC-ENHANCE-004 requirements.

This module tests the caching system including:
- FR-1: Cache key generation with SHA-256
- FR-2: File system cache storage
- US-1: Cached response reuse
- US-5: Cache management (list, clear, stats)
"""

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from src.cache.key_generator import CacheKeyGenerator
from src.cache.manager import CacheManager
from src.cache.storage import CacheStorage
from src.core.models import AgentType
from src.gateway.models import GatewayResponse


class TestCacheKeyGenerator:
    """Test CacheKeyGenerator following FR-1 requirements."""

    def test_generate_key_with_prompt_only(self):
        """Test key generation with prompt only."""
        generator = CacheKeyGenerator()
        prompt = "Test prompt for business plan"
        key = generator.generate(prompt=prompt)

        # Should be a hex string (SHA-256)
        assert isinstance(key, str)
        assert len(key) == 64
        assert all(c in "0123456789abcdef" for c in key)

    def test_generate_key_with_context(self):
        """Test key generation includes context hash."""
        generator = CacheKeyGenerator()
        prompt = "Test prompt"
        context = {"phase": 1, "previous_summary": "Summary text"}
        key1 = generator.generate(prompt=prompt, context=context)
        key2 = generator.generate(prompt=prompt)

        # Different context should produce different keys
        assert key1 != key2

    def test_generate_key_with_agent_type(self):
        """Test key generation includes agent type."""
        generator = CacheKeyGenerator()
        prompt = "Test prompt"
        key1 = generator.generate(prompt=prompt, agent_type=AgentType.CLAUDE)
        key2 = generator.generate(prompt=prompt, agent_type=AgentType.CHATGPT)

        # Different agent types should produce different keys
        assert key1 != key2

    def test_generate_key_with_phase(self):
        """Test key generation includes phase number."""
        generator = CacheKeyGenerator()
        prompt = "Test prompt"
        key1 = generator.generate(prompt=prompt, phase=1)
        key2 = generator.generate(prompt=prompt, phase=2)

        # Different phases should produce different keys
        assert key1 != key2

    def test_generate_key_consistency(self):
        """Test same inputs produce same key (deterministic)."""
        generator = CacheKeyGenerator()
        prompt = "Test prompt"
        context = {"phase": 1}

        key1 = generator.generate(
            prompt=prompt, context=context, agent_type=AgentType.CLAUDE, phase=1
        )
        key2 = generator.generate(
            prompt=prompt, context=context, agent_type=AgentType.CLAUDE, phase=1
        )

        assert key1 == key2

    def test_generate_key_normalization(self):
        """Test whitespace normalization in prompt."""
        generator = CacheKeyGenerator()
        prompt1 = "Test  prompt\nwith  spaces"
        prompt2 = "Test prompt with spaces"

        # After normalization, keys should match
        key1 = generator.generate(prompt=prompt1)
        key2 = generator.generate(prompt=prompt2)
        assert key1 == key2

    def test_generate_key_case_sensitivity(self):
        """Test case sensitivity in prompt."""
        generator = CacheKeyGenerator()
        prompt1 = "Test prompt"
        prompt2 = "test prompt"

        # Different cases should produce different keys
        key1 = generator.generate(prompt=prompt1)
        key2 = generator.generate(prompt=prompt2)
        assert key1 != key2


class TestCacheStorage:
    """Test CacheStorage following FR-2 requirements."""

    @pytest.fixture
    def temp_cache_dir(self, tmp_path: Path) -> Path:
        """Create temporary cache directory."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    @pytest.fixture
    def storage(self, temp_cache_dir: Path) -> CacheStorage:
        """Create CacheStorage instance."""
        return CacheStorage(cache_dir=temp_cache_dir)

    @pytest.fixture
    def sample_response(self) -> GatewayResponse:
        """Create sample GatewayResponse."""
        return GatewayResponse(
            content="Test response content",
            success=True,
            tokens_used=100,
            response_time=1.5,
            metadata={"agent_type": "claude", "model": "claude-3-5-sonnet"},
        )

    def test_init_creates_directory_structure(self, temp_cache_dir: Path):
        """Test storage initialization creates required directories."""
        CacheStorage(cache_dir=temp_cache_dir)

        assert (temp_cache_dir / "responses").exists()
        assert (temp_cache_dir / "responses").is_dir()

    def test_save_and_retrieve(self, storage: CacheStorage, sample_response: GatewayResponse):
        """Test saving and retrieving cache entry."""
        key = "test_key_123"
        ttl_hours = 24

        # Save
        storage.save(key=key, response=sample_response, ttl_hours=ttl_hours)

        # Retrieve
        retrieved = storage.get(key)

        assert retrieved is not None
        assert retrieved.content == sample_response.content
        assert retrieved.success == sample_response.success
        assert retrieved.tokens_used == sample_response.tokens_used

    def test_get_nonexistent_key(self, storage: CacheStorage):
        """Test retrieving non-existent key returns None."""
        result = storage.get("nonexistent_key")
        assert result is None

    def test_delete(self, storage: CacheStorage, sample_response: GatewayResponse):
        """Test deleting cache entry."""
        key = "test_key_delete"
        storage.save(key=key, response=sample_response, ttl_hours=24)

        # Verify exists
        assert storage.get(key) is not None

        # Delete
        storage.delete(key)

        # Verify deleted
        assert storage.get(key) is None

    def test_clear_all(self, storage: CacheStorage, sample_response: GatewayResponse):
        """Test clearing all cache entries."""
        # Save multiple entries
        for i in range(3):
            storage.save(key=f"key_{i}", response=sample_response, ttl_hours=24)

        # Clear all
        cleared_count = storage.clear()
        assert cleared_count == 3

        # Verify all deleted
        assert storage.get("key_0") is None
        assert storage.get("key_1") is None
        assert storage.get("key_2") is None

    def test_list_entries(self, storage: CacheStorage, sample_response: GatewayResponse):
        """Test listing cache entries."""
        # Save entries with different creation times
        storage.save(key="key_1", response=sample_response, ttl_hours=24)
        storage.save(key="key_2", response=sample_response, ttl_hours=24)

        entries = storage.list()

        assert len(entries) == 2
        assert any(e.key == "key_1" for e in entries)
        assert any(e.key == "key_2" for e in entries)

    def test_expired_entry_returns_none(
        self, storage: CacheStorage, sample_response: GatewayResponse
    ):
        """Test expired entries are not returned."""
        key = "expired_key"

        # Save with TTL that has already expired
        storage.save(key=key, response=sample_response, ttl_hours=-1)

        # Should return None due to expiration
        result = storage.get(key)
        assert result is None

    def test_lru_eviction(self, temp_cache_dir: Path):
        """Test LRU eviction when max_size_mb is exceeded."""
        # Create storage with small max size (1MB)
        storage = CacheStorage(cache_dir=temp_cache_dir, max_size_mb=1)

        # Create large response (~200KB each)
        large_response = GatewayResponse(
            content="x" * 200_000,  # 200KB
            success=True,
        )

        # Save 10 entries (total ~2MB, exceeding 1MB limit)
        for i in range(10):
            storage.save(key=f"large_key_{i}", response=large_response, ttl_hours=24)

        # LRU should have evicted oldest entries
        # After 10 saves, we should have fewer than 10 entries
        entries = storage.list()
        assert len(entries) < 10  # Some entries were evicted

    def test_get_stats(self, storage: CacheStorage, sample_response: GatewayResponse):
        """Test getting cache statistics."""
        # Save some entries
        storage.save(key="key_1", response=sample_response, ttl_hours=24)
        storage.save(key="key_2", response=sample_response, ttl_hours=24)

        stats = storage.get_stats()

        assert stats.total_entries == 2
        assert stats.total_size_bytes > 0
        assert stats.hit_count == 0
        assert stats.miss_count == 0

    def test_increment_hit_miss_counters(
        self, storage: CacheStorage, sample_response: GatewayResponse
    ):
        """Test hit and miss counters."""
        storage.save(key="test_key", response=sample_response, ttl_hours=24)

        # Hit
        storage.get("test_key")
        stats = storage.get_stats()
        assert stats.hit_count == 1
        assert stats.miss_count == 0

        # Miss
        storage.get("nonexistent_key")
        stats = storage.get_stats()
        assert stats.hit_count == 1
        assert stats.miss_count == 1


class TestCacheManager:
    """Test CacheManager following US-1 and US-5 requirements."""

    @pytest.fixture
    def temp_cache_dir(self, tmp_path: Path) -> Path:
        """Create temporary cache directory."""
        return tmp_path / "cache"

    @pytest.fixture
    def manager(self, temp_cache_dir: Path) -> CacheManager:
        """Create CacheManager instance."""
        return CacheManager(cache_dir=temp_cache_dir)

    @pytest.fixture
    def sample_response(self) -> GatewayResponse:
        """Create sample GatewayResponse."""
        return GatewayResponse(
            content="Test response content",
            success=True,
            tokens_used=100,
            response_time=1.5,
        )

    @pytest.mark.asyncio
    async def test_get_returns_cached_response(
        self, manager: CacheManager, sample_response: GatewayResponse
    ):
        """Test retrieving cached response."""
        prompt = "Test prompt"
        key = manager.key_generator.generate(prompt=prompt)

        # Set cache
        await manager.set(key=key, response=sample_response)

        # Get from cache
        cached = await manager.get(key)

        assert cached is not None
        assert cached.content == sample_response.content

    @pytest.mark.asyncio
    async def test_get_returns_none_for_miss(self, manager: CacheManager):
        """Test get returns None when key not found."""
        result = await manager.get("nonexistent_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_with_default_ttl(
        self, manager: CacheManager, sample_response: GatewayResponse
    ):
        """Test set with default TTL."""
        key = "test_key"
        await manager.set(key=key, response=sample_response)

        # Should be retrievable immediately
        result = await manager.get(key)
        assert result is not None

    @pytest.mark.asyncio
    async def test_set_with_custom_ttl(
        self, manager: CacheManager, sample_response: GatewayResponse
    ):
        """Test set with custom TTL."""
        key = "test_key_ttl"
        await manager.set(key=key, response=sample_response, ttl_hours=48)

        result = await manager.get(key)
        assert result is not None

    @pytest.mark.asyncio
    async def test_invalidate(self, manager: CacheManager, sample_response: GatewayResponse):
        """Test invalidating cache entry."""
        key = "test_key_invalidate"
        await manager.set(key=key, response=sample_response)

        # Verify exists
        assert await manager.get(key) is not None

        # Invalidate
        await manager.invalidate(key)

        # Verify deleted
        assert await manager.get(key) is None

    @pytest.mark.asyncio
    async def test_get_or_compute_hit(
        self, manager: CacheManager, sample_response: GatewayResponse
    ):
        """Test get_or_compute returns cached value on hit."""
        key = "test_key_compute"
        await manager.set(key=key, response=sample_response)

        compute_fn = AsyncMock(return_value=GatewayResponse(content="new", success=True))

        result = await manager.get_or_compute(key=key, compute_fn=compute_fn)

        # Should return cached value, not call compute function
        assert result.content == sample_response.content
        compute_fn.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_get_or_compute_miss(self, manager: CacheManager):
        """Test get_or_compute calls compute function on miss."""
        key = "test_key_compute_miss"
        new_response = GatewayResponse(content="new content", success=True)
        compute_fn = AsyncMock(return_value=new_response)

        result = await manager.get_or_compute(key=key, compute_fn=compute_fn)

        # Should call compute function and cache result
        assert result.content == "new content"
        compute_fn.assert_awaited_once()

        # Verify cached
        cached = await manager.get(key)
        assert cached is not None
        assert cached.content == "new content"

    def test_get_stats(self, manager: CacheManager):
        """Test getting cache statistics."""
        stats = manager.get_stats()

        assert stats.total_entries == 0
        assert stats.total_size_bytes == 0
        assert stats.hit_count == 0
        assert stats.miss_count == 0
        assert stats.hit_rate == 0.0

    @pytest.mark.asyncio
    async def test_hit_rate_calculation(
        self, manager: CacheManager, sample_response: GatewayResponse
    ):
        """Test hit rate calculation."""
        key = "test_key_hit_rate"
        await manager.set(key=key, response=sample_response)

        # 2 hits, 1 miss = 66.7% hit rate
        await manager.get(key)
        await manager.get(key)
        await manager.get("nonexistent")

        stats = manager.get_stats()
        assert stats.hit_count == 2
        assert stats.miss_count == 1
        assert abs(stats.hit_rate - 0.666) < 0.01  # ~66.7%
