"""
Rate limiter abstraction supporting in-memory sliding window and Redis-backed storage.
"""
from abc import ABC, abstractmethod
from collections import defaultdict
import threading
import time
from typing import Optional, Tuple

from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger("rate_limiter_core")


class BaseRateLimiter(ABC):
    """Abstract interface for rate limiting backends."""

    @abstractmethod
    async def is_rate_limited(self, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
        """
        Check if an operation is rate limited.

        Args:
            key: Unique key (e.g., ip:path or user_id:path).
            max_requests: Maximum allowed requests within the window.
            window_seconds: Time window in seconds.

        Returns:
            (is_limited: bool, retry_after_seconds: int)
        """
        pass


class InMemoryRateLimiter(BaseRateLimiter):
    """Thread-safe sliding-window in-memory rate limiter."""

    def __init__(self):
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()
        self._last_cleanup = time.time()

    async def is_rate_limited(self, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
        now = time.time()

        with self._lock:
            # Periodic cleanup of completely stale keys every 5 minutes
            if now - self._last_cleanup > 300:
                stale_threshold = now - 600
                keys_to_delete = [
                    k for k, timestamps in self._requests.items()
                    if not timestamps or timestamps[-1] < stale_threshold
                ]
                for k in keys_to_delete:
                    del self._requests[k]
                self._last_cleanup = now

            timestamps = self._requests[key]
            # Remove entries outside sliding window
            cutoff = now - window_seconds
            self._requests[key] = [t for t in timestamps if t > cutoff]
            timestamps = self._requests[key]

            if len(timestamps) >= max_requests:
                oldest = timestamps[0]
                retry_after = max(1, int(window_seconds - (now - oldest)))
                return True, retry_after

            # Record this hit
            self._requests[key].append(now)
            return False, 0


class RedisRateLimiter(BaseRateLimiter):
    """Redis-backed distributed sliding-window rate limiter using sorted sets."""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._redis = None
        self._fallback = InMemoryRateLimiter()
        self._init_redis()

    def _init_redis(self):
        try:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2.0,
            )
            logger.info("Connected to Redis for distributed rate limiting at %s", self.redis_url)
        except Exception as e:
            logger.warning("Could not connect to Redis (%s), falling back to in-memory rate limiter: %s", self.redis_url, e)
            self._redis = None

    async def is_rate_limited(self, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
        if self._redis is None:
            return await self._fallback.is_rate_limited(key, max_requests, window_seconds)

        now = time.time()
        redis_key = f"rl:{key}"
        cutoff = now - window_seconds

        try:
            pipe = self._redis.pipeline()
            # Remove old elements
            pipe.zremrangebyscore(redis_key, 0, cutoff)
            # Count elements in current window
            pipe.zcard(redis_key)
            # Add current element
            pipe.zadd(redis_key, {str(now): now})
            # Set key expiry
            pipe.expire(redis_key, window_seconds + 1)
            results = await pipe.execute()

            current_count = results[1]
            if current_count >= max_requests:
                # Rate limit exceeded
                oldest_elements = await self._redis.zrange(redis_key, 0, 0, withscores=True)
                if oldest_elements:
                    oldest_time = oldest_elements[0][1]
                    retry_after = max(1, int(window_seconds - (now - oldest_time)))
                else:
                    retry_after = window_seconds
                return True, retry_after

            return False, 0
        except Exception as e:
            logger.warning("Redis rate limit error, falling back to in-memory: %s", e)
            return await self._fallback.is_rate_limited(key, max_requests, window_seconds)


_limiter_instance: Optional[BaseRateLimiter] = None


def get_rate_limiter() -> BaseRateLimiter:
    """Singleton getter for active rate limiter."""
    global _limiter_instance
    if _limiter_instance is None:
        settings = get_settings()
        if settings.redis_url and settings.is_production:
            _limiter_instance = RedisRateLimiter(settings.redis_url)
        else:
            _limiter_instance = InMemoryRateLimiter()
    return _limiter_instance
