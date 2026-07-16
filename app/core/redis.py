import redis.asyncio as redis
from app.core.config import settings


class RedisManager:
    def __init__(self) -> None:
        self.client: redis.Redis | None = None

    async def init(self) -> None:
        self.client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )

    async def close(self) -> None:
        if self.client:
            await self.client.aclose()
            self.client = None


redis_manager = RedisManager()
