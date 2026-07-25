import asyncio
import time
from dataclasses import dataclass


@dataclass
class CacheEntry[T]:
    value: T
    expires_at: float


class TTLCache:
    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self._values: dict[str, CacheEntry[object]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> object | None:
        if not self.enabled:
            return None
        async with self._lock:
            entry = self._values.get(key)
            if entry is None:
                return None
            if entry.expires_at <= time.monotonic():
                self._values.pop(key, None)
                return None
            return entry.value

    async def set(self, key: str, value: object, ttl_seconds: int) -> None:
        if not self.enabled or ttl_seconds <= 0:
            return
        async with self._lock:
            self._values[key] = CacheEntry(value, time.monotonic() + ttl_seconds)

    async def clear(self) -> None:
        async with self._lock:
            self._values.clear()
