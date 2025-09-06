import asyncio
import time
from typing import Callable, Awaitable

from _configs.config import get_config

cfg = get_config()

ACCESS_CACHE_TTL = cfg.bot_config.access_cache_ttl

class AccessLevelCache:
    def __init__(self, db_accessor: Callable[[int], Awaitable[int]]):
        self._cache: dict[int, tuple[int, float]] = {}
        self._lock = asyncio.Lock()
        self._db_accessor = db_accessor

    async def get_access_level(self, user_id: int) -> int:
        now = time.time()
        cached = self._cache.get(user_id)

        if cached and now - cached[1] < ACCESS_CACHE_TTL:
            return cached[0]

        async with self._lock:
            cached = self._cache.get(user_id)
            if cached and now - cached[1] < ACCESS_CACHE_TTL:
                return cached[0]

            access_level = await self._db_accessor(user_id)
            self._cache[user_id] = (access_level, now)
            return access_level

    def invalidate(self, user_id: int):
        self._cache.pop(user_id, None)

    def clear(self):
        self._cache.clear()


# access_cache: AccessLevelCache | None = None
#
# def init_access_cache(db_accessor):
#     global access_cache
#     access_cache =  AccessLevelCache(db_accessor)

