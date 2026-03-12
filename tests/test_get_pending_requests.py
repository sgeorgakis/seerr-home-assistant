"""Tests for get_pending_requests — GET /api/v1/requests."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from custom_components.seerr_home_assistant.api import (
    SeerrAuthError,
    SeerrClient,
    SeerrConnectionError,
)
from tests.conftest import PENDING_REQUESTS_RESPONSE, TEST_API_KEY, TEST_HOST, TEST_PORT

FIXED_PARAMS = {
    "take": 20,
    "skip": 0,
    "filter": "pending",
    "sort": "added",
    "sortDirection": "desc",
}


def make_client() -> SeerrClient:
    return SeerrClient(TEST_HOST, TEST_PORT, TEST_API_KEY)


# ---------------------------------------------------------------------------
# Correct endpoint and params
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_calls_correct_endpoint():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value=PENDING_REQUESTS_RESPONSE) as mock_req:
        await client.get_pending_requests()
    mock_req.assert_called_once()
    assert mock_req.call_args.args[1] == "/requests"


@pytest.mark.asyncio
async def test_uses_get_method():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value=PENDING_REQUESTS_RESPONSE) as mock_req:
        await client.get_pending_requests()
    assert mock_req.call_args.args[0] == "GET"


@pytest.mark.asyncio
async def test_default_take_and_skip():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value=PENDING_REQUESTS_RESPONSE) as mock_req:
        await client.get_pending_requests()
    params = mock_req.call_args.kwargs["params"]
    assert params["take"] == 20
    assert params["skip"] == 0


@pytest.mark.asyncio
async def test_custom_take_and_skip():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value=PENDING_REQUESTS_RESPONSE) as mock_req:
        await client.get_pending_requests(take=5, skip=10)
    params = mock_req.call_args.kwargs["params"]
    assert params["take"] == 5
    assert params["skip"] == 10


# ---------------------------------------------------------------------------
# Fixed params — not configurable
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_filter_is_always_pending():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value=PENDING_REQUESTS_RESPONSE) as mock_req:
        await client.get_pending_requests()
    assert mock_req.call_args.kwargs["params"]["filter"] == "pending"


@pytest.mark.asyncio
async def test_sort_is_always_added():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value=PENDING_REQUESTS_RESPONSE) as mock_req:
        await client.get_pending_requests()
    assert mock_req.call_args.kwargs["params"]["sort"] == "added"


@pytest.mark.asyncio
async def test_sort_direction_is_always_desc():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value=PENDING_REQUESTS_RESPONSE) as mock_req:
        await client.get_pending_requests()
    assert mock_req.call_args.kwargs["params"]["sortDirection"] == "desc"


# ---------------------------------------------------------------------------
# Return value
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_returns_response():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value=PENDING_REQUESTS_RESPONSE):
        result = await client.get_pending_requests()
    assert result == PENDING_REQUESTS_RESPONSE
    assert result["results"][0]["id"] == 123


# ---------------------------------------------------------------------------
# Error propagation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_auth_error_propagates():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, side_effect=SeerrAuthError("bad key")):
        with pytest.raises(SeerrAuthError):
            await client.get_pending_requests()


@pytest.mark.asyncio
async def test_connection_error_propagates():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, side_effect=SeerrConnectionError("timeout")):
        with pytest.raises(SeerrConnectionError):
            await client.get_pending_requests()
