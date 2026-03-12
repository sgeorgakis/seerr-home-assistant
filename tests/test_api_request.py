"""Tests for SeerrClient._request — the core HTTP method."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from custom_components.seerr_home_assistant.api import (
    SeerrApiError,
    SeerrAuthError,
    SeerrClient,
    SeerrConnectionError,
)
from tests.conftest import (
    STATUS_RESPONSE,
    TEST_API_KEY,
    TEST_HOST,
    TEST_PORT,
    make_mock_response,
    make_mock_session,
)


def make_client(session=None) -> SeerrClient:
    return SeerrClient(TEST_HOST, TEST_PORT, TEST_API_KEY, session=session)


# ---------------------------------------------------------------------------
# Successful responses
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_returns_parsed_json_on_success():
    session = make_mock_session(make_mock_response(200, STATUS_RESPONSE))
    client = make_client(session)
    result = await client._request("GET", "/status")
    assert result == STATUS_RESPONSE


@pytest.mark.asyncio
async def test_204_returns_empty_dict():
    response = make_mock_response(204)
    session = make_mock_session(response)
    client = make_client(session)
    result = await client._request("GET", "/status")
    assert result == {}


# ---------------------------------------------------------------------------
# Auth errors
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_401_raises_seerr_auth_error():
    session = make_mock_session(make_mock_response(401))
    client = make_client(session)
    with pytest.raises(SeerrAuthError):
        await client._request("GET", "/status")


@pytest.mark.asyncio
async def test_403_raises_seerr_auth_error():
    session = make_mock_session(make_mock_response(403))
    client = make_client(session)
    with pytest.raises(SeerrAuthError):
        await client._request("GET", "/status")


@pytest.mark.asyncio
async def test_auth_error_message_contains_status_code():
    session = make_mock_session(make_mock_response(401))
    client = make_client(session)
    with pytest.raises(SeerrAuthError, match="401"):
        await client._request("GET", "/status")


# ---------------------------------------------------------------------------
# API errors
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_500_raises_seerr_api_error():
    session = make_mock_session(make_mock_response(500))
    client = make_client(session)
    with pytest.raises(SeerrApiError):
        await client._request("GET", "/status")


@pytest.mark.asyncio
async def test_404_raises_seerr_api_error():
    session = make_mock_session(make_mock_response(404))
    client = make_client(session)
    with pytest.raises(SeerrApiError):
        await client._request("GET", "/request/999")


# ---------------------------------------------------------------------------
# Connection errors
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_connector_error_raises_seerr_connection_error():
    exc = aiohttp.ClientConnectorError(MagicMock(), OSError("refused"))
    session = make_mock_session(side_effect=exc)
    client = make_client(session)
    with pytest.raises(SeerrConnectionError):
        await client._request("GET", "/status")


@pytest.mark.asyncio
async def test_timeout_raises_seerr_connection_error():
    session = make_mock_session(side_effect=asyncio.TimeoutError())
    client = make_client(session)
    with pytest.raises(SeerrConnectionError):
        await client._request("GET", "/status")


@pytest.mark.asyncio
async def test_connection_error_message_contains_host():
    exc = aiohttp.ClientConnectorError(MagicMock(), OSError("refused"))
    session = make_mock_session(side_effect=exc)
    client = make_client(session)
    with pytest.raises(SeerrConnectionError, match=TEST_HOST):
        await client._request("GET", "/status")


# ---------------------------------------------------------------------------
# Request construction
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_api_key_sent_in_x_api_key_header():
    response = make_mock_response(200, STATUS_RESPONSE)
    session = make_mock_session(response)
    client = make_client(session)
    await client._request("GET", "/status")
    call_kwargs = session.request.call_args.kwargs
    assert call_kwargs["headers"]["X-Api-Key"] == TEST_API_KEY


@pytest.mark.asyncio
async def test_api_key_not_in_url():
    response = make_mock_response(200, STATUS_RESPONSE)
    session = make_mock_session(response)
    client = make_client(session)
    await client._request("GET", "/status")
    url = str(session.request.call_args.args[1])
    assert TEST_API_KEY not in url


@pytest.mark.asyncio
async def test_correct_url_constructed():
    response = make_mock_response(200, STATUS_RESPONSE)
    session = make_mock_session(response)
    client = make_client(session)
    await client._request("GET", "/status")
    url = session.request.call_args.args[1]
    assert url == f"http://{TEST_HOST}:{TEST_PORT}/api/v1/status"


@pytest.mark.asyncio
async def test_params_forwarded():
    response = make_mock_response(200, {})
    session = make_mock_session(response)
    client = make_client(session)
    await client._request("GET", "/request", params={"take": 5})
    assert session.request.call_args.kwargs["params"] == {"take": 5}


@pytest.mark.asyncio
async def test_json_body_forwarded():
    response = make_mock_response(200, {})
    session = make_mock_session(response)
    client = make_client(session)
    await client._request("POST", "/request", json={"mediaId": 1})
    assert session.request.call_args.kwargs["json"] == {"mediaId": 1}


# ---------------------------------------------------------------------------
# Session lifecycle
# ---------------------------------------------------------------------------


def test_owned_session_not_created_at_init():
    client = make_client(session=None)
    assert client._session is None
    assert client._external_session is False


@pytest.mark.asyncio
async def test_external_session_not_closed():
    session = make_mock_session(make_mock_response(200, STATUS_RESPONSE))
    client = make_client(session)
    await client.close()
    session.close.assert_not_called()


@pytest.mark.asyncio
async def test_https_base_url_when_ssl_true():
    client = SeerrClient(TEST_HOST, TEST_PORT, TEST_API_KEY, ssl=True)
    assert client._base_url.startswith("https://")


@pytest.mark.asyncio
async def test_http_base_url_when_ssl_false():
    client = SeerrClient(TEST_HOST, TEST_PORT, TEST_API_KEY, ssl=False)
    assert client._base_url.startswith("http://")
