"""Shared fixtures and helpers for Seerr integration tests."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

TEST_HOST = "192.168.1.100"
TEST_PORT = 5055
TEST_API_KEY = "test-api-key-abc123"
BASE_URL = f"http://{TEST_HOST}:{TEST_PORT}/api/v1"

# ---------------------------------------------------------------------------
# Reusable response payloads
# ---------------------------------------------------------------------------

PENDING_REQUESTS_RESPONSE = {
    "pageInfo": {"page": 1, "pages": 10, "results": 100},
    "results": [
        {
            "id": 123,
            "status": 1,
            "media": "string",
            "createdAt": "2020-09-12T10:00:27.000Z",
            "updatedAt": "2020-09-12T10:00:27.000Z",
            "requestedBy": {
                "id": 1,
                "email": "hey@itsme.com",
                "username": "string",
                "userType": 1,
                "permissions": 0,
                "avatar": "string",
                "createdAt": "2020-09-02T05:02:23.000Z",
                "updatedAt": "2020-09-02T05:02:23.000Z",
                "requestCount": 5,
            },
            "modifiedBy": None,
            "is4k": False,
            "serverId": 0,
            "profileId": 0,
            "rootFolder": "string",
        }
    ],
}

SINGLE_REQUEST_RESPONSE = {
    "id": 123,
    "status": 0,
    "media": "string",
    "createdAt": "2020-09-12T10:00:27.000Z",
    "updatedAt": "2020-09-12T10:00:27.000Z",
    "requestedBy": {
        "id": 1,
        "email": "hey@itsme.com",
        "username": "string",
        "userType": 1,
        "permissions": 0,
        "avatar": "string",
        "createdAt": "2020-09-02T05:02:23.000Z",
        "updatedAt": "2020-09-02T05:02:23.000Z",
        "requestCount": 5,
    },
    "modifiedBy": None,
    "is4k": False,
    "serverId": 0,
    "profileId": 0,
    "rootFolder": "string",
}

UPDATED_REQUEST_RESPONSE = {**SINGLE_REQUEST_RESPONSE, "status": 2}

CREATED_REQUEST_RESPONSE = {
    "id": 456,
    "status": 1,
    "media": "string",
    "createdAt": "2020-09-12T10:00:27.000Z",
    "updatedAt": "2020-09-12T10:00:27.000Z",
    "requestedBy": {
        "id": 1,
        "email": "hey@itsme.com",
        "username": "string",
        "userType": 1,
        "permissions": 0,
        "avatar": "string",
        "createdAt": "2020-09-02T05:02:23.000Z",
        "updatedAt": "2020-09-02T05:02:23.000Z",
        "requestCount": 5,
    },
    "modifiedBy": None,
    "is4k": False,
    "serverId": 0,
    "profileId": 0,
    "rootFolder": "string",
}

STATUS_RESPONSE = {
    "appName": "Seerr",
    "version": "1.0.0",
}

# ---------------------------------------------------------------------------
# Mock HTTP helpers (no real TCP — no background threads)
# ---------------------------------------------------------------------------


def make_mock_response(
    status: int = 200,
    json_data: dict | None = None,
) -> MagicMock:
    """Return a mock aiohttp response suitable for use as an async context manager."""
    response = MagicMock()
    response.status = status
    response.json = AsyncMock(return_value=json_data or {})

    if status in (401, 403):
        response.raise_for_status = MagicMock()  # auth check happens before raise_for_status
    elif status >= 400:
        response.raise_for_status = MagicMock(
            side_effect=aiohttp.ClientResponseError(
                request_info=MagicMock(), history=(), status=status
            )
        )
    else:
        response.raise_for_status = MagicMock()

    response.__aenter__ = AsyncMock(return_value=response)
    response.__aexit__ = AsyncMock(return_value=False)
    return response


def make_mock_session(
    response: MagicMock | None = None,
    side_effect: Exception | None = None,
) -> MagicMock:
    """Return a mock aiohttp.ClientSession.

    Pass ``side_effect`` to simulate network-level failures (raised in __aenter__).
    """
    session = MagicMock(spec=aiohttp.ClientSession)
    session.closed = False

    cm = MagicMock()
    if side_effect is not None:
        cm.__aenter__ = AsyncMock(side_effect=side_effect)
    else:
        cm.__aenter__ = AsyncMock(return_value=response)
    cm.__aexit__ = AsyncMock(return_value=False)

    session.request = MagicMock(return_value=cm)
    return session
