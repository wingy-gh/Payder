import threading
import time
from collections import deque

from fastapi import HTTPException, status


class RateLimiter:
    """Скользящее окно в памяти процесса: не больше `limit` ошибок за `window` секунд на ключ.

    Работает в пределах одного процесса. При нескольких воркерах или серверах
    лимиты не общие: тогда нужен общий склад (например, Redis).
    """

    def __init__(self, limit: int, window: int) -> None:
        self.limit = limit
        self.window = window
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def _prune(self, key: str, now: float) -> deque[float] | None:
        hits = self._hits.get(key)
        if hits is None:
            return None
        while hits and hits[0] <= now - self.window:
            hits.popleft()
        if not hits:
            del self._hits[key]
            return None
        return hits

    def check(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            if len(self._hits) > 10_000:
                for stale in list(self._hits):
                    self._prune(stale, now)
            hits = self._prune(key, now)
            if hits is not None and len(hits) >= self.limit:
                retry_after = max(1, int(hits[0] + self.window - now))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Слишком много попыток. Попробуйте позже",
                    headers={"Retry-After": str(retry_after)},
                )

    def hit(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            self._hits.setdefault(key, deque()).append(now)

    def reset(self, key: str) -> None:
        with self._lock:
            self._hits.pop(key, None)
