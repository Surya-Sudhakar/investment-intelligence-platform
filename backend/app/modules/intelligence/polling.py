import asyncio
import logging
from collections.abc import Awaitable, Callable

from app.modules.market_data.schemas import Quote

logger = logging.getLogger(__name__)


class QuotePollingEngine:
    def __init__(
        self,
        fetch_quote: Callable[[str], Awaitable[Quote]],
        interval_seconds: float,
        on_quote: Callable[[Quote], Awaitable[None]] | None = None,
    ) -> None:
        self.fetch_quote = fetch_quote
        self.interval_seconds = interval_seconds
        self.on_quote = on_quote
        self.latest: dict[str, Quote] = {}
        self._tasks: dict[str, asyncio.Task[None]] = {}

    @property
    def active_count(self) -> int:
        return len(self._tasks)

    def start(self, symbol: str) -> bool:
        symbol = symbol.strip().upper()
        if symbol in self._tasks and not self._tasks[symbol].done():
            return False
        self._tasks[symbol] = asyncio.create_task(self._run(symbol), name=f"quote-poll-{symbol}")
        return True

    async def stop(self, symbol: str) -> bool:
        task = self._tasks.pop(symbol.strip().upper(), None)
        if task is None:
            return False
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        return True

    async def stop_all(self) -> None:
        tasks = list(self._tasks.values())
        self._tasks.clear()
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _run(self, symbol: str) -> None:
        try:
            while True:
                try:
                    quote = await self.fetch_quote(symbol)
                    self.latest[symbol] = quote
                    if self.on_quote:
                        await self.on_quote(quote)
                except Exception:
                    logger.exception("Quote polling failed", extra={"symbol": symbol})
                await asyncio.sleep(self.interval_seconds)
        except asyncio.CancelledError:
            raise
        finally:
            current = asyncio.current_task()
            if self._tasks.get(symbol) is current:
                self._tasks.pop(symbol, None)
