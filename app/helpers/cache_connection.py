"""Redis client connection helper for optional cache."""

from __future__ import annotations

import logging

import redis

from app.core.config import settings


class CacheConnectionHelper:
    """Creates and validates a Redis client connection."""

    @staticmethod
    def connect(logger: logging.Logger) -> redis.Redis | None:
        try:
            client = redis.from_url(settings.REDIS_URL)
            client.ping()
            logger.info("Redis connected successfully")
            return client
        except Exception as exc:
            logger.warning("Redis connection failed: %s. Cache is disabled.", exc)
            return None
