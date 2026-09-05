"""
Rate limiter abstraction supporting in-memory sliding window and Redis-backed storage.
"""
import threading
import time
from abc import ABC, abstractmethod
from collections import defaultdict

from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger("rate_limiter_core")


class BaseRateLimiter(ABC):
    """Abstract interface for rate limiting backends."""

    @abstractmethod
    async def is_rate_limited(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, int]:
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

    async def is_rate_limited(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, int]:
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

        self._lua_script = """
        local key = KEYS[1]
        local now = tonumber(ARGV[1])
        local cutoff = tonumber(ARGV[2])
        local max_requests = tonumber(ARGV[3])
        local window = tonumber(ARGV[4])

        redis.call('ZREMRANGEBYSCORE', key, 0, cutoff)
        local count = redis.call('ZCARD', key)

        if count >= max_requests then
            local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
            local retry_after = window
            if oldest and #oldest >= 2 then
                local oldest_time = tonumber(oldest[2])
                retry_after = math.max(1, math.ceil(window - (now - oldest_time)))
            end
            return {1, retry_after}
        else
            redis.call('ZADD', key, now, tostring(now))
            redis.call('EXPIRE', key, window + 1)
            return {0, 0}
        end
        """

    async def is_rate_limited(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, int]:
        if self._redis is None:
            return await self._fallback.is_rate_limited(key, max_requests, window_seconds)

        now = time.time()
        redis_key = f"rl:{key}"
        cutoff = now - window_seconds

        try:
            res = await self._redis.eval(
                self._lua_script,
                1,
                redis_key,
                str(now),
                str(cutoff),
                str(max_requests),
                str(window_seconds),
            )
            is_limited = bool(res[0])
            retry_after = int(res[1])
            return is_limited, retry_after
        except Exception as e:
            logger.warning("Redis rate limit error, falling back to in-memory: %s", e)
            return await self._fallback.is_rate_limited(key, max_requests, window_seconds)


_limiter_instance: BaseRateLimiter | None = None


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
