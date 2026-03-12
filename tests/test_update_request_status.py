"""Tests for update_request_status — POST /api/v1/request/{requestId}/{status}."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from custom_components.seerr_home_assistant.api import (
    SeerrApiError,
    SeerrAuthError,
    SeerrClient,
    SeerrConnectionError,
)
from tests.conftest import UPDATED_REQUEST_RESPONSE, TEST_API_KEY, TEST_HOST, TEST_PORT


def make_client() -> SeerrClient:
    return SeerrClient(TEST_HOST, TEST_PORT, TEST_API_KEY)


# ---------------------------------------------------------------------------
# Correct endpoint — approve
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_approve_calls_correct_endpoint():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value=UPDATED_REQUEST_RESPONSE) as mock_req:
        await client.update_request_status(123, "approve")
    assert mock_req.call_args.args == ("POST", "/request/123/approve")


@pytest.mark.asyncio
async def test_approve_returns_updated_request():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value=UPDATED_REQUEST_RESPONSE):
        result = await client.update_request_status(123, "approve")
    assert result["id"] == 123
    assert result["status"] == 2


# ---------------------------------------------------------------------------
# Correct endpoint — decline
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_decline_calls_correct_endpoint():
    declined = {**UPDATED_REQUEST_RESPONSE, "status": 3}
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value=declined) as mock_req:
        await client.update_request_status(123, "decline")
    assert mock_req.call_args.args == ("POST", "/request/123/decline")


@pytest.mark.asyncio
async def test_decline_returns_updated_request():
    declined = {**UPDATED_REQUEST_RESPONSE, "status": 3}
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value=declined):
        result = await client.update_request_status(123, "decline")
    assert result["status"] == 3


# ---------------------------------------------------------------------------
# Request ID is used in path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_request_id_in_path():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value=UPDATED_REQUEST_RESPONSE) as mock_req:
        await client.update_request_status(99, "approve")
    assert "/request/99/approve" in mock_req.call_args.args[1]


# ---------------------------------------------------------------------------
# Error propagation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_auth_error_propagates():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, side_effect=SeerrAuthError("bad key")):
        with pytest.raises(SeerrAuthError):
            await client.update_request_status(123, "approve")


@pytest.mark.asyncio
async def test_not_found_raises_api_error():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, side_effect=SeerrApiError("HTTP 404")):
        with pytest.raises(SeerrApiError):
            await client.update_request_status(999, "approve")


@pytest.mark.asyncio
async def test_connection_error_propagates():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, side_effect=SeerrConnectionError("timeout")):
        with pytest.raises(SeerrConnectionError):
            await client.update_request_status(123, "decline")
