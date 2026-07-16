import logging
from typing import Any, Optional

from app.repository.cache_repository import CacheRepository

logger = logging.getLogger(__name__)


class CacheService:
    """Application cache backed by :class:`CacheRepository` (sync Redis)."""

    def __init__(self, repository: CacheRepository | None = None) -> None:
        self._repo = repository if repository is not None else CacheRepository.connect()

    @property
    def repository(self) -> CacheRepository:
        return self._repo

    def get(self, key: str) -> Optional[str]:
        return self._repo.get(key)

    def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        self._repo.set(key, value, ttl=ttl)

    def delete(self, key: str) -> None:
        self._repo.delete(key)

    def get_json(self, key: str) -> Any | None:
        return self._repo.get_json(key)

    def set_json(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        self._repo.set_json(key, value, ttl=ttl)


cache_service = CacheService()


def get_cache(key: str) -> Optional[str]:
    return cache_service.get(key)


def set_cache(key: str, value: str, ttl: Optional[int] = None) -> None:
    cache_service.set(key, value, ttl=ttl)
