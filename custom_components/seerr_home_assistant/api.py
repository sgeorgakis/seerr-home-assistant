"""Async API client for Jellyseerr / Overseerr."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Literal

import aiohttp

from .const import API_BASE_PATH, REQUEST_TIMEOUT

_LOGGER = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

MediaType = Literal["movie", "tv"]

RequestFilter = Literal[
    "all", "pending", "approved", "declined", "available", "processing"
]

RequestSort = Literal["added", "modified"]


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class SeerrError(Exception):
    """Base exception for all Seerr API errors."""


class SeerrAuthError(SeerrError):
    """Raised on HTTP 401 / 403 — invalid or missing API key."""


class SeerrConnectionError(SeerrError):
    """Raised when the Seerr server cannot be reached."""


class SeerrApiError(SeerrError):
    """Raised when the server returns an unexpected HTTP error."""


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class SeerrClient:
    """Async client for the Jellyseerr / Overseerr REST API.

    Accepts an externally managed ``aiohttp.ClientSession`` (e.g. the one
    provided by ``homeassistant.helpers.aiohttp_client.async_get_clientsession``).
    If none is supplied a private session is created and owned by this instance.

    The API key is stored as a private attribute and is **never** written to
    any logger.
    """

    def __init__(
        self,
        host: str,
        port: int,
        api_key: str,
        *,
        ssl: bool = False,
        verify_ssl: bool = True,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self._host = host.strip().rstrip("/")
        self._port = port
        self._api_key = api_key
        self._ssl = ssl
        self._verify_ssl = verify_ssl

        scheme = "https" if ssl else "http"
        self._base_url = f"{scheme}://{self._host}:{self._port}{API_BASE_PATH}"

        self._external_session = session is not None
        self._session: aiohttp.ClientSession | None = session
        self._timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_session(self) -> aiohttp.ClientSession:
        """Return the active session, creating a private one if needed."""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                ssl=None if not self._ssl else self._verify_ssl
            )
            self._session = aiohttp.ClientSession(connector=connector)
            self._external_session = False
        return self._session

    @property
    def _headers(self) -> dict[str, str]:
        # The API key is injected here and ONLY here — never passed to a logger.
        return {
            "X-Api-Key": self._api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        """Execute an authenticated HTTP request and return the parsed JSON body.

        Args:
            method:   HTTP verb (``GET``, ``POST``, ``DELETE`` …).
            endpoint: Path relative to the API base, e.g. ``"/status"``.
            params:   Optional query-string parameters.
            json:     Optional request body (serialised to JSON).

        Raises:
            SeerrAuthError:       Server rejected the API key (401/403).
            SeerrConnectionError: Network-level failure or timeout.
            SeerrApiError:        Any other non-2xx HTTP response.
        """
        url = f"{self._base_url}{endpoint}"
        session = self._get_session()

        _LOGGER.debug("Seerr → %s %s params=%s", method, endpoint, params)

        try:
            async with session.request(
                method,
                url,
                headers=self._headers,
                params=params,
                json=json,
                timeout=self._timeout,
            ) as response:
                if response.status in (401, 403):
                    raise SeerrAuthError(
                        f"Authentication failed (HTTP {response.status}). "
                        "Check your API key."
                    )
                response.raise_for_status()
                if response.status == 204:
                    # No Content — return empty dict so callers always get a dict.
                    return {}
                return await response.json()

        except SeerrAuthError:
            raise
        except aiohttp.ClientConnectorError as exc:
            raise SeerrConnectionError(
                f"Cannot connect to {self._host}:{self._port}"
            ) from exc
        except aiohttp.ClientResponseError as exc:
            raise SeerrApiError(
                f"Unexpected response from Seerr (HTTP {exc.status})"
            ) from exc
        except asyncio.TimeoutError as exc:
            raise SeerrConnectionError(
                f"Request to {self._host}:{self._port} timed out"
            ) from exc

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    async def get_status(self) -> dict[str, Any]:
        """Return server status.  Also used to validate connectivity + credentials."""
        return await self._request("GET", "/status")

    # ------------------------------------------------------------------
    # Search  —  GET /api/v1/search
    # ------------------------------------------------------------------

    async def search(
        self,
        query: str,
        *,
        page: int = 1,
    ) -> dict[str, Any]:
        """Search for media by keyword.

        Args:
            query: Search string (required).
            page:  Page number for paginated results (default ``1``).

        Returns:
            Paginated response with ``results`` and ``pageInfo``.
        """
        return await self._request(
            "GET",
            "/search/keyword",
            params={"query": query, "page": page},
        )

    # ------------------------------------------------------------------
    # Requests  —  GET /api/v1/request
    # ------------------------------------------------------------------

    async def get_requests(
        self,
        *,
        take: int = 20,
        skip: int = 0,
        filter: RequestFilter = "all",
        sort: RequestSort = "added",
        requested_by: int | None = None,
    ) -> dict[str, Any]:
        """Return a paginated list of media requests.

        Args:
            take:         Number of results to return (page size).
            skip:         Number of results to skip (offset).
            filter:       Status filter — one of ``"all"``, ``"pending"``,
                          ``"approved"``, ``"declined"``, ``"available"``,
                          ``"processing"``.
            sort:         Sort order — ``"added"`` or ``"modified"``.
            requested_by: Filter by requesting user ID (optional).

        Returns:
            Dict with ``results`` (list of ``MediaRequest``) and ``pageInfo``.
        """
        params: dict[str, Any] = {
            "take": take,
            "skip": skip,
            "filter": filter,
            "sort": sort,
        }
        if requested_by is not None:
            params["requestedBy"] = requested_by
        return await self._request("GET", "/request", params=params)

    async def get_request_count(self) -> dict[str, Any]:
        """Return aggregate counts: pending, approved, declined, available, total."""
        return await self._request("GET", "/request/count")

    async def get_request(self, request_id: int) -> dict[str, Any]:
        """Return details for a single request by its ID."""
        return await self._request("GET", f"/request/{request_id}")

    # ------------------------------------------------------------------
    # Create request  —  POST /api/v1/request
    # ------------------------------------------------------------------

    async def create_request(
        self,
        media_id: int,
        media_type: MediaType,
        *,
        seasons: list[int] | None = None,
        is4k: bool = False,
        server_id: int | None = None,
        profile_id: int | None = None,
        root_folder: str | None = None,
        language_profile_id: int | None = None,
        tags: list[int] | None = None,
    ) -> dict[str, Any]:
        """Submit a new media request.

        Args:
            media_id:            TMDB ID of the movie or TV show (required).
            media_type:          ``"movie"`` or ``"tv"`` (required).
            seasons:             List of season numbers to request; only used
                                 when ``media_type="tv"``.  Pass ``[0]`` for
                                 all seasons.
            is4k:                Request the 4K version (default ``False``).
            server_id:           Target Radarr / Sonarr server instance ID.
            profile_id:          Quality profile ID on the target server.
            root_folder:         Destination root folder path on the server.
            language_profile_id: Sonarr language profile ID (TV only).
            tags:                List of tag IDs to apply on the target server.

        Returns:
            The created ``MediaRequest`` object.
        """
        body: dict[str, Any] = {
            "mediaId": media_id,
            "mediaType": media_type,
            "is4k": is4k,
        }

        if media_type == "tv" and seasons is not None:
            body["seasons"] = seasons

        if server_id is not None:
            body["serverId"] = server_id
        if profile_id is not None:
            body["profileId"] = profile_id
        if root_folder is not None:
            body["rootFolder"] = root_folder
        if language_profile_id is not None:
            body["languageProfileId"] = language_profile_id
        if tags is not None:
            body["tags"] = tags

        return await self._request("POST", "/request", json=body)

    # ------------------------------------------------------------------
    # Request actions
    # ------------------------------------------------------------------

    async def approve_request(self, request_id: int) -> dict[str, Any]:
        """Approve a pending request."""
        return await self._request("POST", f"/request/{request_id}/approve")

    async def decline_request(self, request_id: int) -> dict[str, Any]:
        """Decline a pending request."""
        return await self._request("POST", f"/request/{request_id}/decline")

    async def delete_request(self, request_id: int) -> None:
        """Delete a request permanently."""
        await self._request("DELETE", f"/request/{request_id}")

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close the underlying session (no-op for externally managed sessions)."""
        if not self._external_session and self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self) -> SeerrClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()
