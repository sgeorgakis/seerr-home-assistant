"""Tests for SeerrConfigFlow."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.seerr_home_assistant.api import SeerrAuthError, SeerrConnectionError
from custom_components.seerr_home_assistant.const import DOMAIN
from tests.conftest import TEST_API_KEY, TEST_HOST, TEST_PORT


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests in this module."""
    return

USER_INPUT = {
    "host": TEST_HOST,
    "port": TEST_PORT,
    "api_key": TEST_API_KEY,
    "ssl": False,
    "verify_ssl": True,
}

STATUS_RESPONSE = {"appName": "Seerr", "version": "1.0.0"}


async def _start_flow(hass: HomeAssistant):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    return result


# ---------------------------------------------------------------------------
# Success
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_form_is_shown(hass: HomeAssistant):
    result = await _start_flow(hass)
    assert result["errors"] == {}


@pytest.mark.asyncio
async def test_successful_setup_creates_entry(hass: HomeAssistant):
    with patch(
        "custom_components.seerr_home_assistant.config_flow._validate_connection",
        return_value=STATUS_RESPONSE,
    ), patch(
        "custom_components.seerr_home_assistant.async_setup_entry",
        return_value=True,
    ):
        result = await _start_flow(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=USER_INPUT
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == USER_INPUT


@pytest.mark.asyncio
async def test_entry_title_from_app_name(hass: HomeAssistant):
    with patch(
        "custom_components.seerr_home_assistant.config_flow._validate_connection",
        return_value={"appName": "MySeerr"},
    ), patch(
        "custom_components.seerr_home_assistant.async_setup_entry",
        return_value=True,
    ):
        result = await _start_flow(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=USER_INPUT
        )

    assert result["title"] == "MySeerr"


@pytest.mark.asyncio
async def test_entry_title_falls_back_when_no_app_name(hass: HomeAssistant):
    with patch(
        "custom_components.seerr_home_assistant.config_flow._validate_connection",
        return_value={},
    ), patch(
        "custom_components.seerr_home_assistant.async_setup_entry",
        return_value=True,
    ):
        result = await _start_flow(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=USER_INPUT
        )

    assert result["title"] == "Seerr"


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cannot_connect_shows_error(hass: HomeAssistant):
    with patch(
        "custom_components.seerr_home_assistant.config_flow._validate_connection",
        side_effect=SeerrConnectionError("refused"),
    ):
        result = await _start_flow(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=USER_INPUT
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


@pytest.mark.asyncio
async def test_invalid_auth_shows_error(hass: HomeAssistant):
    with patch(
        "custom_components.seerr_home_assistant.config_flow._validate_connection",
        side_effect=SeerrAuthError("bad key"),
    ):
        result = await _start_flow(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=USER_INPUT
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


@pytest.mark.asyncio
async def test_unknown_exception_shows_error(hass: HomeAssistant):
    with patch(
        "custom_components.seerr_home_assistant.config_flow._validate_connection",
        side_effect=Exception("unexpected"),
    ):
        result = await _start_flow(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=USER_INPUT
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}


# ---------------------------------------------------------------------------
# Duplicate entry
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_duplicate_entry_aborted(hass: HomeAssistant):
    with patch(
        "custom_components.seerr_home_assistant.config_flow._validate_connection",
        return_value=STATUS_RESPONSE,
    ), patch(
        "custom_components.seerr_home_assistant.async_setup_entry",
        return_value=True,
    ):
        result = await _start_flow(hass)
        await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=USER_INPUT
        )
        result = await _start_flow(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=USER_INPUT
        )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


# ---------------------------------------------------------------------------
# Retry after error
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_form_reshown_after_error_then_succeeds(hass: HomeAssistant):
    with patch(
        "custom_components.seerr_home_assistant.config_flow._validate_connection",
        side_effect=SeerrConnectionError("down"),
    ):
        result = await _start_flow(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=USER_INPUT
        )
    assert result["type"] == FlowResultType.FORM

    with patch(
        "custom_components.seerr_home_assistant.config_flow._validate_connection",
        return_value=STATUS_RESPONSE,
    ), patch(
        "custom_components.seerr_home_assistant.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=USER_INPUT
        )
    assert result["type"] == FlowResultType.CREATE_ENTRY
