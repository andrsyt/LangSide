"""Sync Redis access for string cache (API, Celery, helpers)."""

from __future__ import annotations

import json
import logging
from typing import Any

import redis

from app.core.config import settings
from app.helpers.text_utils import canonical_english_word_key

logger = logging.getLogger(__name__)


class CacheRepository:
    """Thin Redis wrapper: get / set / delete string and JSON payloads."""

    def __init__(self, client: redis.Redis | None) -> None:
        self._client = client

    @classmethod
    def connect(cls, redis_url: str | None = None) -> CacheRepository:
        url = redis_url or settings.REDIS_URL
        try:
            client = redis.from_url(url, decode_responses=True)
            client.ping()
            logger.info("CacheRepository: Redis connected")
            return cls(client)
        except Exception as exc:
            logger.warning("CacheRepository: Redis unavailable (%s). Cache disabled.", exc)
            return cls(None)

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def get(self, key: str) -> str | None:
        if not self._client:
            return None
        try:
            return self._client.get(key)
        except Exception as exc:
            logger.warning("Cache get error for key %r: %s", key, exc)
            return None

    def set(self, key: str, value: str, ttl: int | None = None) -> None:
        if not self._client:
            return
        try:
            ex = ttl if ttl is not None else settings.CACHE_TTL_SECONDS
            self._client.set(key, value, ex=ex)
        except Exception as exc:
            logger.warning("Cache set error for key %r: %s", key, exc)

    def delete(self, key: str) -> None:
        if not self._client:
            return
        try:
            self._client.delete(key)
        except Exception as exc:
            logger.warning("Cache delete error for key %r: %s", key, exc)

    def get_json(self, key: str) -> Any | None:
        raw = self.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    def set_json(self, key: str, value: Any, ttl: int | None = None) -> None:
        self.set(key, json.dumps(value, ensure_ascii=False), ttl=ttl)

    @staticmethod
    def word_analysis_key(word: str, target_language: str) -> str:
        return f"word_analysis:{canonical_english_word_key(word)}:{target_language}"

    @staticmethod
    def user_word_snapshot_key(user_id: int, word_id: int) -> str:
        return f"user:{user_id}:word:{word_id}:snapshot"
