"""Tests for get_request — GET /api/v1/request/{requestId}."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from custom_components.seerr_home_assistant.api import (
    SeerrApiError,
    SeerrAuthError,
    SeerrClient,
    SeerrConnectionError,
)
from tests.conftest import SINGLE_REQUEST_RESPONSE, TEST_API_KEY, TEST_HOST, TEST_PORT


def make_client() -> SeerrClient:
    return SeerrClient(TEST_HOST, TEST_PORT, TEST_API_KEY)


# ---------------------------------------------------------------------------
# Correct endpoint
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_calls_correct_endpoint():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value=SINGLE_REQUEST_RESPONSE) as mock_req:
        await client.get_request(123)
    assert mock_req.call_args.args == ("GET", "/request/123")


@pytest.mark.asyncio
async def test_request_id_used_in_url():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value=SINGLE_REQUEST_RESPONSE) as mock_req:
        await client.get_request(456)
    assert "/request/456" in mock_req.call_args.args[1]


# ---------------------------------------------------------------------------
# Return value
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_returns_request():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value=SINGLE_REQUEST_RESPONSE):
        result = await client.get_request(123)
    assert result["id"] == 123
    assert result["status"] == 0


@pytest.mark.asyncio
async def test_response_contains_requested_by():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value=SINGLE_REQUEST_RESPONSE):
        result = await client.get_request(123)
    assert result["requestedBy"]["id"] == 1
    assert result["requestedBy"]["email"] == "hey@itsme.com"


@pytest.mark.asyncio
async def test_response_contains_media_fields():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value=SINGLE_REQUEST_RESPONSE):
        result = await client.get_request(123)
    assert "is4k" in result
    assert "serverId" in result
    assert "profileId" in result
    assert "rootFolder" in result


# ---------------------------------------------------------------------------
# Error propagation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_auth_error_propagates():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, side_effect=SeerrAuthError("bad key")):
        with pytest.raises(SeerrAuthError):
            await client.get_request(123)


@pytest.mark.asyncio
async def test_not_found_raises_api_error():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, side_effect=SeerrApiError("HTTP 404")):
        with pytest.raises(SeerrApiError):
            await client.get_request(999)


@pytest.mark.asyncio
async def test_connection_error_propagates():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, side_effect=SeerrConnectionError("timeout")):
        with pytest.raises(SeerrConnectionError):
            await client.get_request(123)
