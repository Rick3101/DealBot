"""
Query cache implementation for optimizing database operations.
Provides in-memory caching with TTL (time-to-live) support.
"""

import hashlib
import json
import logging
import threading
import time
from typing import Any, Dict, Optional, Tuple
from datetime import datetime, timedelta


class QueryCache:
    """
    Thread-safe query cache with TTL support.
    Caches query results to reduce database load for frequently accessed data.
    """

    def __init__(self, default_ttl: int = 300, max_size: int = 1000):
        """
        Initialize query cache.

        Args:
            default_ttl: Default time-to-live in seconds (5 minutes)
            max_size: Maximum number of cached entries
        """
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._access_times: Dict[str, float] = {}
        self.logger = logging.getLogger(__name__)

    def _generate_cache_key(self, query: str, params: Tuple = ()) -> str:
        """Generate cache key from query and parameters."""
        # Create a unique key based on query and parameters
        key_data = {
            'query': query.strip(),
            'params': params if params else ()
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, query: str, params: Tuple = ()) -> Optional[Any]:
        """
        Get cached result for query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Cached result or None if not found/expired
        """
        cache_key = self._generate_cache_key(query, params)

        with self._lock:
            if cache_key not in self._cache:
                return None

            cache_entry = self._cache[cache_key]
            current_time = time.time()

            # Check if expired
            if current_time > cache_entry['expires_at']:
                del self._cache[cache_key]
                if cache_key in self._access_times:
                    del self._access_times[cache_key]
                self.logger.debug(f"Cache entry expired: {cache_key[:8]}...")
                return None

            # Update access time
            self._access_times[cache_key] = current_time
            self.logger.debug(f"Cache hit: {cache_key[:8]}...")
            return cache_entry['data']

    def set(self, query: str, params: Tuple, data: Any, ttl: Optional[int] = None) -> None:
        """
        Cache query result.

        Args:
            query: SQL query string
            params: Query parameters
            data: Query result to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        if data is None:
            return  # Don't cache None results

        cache_key = self._generate_cache_key(query, params)
        cache_ttl = ttl if ttl is not None else self.default_ttl
        current_time = time.time()
        expires_at = current_time + cache_ttl

        with self._lock:
            # Evict least recently used entries if cache is full
            if len(self._cache) >= self.max_size and cache_key not in self._cache:
                self._evict_lru()

            self._cache[cache_key] = {
                'data': data,
                'expires_at': expires_at,
                'created_at': current_time
            }
            self._access_times[cache_key] = current_time

        self.logger.debug(f"Cached query result: {cache_key[:8]}... (TTL: {cache_ttl}s)")

    def _evict_lru(self) -> None:
        """Evict least recently used cache entries."""
        if not self._access_times:
            return

        # Find the oldest accessed entry
        oldest_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])

        if oldest_key in self._cache:
            del self._cache[oldest_key]
        del self._access_times[oldest_key]

        self.logger.debug(f"Evicted LRU cache entry: {oldest_key[:8]}...")

    def invalidate(self, pattern: Optional[str] = None) -> int:
        """
        Invalidate cache entries.

        Args:
            pattern: If provided, only invalidate keys containing this pattern

        Returns:
            Number of entries invalidated
        """
        with self._lock:
            if pattern is None:
                # Clear all cache
                count = len(self._cache)
                self._cache.clear()
                self._access_times.clear()
                self.logger.info(f"Cleared entire cache: {count} entries")
                return count

            # Pattern-based invalidation
            keys_to_remove = []
            for cache_key in self._cache.keys():
                cache_entry = self._cache[cache_key]
                if pattern.lower() in str(cache_entry.get('data', '')).lower():
                    keys_to_remove.append(cache_key)

            for key in keys_to_remove:
                if key in self._cache:
                    del self._cache[key]
                if key in self._access_times:
                    del self._access_times[key]

            self.logger.info(f"Invalidated {len(keys_to_remove)} cache entries matching pattern: {pattern}")
            return len(keys_to_remove)

    def cleanup_expired(self) -> int:
        """
        Remove expired cache entries.

        Returns:
            Number of expired entries removed
        """
        current_time = time.time()
        expired_keys = []

        with self._lock:
            for cache_key, cache_entry in self._cache.items():
                if current_time > cache_entry['expires_at']:
                    expired_keys.append(cache_key)

            for key in expired_keys:
                if key in self._cache:
                    del self._cache[key]
                if key in self._access_times:
                    del self._access_times[key]

        if expired_keys:
            self.logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            current_time = time.time()
            expired_count = sum(
                1 for entry in self._cache.values()
                if current_time > entry['expires_at']
            )

            return {
                'total_entries': len(self._cache),
                'expired_entries': expired_count,
                'active_entries': len(self._cache) - expired_count,
                'max_size': self.max_size,
                'default_ttl': self.default_ttl,
                'memory_usage_estimate': sum(
                    len(str(entry)) for entry in self._cache.values()
                )
            }

    def cache_query_result(self, query_func, query: str, params: Tuple = (), ttl: Optional[int] = None) -> Any:
        """
        Decorator-style cache wrapper for query functions.

        Args:
            query_func: Function that executes the query
            query: SQL query string
            params: Query parameters
            ttl: Time-to-live in seconds

        Returns:
            Query result (from cache or fresh execution)
        """
        # Check cache first
        cached_result = self.get(query, params)
        if cached_result is not None:
            return cached_result

        # Execute query and cache result
        result = query_func(query, params)
        if result is not None:
            self.set(query, params, result, ttl)

        return result


# Global cache instance
_query_cache = QueryCache()


def get_query_cache() -> QueryCache:
    """Get global query cache instance."""
    return _query_cache


def cached_query(ttl: Optional[int] = None):
    """
    Decorator for caching query results.

    Args:
        ttl: Time-to-live in seconds (uses cache default if None)

    Usage:
        @cached_query(ttl=300)
        def get_expeditions(query, params):
            return execute_query(query, params)
    """
    def decorator(func):
        def wrapper(query: str, params: Tuple = (), *args, **kwargs):
            cache = get_query_cache()

            # Check cache first
            cached_result = cache.get(query, params)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(query, params, *args, **kwargs)
            if result is not None:
                cache.set(query, params, result, ttl)

            return result
        return wrapper
    return decorator


def invalidate_cache(pattern: Optional[str] = None) -> int:
    """
    Invalidate cache entries globally.

    Args:
        pattern: Pattern to match for selective invalidation

    Returns:
        Number of entries invalidated
    """
    cache = get_query_cache()
    return cache.invalidate(pattern)


def cleanup_cache() -> int:
    """
    Clean up expired cache entries globally.

    Returns:
        Number of expired entries removed
    """
    cache = get_query_cache()
    return cache.cleanup_expired()


def get_cache_stats() -> Dict[str, Any]:
    """Get global cache statistics."""
    cache = get_query_cache()
    return cache.get_stats()