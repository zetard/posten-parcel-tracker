"""Posten/Bring provider implementation."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
import logging

import aiohttp

from ...const import PROVIDER_POSTEN
from ...models import Parcel
from .. import Provider
from .auth import PostenAuth
from .client import PostenClient
from .const import CARRIER_NAME, PARCEL_LOOKBACK_DAYS
from .parser import parse_parcels

_LOGGER = logging.getLogger(__name__)


class PostenProvider(Provider):
    """Fetch a user's parcels from the (unofficial) Posten account API."""

    provider_id = PROVIDER_POSTEN
    carrier_name = CARRIER_NAME

    def __init__(
        self,
        session: aiohttp.ClientSession,
        auth: PostenAuth,
        lookback_days: int = PARCEL_LOOKBACK_DAYS,
    ) -> None:
        self._auth = auth
        self._client = PostenClient(session, auth, lookback_days)

    @property
    def auth(self) -> PostenAuth:
        return self._auth

    async def async_get_parcels(self) -> Sequence[Parcel]:
        raw = await self._client.async_get_parcels_raw()
        parsed = parse_parcels(raw)

        raw_items = raw.get("parcels") if isinstance(raw, dict) else None
        raw_items = raw_items if isinstance(raw_items, list) else []
        raw_statuses = Counter(
            str(item.get("status"))
            for item in raw_items
            if isinstance(item, dict) and item.get("status") is not None
        )
        normalized_statuses = Counter(parcel.status.value for parcel in parsed)
        active_count = sum(1 for parcel in parsed if parcel.is_active)

        _LOGGER.debug(
            "Posten parcel diagnostics: raw_count=%d parsed_count=%d "
            "active_count=%d raw_statuses=%s normalized_statuses=%s",
            len(raw_items),
            len(parsed),
            active_count,
            dict(raw_statuses),
            dict(normalized_statuses),
        )
        return parsed


__all__ = ["PostenProvider", "PostenAuth"]
