"""Tests for Seerr HA services: search, request_media, approve_request."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from custom_components.seerr_home_assistant.api import (
    SeerrApiError,
    SeerrAuthError,
    SeerrConnectionError,
)
from custom_components.seerr_home_assistant.const import DOMAIN
from custom_components.seerr_home_assistant.services import (
    SERVICE_APPROVE_REQUEST,
    SERVICE_REQUEST_MEDIA,
    SERVICE_SEARCH,
    async_register_services,
    async_unregister_services,
)
from tests.conftest import CREATED_REQUEST_RESPONSE, UPDATED_REQUEST_RESPONSE

SEARCH_RESPONSE = {
    "results": [
        {"id": 1, "title": "Fight Club", "mediaType": "movie", "posterPath": "/abc.jpg"}
    ],
    "pageInfo": {"page": 1, "pages": 1, "results": 1},
}

APPROVED_REQUEST = {**CREATED_REQUEST_RESPONSE, "status": 2}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_mock_client(**overrides) -> MagicMock:
    client = MagicMock()
    client.search = AsyncMock(return_value=SEARCH_RESPONSE)
    client.create_request = AsyncMock(return_value=CREATED_REQUEST_RESPONSE)
    client.update_request_status = AsyncMock(return_value=UPDATED_REQUEST_RESPONSE)
    for attr, val in overrides.items():
        setattr(client, attr, val)
    return client


def setup_coordinator(hass: HomeAssistant, client: MagicMock) -> None:
    coordinator = MagicMock()
    coordinator.client = client
    hass.data.setdefault(DOMAIN, {})["test_entry"] = coordinator


# ---------------------------------------------------------------------------
# Service registration
# ---------------------------------------------------------------------------


def test_services_registered(hass: HomeAssistant) -> None:
    async_register_services(hass)
    assert hass.services.has_service(DOMAIN, SERVICE_SEARCH)
    assert hass.services.has_service(DOMAIN, SERVICE_REQUEST_MEDIA)
    assert hass.services.has_service(DOMAIN, SERVICE_APPROVE_REQUEST)


def test_register_services_is_idempotent(hass: HomeAssistant) -> None:
    async_register_services(hass)
    async_register_services(hass)  # second call must not raise
    assert hass.services.has_service(DOMAIN, SERVICE_SEARCH)


def test_unregister_removes_services_when_no_entries(hass: HomeAssistant) -> None:
    async_register_services(hass)
    hass.data[DOMAIN] = {}
    async_unregister_services(hass)
    assert not hass.services.has_service(DOMAIN, SERVICE_SEARCH)
    assert not hass.services.has_service(DOMAIN, SERVICE_REQUEST_MEDIA)
    assert not hass.services.has_service(DOMAIN, SERVICE_APPROVE_REQUEST)


def test_unregister_keeps_services_when_entries_remain(hass: HomeAssistant) -> None:
    client = make_mock_client()
    setup_coordinator(hass, client)
    async_register_services(hass)
    async_unregister_services(hass)  # entries still present — should be a no-op
    assert hass.services.has_service(DOMAIN, SERVICE_SEARCH)


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_calls_client(hass: HomeAssistant) -> None:
    client = make_mock_client()
    setup_coordinator(hass, client)
    async_register_services(hass)

    await hass.services.async_call(
        DOMAIN, SERVICE_SEARCH, {"query": "Fight Club"}, blocking=True, return_response=True
    )
    client.search.assert_called_once_with("Fight Club", page=1)


@pytest.mark.asyncio
async def test_search_returns_results(hass: HomeAssistant) -> None:
    client = make_mock_client()
    setup_coordinator(hass, client)
    async_register_services(hass)

    result = await hass.services.async_call(
        DOMAIN, SERVICE_SEARCH, {"query": "Fight Club"}, blocking=True, return_response=True
    )
    assert result["results"] == SEARCH_RESPONSE["results"]


@pytest.mark.asyncio
async def test_search_returns_page_info(hass: HomeAssistant) -> None:
    client = make_mock_client()
    setup_coordinator(hass, client)
    async_register_services(hass)

    result = await hass.services.async_call(
        DOMAIN, SERVICE_SEARCH, {"query": "q"}, blocking=True, return_response=True
    )
    assert result["page_info"] == SEARCH_RESPONSE["pageInfo"]


@pytest.mark.asyncio
async def test_search_passes_page_param(hass: HomeAssistant) -> None:
    client = make_mock_client()
    setup_coordinator(hass, client)
    async_register_services(hass)

    await hass.services.async_call(
        DOMAIN, SERVICE_SEARCH, {"query": "x", "page": 3}, blocking=True, return_response=True
    )
    client.search.assert_called_once_with("x", page=3)


@pytest.mark.asyncio
async def test_search_empty_results_returns_empty_list(hass: HomeAssistant) -> None:
    client = make_mock_client()
    client.search = AsyncMock(return_value={})
    setup_coordinator(hass, client)
    async_register_services(hass)

    result = await hass.services.async_call(
        DOMAIN, SERVICE_SEARCH, {"query": "nothing"}, blocking=True, return_response=True
    )
    assert result["results"] == []
    assert result["page_info"] == {}


@pytest.mark.asyncio
async def test_search_auth_error_raises(hass: HomeAssistant) -> None:
    client = make_mock_client()
    client.search = AsyncMock(side_effect=SeerrAuthError("bad key"))
    setup_coordinator(hass, client)
    async_register_services(hass)

    with pytest.raises(HomeAssistantError, match="Authentication failed"):
        await hass.services.async_call(
            DOMAIN, SERVICE_SEARCH, {"query": "q"}, blocking=True, return_response=True
        )


@pytest.mark.asyncio
async def test_search_connection_error_raises(hass: HomeAssistant) -> None:
    client = make_mock_client()
    client.search = AsyncMock(side_effect=SeerrConnectionError("timeout"))
    setup_coordinator(hass, client)
    async_register_services(hass)

    with pytest.raises(HomeAssistantError, match="Cannot reach"):
        await hass.services.async_call(
            DOMAIN, SERVICE_SEARCH, {"query": "q"}, blocking=True, return_response=True
        )


@pytest.mark.asyncio
async def test_search_api_error_raises(hass: HomeAssistant) -> None:
    client = make_mock_client()
    client.search = AsyncMock(side_effect=SeerrApiError("500"))
    setup_coordinator(hass, client)
    async_register_services(hass)

    with pytest.raises(HomeAssistantError, match="Seerr API error"):
        await hass.services.async_call(
            DOMAIN, SERVICE_SEARCH, {"query": "q"}, blocking=True, return_response=True
        )


@pytest.mark.asyncio
async def test_search_no_entries_raises(hass: HomeAssistant) -> None:
    hass.data[DOMAIN] = {}
    async_register_services(hass)

    with pytest.raises(HomeAssistantError, match="not configured"):
        await hass.services.async_call(
            DOMAIN, SERVICE_SEARCH, {"query": "q"}, blocking=True, return_response=True
        )


# ---------------------------------------------------------------------------
# request_media
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_request_media_creates_request(hass: HomeAssistant) -> None:
    client = make_mock_client()
    setup_coordinator(hass, client)
    async_register_services(hass)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_REQUEST_MEDIA,
        {"media_id": 550, "media_type": "movie"},
        blocking=True,
    )
    client.create_request.assert_called_once_with(
        media_id=550, media_type="movie", is4k=False
    )


@pytest.mark.asyncio
async def test_request_media_auto_approves_when_pending(hass: HomeAssistant) -> None:
    client = make_mock_client()
    # CREATED_REQUEST_RESPONSE has status=1 (pending)
    client.create_request = AsyncMock(return_value=CREATED_REQUEST_RESPONSE)
    setup_coordinator(hass, client)
    async_register_services(hass)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_REQUEST_MEDIA,
        {"media_id": 550, "media_type": "movie"},
        blocking=True,
    )
    client.update_request_status.assert_called_once_with(
        CREATED_REQUEST_RESPONSE["id"], "approve"
    )


@pytest.mark.asyncio
async def test_request_media_no_approve_when_already_approved(hass: HomeAssistant) -> None:
    client = make_mock_client()
    client.create_request = AsyncMock(return_value=APPROVED_REQUEST)
    setup_coordinator(hass, client)
    async_register_services(hass)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_REQUEST_MEDIA,
        {"media_id": 550, "media_type": "movie"},
        blocking=True,
    )
    client.update_request_status.assert_not_called()


@pytest.mark.asyncio
async def test_request_media_returns_request(hass: HomeAssistant) -> None:
    client = make_mock_client()
    client.create_request = AsyncMock(return_value=APPROVED_REQUEST)
    setup_coordinator(hass, client)
    async_register_services(hass)

    result = await hass.services.async_call(
        DOMAIN,
        SERVICE_REQUEST_MEDIA,
        {"media_id": 550, "media_type": "movie"},
        blocking=True,
        return_response=True,
    )
    assert result["id"] == APPROVED_REQUEST["id"]
    assert result["status"] == 2


@pytest.mark.asyncio
async def test_request_media_4k_passed_through(hass: HomeAssistant) -> None:
    client = make_mock_client()
    client.create_request = AsyncMock(return_value=APPROVED_REQUEST)
    setup_coordinator(hass, client)
    async_register_services(hass)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_REQUEST_MEDIA,
        {"media_id": 550, "media_type": "movie", "is4k": True},
        blocking=True,
    )
    client.create_request.assert_called_once_with(
        media_id=550, media_type="movie", is4k=True
    )


@pytest.mark.asyncio
async def test_request_media_connection_error_raises(hass: HomeAssistant) -> None:
    client = make_mock_client()
    client.create_request = AsyncMock(side_effect=SeerrConnectionError("refused"))
    setup_coordinator(hass, client)
    async_register_services(hass)

    with pytest.raises(HomeAssistantError, match="Cannot reach"):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_REQUEST_MEDIA,
            {"media_id": 550, "media_type": "movie"},
            blocking=True,
        )


@pytest.mark.asyncio
async def test_request_media_auth_error_raises(hass: HomeAssistant) -> None:
    client = make_mock_client()
    client.create_request = AsyncMock(side_effect=SeerrAuthError("bad key"))
    setup_coordinator(hass, client)
    async_register_services(hass)

    with pytest.raises(HomeAssistantError, match="Authentication failed"):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_REQUEST_MEDIA,
            {"media_id": 550, "media_type": "movie"},
            blocking=True,
        )


# ---------------------------------------------------------------------------
# approve_request
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_approve_request_calls_update_status(hass: HomeAssistant) -> None:
    client = make_mock_client()
    setup_coordinator(hass, client)
    async_register_services(hass)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_APPROVE_REQUEST,
        {"request_id": 123},
        blocking=True,
    )
    client.update_request_status.assert_called_once_with(123, "approve")


@pytest.mark.asyncio
async def test_approve_request_auth_error_raises(hass: HomeAssistant) -> None:
    client = make_mock_client()
    client.update_request_status = AsyncMock(side_effect=SeerrAuthError("bad key"))
    setup_coordinator(hass, client)
    async_register_services(hass)

    with pytest.raises(HomeAssistantError, match="Authentication failed"):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_APPROVE_REQUEST,
            {"request_id": 123},
            blocking=True,
        )


@pytest.mark.asyncio
async def test_approve_request_connection_error_raises(hass: HomeAssistant) -> None:
    client = make_mock_client()
    client.update_request_status = AsyncMock(side_effect=SeerrConnectionError("timeout"))
    setup_coordinator(hass, client)
    async_register_services(hass)

    with pytest.raises(HomeAssistantError, match="Cannot reach"):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_APPROVE_REQUEST,
            {"request_id": 123},
            blocking=True,
        )


@pytest.mark.asyncio
async def test_approve_request_api_error_raises(hass: HomeAssistant) -> None:
    client = make_mock_client()
    client.update_request_status = AsyncMock(side_effect=SeerrApiError("500"))
    setup_coordinator(hass, client)
    async_register_services(hass)

    with pytest.raises(HomeAssistantError, match="Seerr API error"):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_APPROVE_REQUEST,
            {"request_id": 123},
            blocking=True,
        )
