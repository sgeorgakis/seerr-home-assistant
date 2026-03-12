"""Tests for SeerrCoordinator."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.seerr_home_assistant.api import (
    SeerrApiError,
    SeerrAuthError,
    SeerrConnectionError,
)
from custom_components.seerr_home_assistant.coordinator import SeerrCoordinator, SeerrData
from tests.conftest import STATUS_RESPONSE


def make_coordinator(hass: HomeAssistant, client: MagicMock) -> SeerrCoordinator:
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    return SeerrCoordinator(hass, client, entry)


def make_client(
    status=None,
    request_counts=None,
    status_exc=None,
    count_exc=None,
) -> MagicMock:
    client = MagicMock()
    client.get_status = AsyncMock(
        return_value=status or STATUS_RESPONSE,
        side_effect=status_exc,
    )
    client.get_request_count = AsyncMock(
        return_value=request_counts or {"pending": 3, "total": 10},
        side_effect=count_exc,
    )
    return client


# ---------------------------------------------------------------------------
# Successful update
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_returns_seerr_data(hass: HomeAssistant):
    client = make_client()
    coordinator = make_coordinator(hass, client)
    data = await coordinator._async_update_data()
    assert isinstance(data, SeerrData)


@pytest.mark.asyncio
async def test_data_contains_status(hass: HomeAssistant):
    client = make_client()
    coordinator = make_coordinator(hass, client)
    data = await coordinator._async_update_data()
    assert data.status == STATUS_RESPONSE


@pytest.mark.asyncio
async def test_data_contains_request_counts(hass: HomeAssistant):
    client = make_client(request_counts={"pending": 5, "total": 20})
    coordinator = make_coordinator(hass, client)
    data = await coordinator._async_update_data()
    assert data.request_counts["pending"] == 5


@pytest.mark.asyncio
async def test_calls_get_status_and_get_request_count(hass: HomeAssistant):
    client = make_client()
    coordinator = make_coordinator(hass, client)
    await coordinator._async_update_data()
    client.get_status.assert_called_once()
    client.get_request_count.assert_called_once()


# ---------------------------------------------------------------------------
# Auth failure → ConfigEntryAuthFailed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_auth_error_raises_config_entry_auth_failed(hass: HomeAssistant):
    client = make_client(status_exc=SeerrAuthError("invalid key"))
    coordinator = make_coordinator(hass, client)
    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()


# ---------------------------------------------------------------------------
# Connection failure → UpdateFailed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_connection_error_raises_update_failed(hass: HomeAssistant):
    client = make_client(status_exc=SeerrConnectionError("timeout"))
    coordinator = make_coordinator(hass, client)
    with pytest.raises(UpdateFailed, match="Cannot reach"):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_count_connection_error_raises_update_failed(hass: HomeAssistant):
    client = make_client(count_exc=SeerrConnectionError("timeout"))
    coordinator = make_coordinator(hass, client)
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


# ---------------------------------------------------------------------------
# API error → UpdateFailed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_api_error_raises_update_failed(hass: HomeAssistant):
    client = make_client(status_exc=SeerrApiError("HTTP 500"))
    coordinator = make_coordinator(hass, client)
    with pytest.raises(UpdateFailed, match="Seerr API error"):
        await coordinator._async_update_data()


# ---------------------------------------------------------------------------
# SeerrData dataclass
# ---------------------------------------------------------------------------


def test_seerr_data_fields():
    data = SeerrData(status=STATUS_RESPONSE, request_counts={"pending": 2})
    assert data.status["appName"] == "Seerr"
    assert data.request_counts["pending"] == 2
