"""Config flow for the Seerr Home Assistant integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SeerAuthError, SeerClient, SeerConnectionError
from .const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_PORT,
    CONF_SSL,
    CONF_VERIFY_SSL,
    DEFAULT_PORT,
    DEFAULT_SSL,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def _validate_connection(
    hass: HomeAssistant, data: dict[str, Any]
) -> dict[str, Any]:
    """Attempt to reach the Seerr server and return its status payload.

    Uses the HA-managed session so SSL settings are respected.
    API key is NOT logged at any point in this function.
    """
    session = async_get_clientsession(
        hass, verify_ssl=data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL)
    )
    client = SeerClient(
        host=data[CONF_HOST],
        port=data[CONF_PORT],
        api_key=data[CONF_API_KEY],
        ssl=data.get(CONF_SSL, DEFAULT_SSL),
        verify_ssl=data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
        session=session,
    )
    return await client.get_status()


class SeerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the UI-driven setup flow for Seerr."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                status = await _validate_connection(self.hass, user_input)
            except SeerAuthError:
                errors["base"] = "invalid_auth"
            except SeerConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error while connecting to Seerr")
                errors["base"] = "unknown"
            else:
                # Prevent duplicate entries for the same server.
                await self.async_set_unique_id(
                    f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
                )
                self._abort_if_unique_id_configured()

                title = status.get("appName", "Seerr")
                return self.async_create_entry(title=title, data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.All(
                    int, vol.Range(min=1, max=65535)
                ),
                vol.Required(CONF_API_KEY): str,
                vol.Optional(CONF_SSL, default=DEFAULT_SSL): bool,
                vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
