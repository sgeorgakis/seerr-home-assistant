"""Tests for remaining SeerrClient methods: search, get_requests, get_request_count,
delete_request, close, and the async context manager."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.seerr_home_assistant.api import (
    SeerrAuthError,
    SeerrClient,
    SeerrConnectionError,
)
from tests.conftest import TEST_API_KEY, TEST_HOST, TEST_PORT


def make_client() -> SeerrClient:
    return SeerrClient(TEST_HOST, TEST_PORT, TEST_API_KEY)


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_calls_correct_endpoint():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value={}) as mock_req:
        await client.search("Fight Club")
    assert mock_req.call_args.args == ("GET", "/search/keyword")


@pytest.mark.asyncio
async def test_search_sends_query_param():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value={}) as mock_req:
        await client.search("Breaking Bad")
    assert mock_req.call_args.kwargs["params"]["query"] == "Breaking Bad"


@pytest.mark.asyncio
async def test_search_default_page_is_1():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value={}) as mock_req:
        await client.search("query")
    assert mock_req.call_args.kwargs["params"]["page"] == 1


@pytest.mark.asyncio
async def test_search_custom_page():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value={}) as mock_req:
        await client.search("query", page=3)
    assert mock_req.call_args.kwargs["params"]["page"] == 3


@pytest.mark.asyncio
async def test_search_auth_error_propagates():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, side_effect=SeerrAuthError("bad")):
        with pytest.raises(SeerrAuthError):
            await client.search("query")


# ---------------------------------------------------------------------------
# get_requests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_requests_calls_correct_endpoint():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value={}) as mock_req:
        await client.get_requests()
    assert mock_req.call_args.args == ("GET", "/request")


@pytest.mark.asyncio
async def test_get_requests_default_params():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value={}) as mock_req:
        await client.get_requests()
    params = mock_req.call_args.kwargs["params"]
    assert params["take"] == 20
    assert params["skip"] == 0
    assert params["filter"] == "all"
    assert params["sort"] == "added"


@pytest.mark.asyncio
async def test_get_requests_with_requested_by():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value={}) as mock_req:
        await client.get_requests(requested_by=5)
    assert mock_req.call_args.kwargs["params"]["requestedBy"] == 5


@pytest.mark.asyncio
async def test_get_requests_without_requested_by_omits_param():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value={}) as mock_req:
        await client.get_requests()
    assert "requestedBy" not in mock_req.call_args.kwargs["params"]


# ---------------------------------------------------------------------------
# get_request_count
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_request_count_calls_correct_endpoint():
    client = make_client()
    payload = {"pending": 3, "total": 10}
    with patch.object(client, "_request", new_callable=AsyncMock, return_value=payload) as mock_req:
        result = await client.get_request_count()
    assert mock_req.call_args.args == ("GET", "/request/count")
    assert result["pending"] == 3


# ---------------------------------------------------------------------------
# delete_request
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_request_calls_correct_endpoint():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value={}) as mock_req:
        await client.delete_request(7)
    assert mock_req.call_args.args == ("DELETE", "/request/7")


@pytest.mark.asyncio
async def test_delete_request_returns_none():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value={}):
        result = await client.delete_request(7)
    assert result is None


@pytest.mark.asyncio
async def test_delete_request_connection_error_propagates():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, side_effect=SeerrConnectionError("timeout")):
        with pytest.raises(SeerrConnectionError):
            await client.delete_request(7)


# ---------------------------------------------------------------------------
# get_status
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_status_calls_correct_endpoint():
    client = make_client()
    payload = {"appName": "Seerr", "version": "1.0.0"}
    with patch.object(client, "_request", new_callable=AsyncMock, return_value=payload) as mock_req:
        result = await client.get_status()
    assert mock_req.call_args.args == ("GET", "/status")
    assert result["appName"] == "Seerr"


# ---------------------------------------------------------------------------
# Session close / context manager
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_close_noop_for_external_session():
    mock_session = MagicMock()
    mock_session.closed = False
    mock_session.close = AsyncMock()
    client = SeerrClient(TEST_HOST, TEST_PORT, TEST_API_KEY, session=mock_session)
    await client.close()
    mock_session.close.assert_not_called()


@pytest.mark.asyncio
async def test_close_noop_when_session_already_closed():
    mock_session = MagicMock()
    mock_session.closed = True
    mock_session.close = AsyncMock()
    # Mark as owned so close would normally be called
    client = SeerrClient(TEST_HOST, TEST_PORT, TEST_API_KEY, session=mock_session)
    client._external_session = False
    await client.close()
    mock_session.close.assert_not_called()


@pytest.mark.asyncio
async def test_context_manager_returns_client():
    mock_session = MagicMock()
    mock_session.closed = False
    mock_session.close = AsyncMock()
    client = SeerrClient(TEST_HOST, TEST_PORT, TEST_API_KEY, session=mock_session)
    async with client as c:
        assert c is client


@pytest.mark.asyncio
async def test_context_manager_calls_close_on_exit():
    mock_session = MagicMock()
    mock_session.closed = False
    mock_session.close = AsyncMock()
    client = SeerrClient(TEST_HOST, TEST_PORT, TEST_API_KEY, session=mock_session)
    client._external_session = False
    async with client:
        pass
    mock_session.close.assert_called_once()
