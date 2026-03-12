"""DataUpdateCoordinator for the Seerr integration."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SeerrApiError, SeerrAuthError, SeerrClient, SeerrConnectionError
from .const import DOMAIN, LOGGER, SCAN_INTERVAL_MINUTES


@dataclass
class SeerrData:
    """Snapshot of data fetched from the Seerr server."""

    status: dict[str, Any]
    request_counts: dict[str, Any]


class SeerrCoordinator(DataUpdateCoordinator[SeerrData]):
    """Poll the Seerr server on a fixed interval and fan data out to entities."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: SeerrClient,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=SCAN_INTERVAL_MINUTES),
        )
        self.client = client
        self.config_entry = entry

    async def _async_update_data(self) -> SeerrData:
        try:
            status = await self.client.get_status()
            request_counts = await self.client.get_request_count()
        except SeerrAuthError as exc:
            # Triggers a reauthentication flow in the UI.
            raise ConfigEntryAuthFailed(exc) from exc
        except SeerrConnectionError as exc:
            raise UpdateFailed(f"Cannot reach Seerr server: {exc}") from exc
        except SeerrApiError as exc:
            raise UpdateFailed(f"Seerr API error: {exc}") from exc

        return SeerrData(status=status, request_counts=request_counts)
