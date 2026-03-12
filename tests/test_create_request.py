"""Tests for create_request — POST /api/v1/request/."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from custom_components.seerr_home_assistant.api import (
    SeerrAuthError,
    SeerrClient,
    SeerrConnectionError,
)
from tests.conftest import CREATED_REQUEST_RESPONSE, TEST_API_KEY, TEST_HOST, TEST_PORT


def make_client() -> SeerrClient:
    return SeerrClient(TEST_HOST, TEST_PORT, TEST_API_KEY)


# ---------------------------------------------------------------------------
# Correct endpoint and method
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_uses_post_to_request_slash():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value=CREATED_REQUEST_RESPONSE) as mock_req:
        await client.create_request(media_id=550, media_type="movie")
    assert mock_req.call_args.args == ("POST", "/request/")


# ---------------------------------------------------------------------------
# Request body — required fields
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_body_contains_media_type_and_id():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value=CREATED_REQUEST_RESPONSE) as mock_req:
        await client.create_request(media_id=550, media_type="movie")
    body = mock_req.call_args.kwargs["json"]
    assert body["mediaType"] == "movie"
    assert body["mediaId"] == 550


@pytest.mark.asyncio
async def test_is4k_defaults_to_false():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value=CREATED_REQUEST_RESPONSE) as mock_req:
        await client.create_request(media_id=550, media_type="movie")
    assert mock_req.call_args.kwargs["json"]["is4k"] is False


# ---------------------------------------------------------------------------
# Request body — optional fields
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tvdb_id_included_when_provided():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value=CREATED_REQUEST_RESPONSE) as mock_req:
        await client.create_request(media_id=1396, media_type="tv", tvdb_id=81189)
    assert mock_req.call_args.kwargs["json"]["tvdbId"] == 81189


@pytest.mark.asyncio
async def test_seasons_included_when_provided():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value=CREATED_REQUEST_RESPONSE) as mock_req:
        await client.create_request(media_id=1396, media_type="tv", seasons=[1, 2, 3])
    assert mock_req.call_args.kwargs["json"]["seasons"] == [1, 2, 3]


@pytest.mark.asyncio
async def test_is4k_true_included():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value=CREATED_REQUEST_RESPONSE) as mock_req:
        await client.create_request(media_id=550, media_type="movie", is4k=True)
    assert mock_req.call_args.kwargs["json"]["is4k"] is True


@pytest.mark.asyncio
async def test_all_optional_fields_included():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value=CREATED_REQUEST_RESPONSE) as mock_req:
        await client.create_request(
            media_id=550,
            media_type="movie",
            server_id=1,
            profile_id=4,
            root_folder="/movies",
            language_profile_id=2,
            user_id=7,
        )
    body = mock_req.call_args.kwargs["json"]
    assert body["serverId"] == 1
    assert body["profileId"] == 4
    assert body["rootFolder"] == "/movies"
    assert body["languageProfileId"] == 2
    assert body["userId"] == 7


# ---------------------------------------------------------------------------
# Optional fields omitted when not provided
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_optional_fields_absent_when_not_provided():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value=CREATED_REQUEST_RESPONSE) as mock_req:
        await client.create_request(media_id=550, media_type="movie")
    body = mock_req.call_args.kwargs["json"]
    assert "tvdbId" not in body
    assert "seasons" not in body
    assert "serverId" not in body
    assert "profileId" not in body
    assert "rootFolder" not in body
    assert "languageProfileId" not in body
    assert "userId" not in body


# ---------------------------------------------------------------------------
# Return value
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_returns_created_request():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, return_value=CREATED_REQUEST_RESPONSE):
        result = await client.create_request(media_id=550, media_type="movie")
    assert result["id"] == 456
    assert result["status"] == 1


# ---------------------------------------------------------------------------
# Error propagation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_auth_error_propagates():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, side_effect=SeerrAuthError("bad key")):
        with pytest.raises(SeerrAuthError):
            await client.create_request(media_id=550, media_type="movie")


@pytest.mark.asyncio
async def test_connection_error_propagates():
    client = make_client()
    with patch.object(client, "_request", new_callable=AsyncMock, side_effect=SeerrConnectionError("timeout")):
        with pytest.raises(SeerrConnectionError):
            await client.create_request(media_id=550, media_type="movie")
