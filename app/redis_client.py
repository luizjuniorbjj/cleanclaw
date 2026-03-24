"""
ClaWin1Click - Redis Client
Connection manager for Redis (rate limiting, OAuth state, caching)
Graceful fallback: if Redis is unavailable, operations return None
and callers must handle the fallback logic.
"""

import logging
from typing import Optional

import redis.asyncio as aioredis

from app.config import REDIS_URL

logger = logging.getLogger("clawin.redis")

_redis: Optional[aioredis.Redis] = None


async def init_redis() -> Optional[aioredis.Redis]:
    """Initialize Redis connection. Returns None if Redis is unavailable."""
    global _redis
    try:
        _redis = aioredis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        await _redis.ping()
        logger.info("[REDIS] Connected to %s", REDIS_URL.split("@")[-1])
        return _redis
    except Exception as e:
        logger.warning(
            "[REDIS] Could not connect (%s). "
            "Falling back to in-memory rate limiter and OAuth state.",
            e,
        )
        _redis = None
        return None


async def close_redis():
    """Close Redis connection gracefully."""
    global _redis
    if _redis:
        await _redis.close()
        logger.info("[REDIS] Connection closed")
        _redis = None


def get_redis() -> Optional[aioredis.Redis]:
    """Get the current Redis instance. Returns None if unavailable."""
    return _redis
