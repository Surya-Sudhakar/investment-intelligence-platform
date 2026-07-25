import asyncio
from collections.abc import Mapping
from typing import Any

import httpx

from app.core.exceptions import (
    ProviderAuthenticationError,
    ProviderInvalidResponseError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)


class MarketDataHttpClient:
    def __init__(
        self,
        *,
        timeout_seconds: float,
        max_retries: int,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.max_retries = max_retries
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_seconds),
            headers={"User-Agent": "AI-Investment-Intelligence/0.2"},
            transport=transport,
        )

    async def get_json(
        self,
        url: str,
        params: Mapping[str, str],
        request_id: str | None = None,
    ) -> dict[str, Any]:
        headers = {"X-Request-ID": request_id} if request_id else {}
        for attempt in range(self.max_retries + 1):
            try:
                response = await self._client.get(url, params=params, headers=headers)
            except httpx.TimeoutException as exc:
                if attempt >= self.max_retries:
                    raise ProviderTimeoutError() from exc
                await asyncio.sleep(0.1 * (2**attempt))
                continue
            except httpx.RequestError as exc:
                if attempt >= self.max_retries:
                    raise ProviderUnavailableError() from exc
                await asyncio.sleep(0.1 * (2**attempt))
                continue

            if response.status_code in {401, 403}:
                raise ProviderAuthenticationError()
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                raise ProviderRateLimitError(
                    int(retry_after) if retry_after and retry_after.isdigit() else None
                )
            if response.status_code >= 500:
                if attempt >= self.max_retries:
                    raise ProviderUnavailableError()
                await asyncio.sleep(0.1 * (2**attempt))
                continue
            if response.status_code >= 400:
                raise ProviderInvalidResponseError()
            try:
                payload = response.json()
            except ValueError as exc:
                raise ProviderInvalidResponseError() from exc
            if not isinstance(payload, dict):
                raise ProviderInvalidResponseError()
            return payload
        raise ProviderUnavailableError()

    async def close(self) -> None:
        await self._client.aclose()
