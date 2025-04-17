import json
from typing import Any, Optional
import aioredis
from datetime import timedelta
import os
from fastapi import Depends

class CacheManager:
    def __init__(self, redis_url: str):
        self.redis = aioredis.from_url(redis_url, encoding="utf-8", decode_responses=True)

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(self, key: str, value: Any, expire: int = 3600) -> None:
        """Set value in cache with expiration"""
        await self.redis.set(key, json.dumps(value), ex=expire)

    async def delete(self, key: str) -> None:
        """Delete value from cache"""
        await self.redis.delete(key)

    async def clear(self) -> None:
        """Clear all cache"""
        await self.redis.flushdb()

    async def get_or_set(self, key: str, func: callable, expire: int = 3600) -> Any:
        """Get value from cache or set it if not exists"""
        value = await self.get(key)
        if value is None:
            value = await func()
            await self.set(key, value, expire)
        return value

# Cache keys
class CacheKeys:
    SONARR_INSTANCES = "sonarr:instances"
    SONARR_INSTANCE = "sonarr:instance:{id}"
    SONARR_STATUS = "sonarr:status:{id}" 