"""Seerr Home Assistant Integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SeerClient
from .const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_PORT,
    CONF_SSL,
    CONF_VERIFY_SSL,
    DEFAULT_SSL,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
    LOGGER,
)
from .coordinator import SeerCoordinator

# Register platform modules here as they are added (e.g. "sensor", "binary_sensor").
PLATFORMS: list[str] = []


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Seerr from a config entry."""
    verify_ssl: bool = entry.data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL)

    session = async_get_clientsession(hass, verify_ssl=verify_ssl)

    client = SeerClient(
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        api_key=entry.data[CONF_API_KEY],
        ssl=entry.data.get(CONF_SSL, DEFAULT_SSL),
        verify_ssl=verify_ssl,
        session=session,
    )

    coordinator = SeerCoordinator(hass, client, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    LOGGER.debug("Seerr integration set up for %s", entry.title)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Seerr config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
