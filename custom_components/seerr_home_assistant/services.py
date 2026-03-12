"""HA service handlers for the Seerr integration."""
from __future__ import annotations

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import HomeAssistantError

from .api import SeerrApiError, SeerrAuthError, SeerrConnectionError
from .const import DOMAIN, LOGGER

SERVICE_SEARCH = "search"
SERVICE_REQUEST_MEDIA = "request_media"
SERVICE_APPROVE_REQUEST = "approve_request"

# Seerr request status: 1=pending, 2=approved, 3=declined
_REQUEST_STATUS_APPROVED = 2

SEARCH_SCHEMA = vol.Schema(
    {
        vol.Required("query"): str,
        vol.Optional("page", default=1): vol.All(int, vol.Range(min=1)),
    }
)

REQUEST_MEDIA_SCHEMA = vol.Schema(
    {
        vol.Required("media_id"): int,
        vol.Required("media_type"): vol.In(["movie", "tv"]),
        vol.Optional("is4k", default=False): bool,
    }
)

APPROVE_REQUEST_SCHEMA = vol.Schema(
    {
        vol.Required("request_id"): int,
    }
)


def _get_client(hass: HomeAssistant):
    """Return the SeerrClient from the first active config entry."""
    entries = hass.data.get(DOMAIN, {})
    if not entries:
        raise HomeAssistantError("Seerr integration is not configured")
    coordinator = next(iter(entries.values()))
    return coordinator.client


def _map_exc(exc: Exception) -> HomeAssistantError:
    """Map Seerr API exceptions to HomeAssistantError."""
    if isinstance(exc, SeerrAuthError):
        return HomeAssistantError(f"Authentication failed: {exc}")
    if isinstance(exc, SeerrConnectionError):
        return HomeAssistantError(f"Cannot reach Seerr server: {exc}")
    return HomeAssistantError(f"Seerr API error: {exc}")


def async_register_services(hass: HomeAssistant) -> None:
    """Register Seerr services. Idempotent — safe to call for every config entry."""
    if hass.services.has_service(DOMAIN, SERVICE_SEARCH):
        return

    async def handle_search(call: ServiceCall) -> ServiceResponse:
        client = _get_client(hass)
        try:
            raw = await client.search(call.data["query"], page=call.data["page"])
        except (SeerrAuthError, SeerrConnectionError, SeerrApiError) as exc:
            raise _map_exc(exc) from exc
        return {
            "results": raw.get("results", []),
            "page_info": raw.get("pageInfo", {}),
        }

    async def handle_request_media(call: ServiceCall) -> ServiceResponse:
        client = _get_client(hass)
        try:
            request = await client.create_request(
                media_id=call.data["media_id"],
                media_type=call.data["media_type"],
                is4k=call.data["is4k"],
            )
            if request.get("status") != _REQUEST_STATUS_APPROVED:
                LOGGER.debug(
                    "Request %s is not approved (status=%s), approving automatically",
                    request.get("id"),
                    request.get("status"),
                )
                request = await client.update_request_status(request["id"], "approve")
        except (SeerrAuthError, SeerrConnectionError, SeerrApiError) as exc:
            raise _map_exc(exc) from exc
        return request

    async def handle_approve_request(call: ServiceCall) -> None:
        client = _get_client(hass)
        try:
            await client.update_request_status(call.data["request_id"], "approve")
        except (SeerrAuthError, SeerrConnectionError, SeerrApiError) as exc:
            raise _map_exc(exc) from exc

    hass.services.async_register(
        DOMAIN,
        SERVICE_SEARCH,
        handle_search,
        schema=SEARCH_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REQUEST_MEDIA,
        handle_request_media,
        schema=REQUEST_MEDIA_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_APPROVE_REQUEST,
        handle_approve_request,
        schema=APPROVE_REQUEST_SCHEMA,
    )
    LOGGER.debug("Seerr services registered")


def async_unregister_services(hass: HomeAssistant) -> None:
    """Unregister Seerr services when the last config entry is removed."""
    if hass.data.get(DOMAIN):
        return
    for service in (SERVICE_SEARCH, SERVICE_REQUEST_MEDIA, SERVICE_APPROVE_REQUEST):
        hass.services.async_remove(DOMAIN, service)
    LOGGER.debug("Seerr services unregistered")
