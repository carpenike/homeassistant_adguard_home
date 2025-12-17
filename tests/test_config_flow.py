"""Tests for the AdGuard Home Extended config flow."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.adguard_home_extended.api.models import AdGuardHomeStatus
from custom_components.adguard_home_extended.config_flow import (
    AdGuardHomeConfigFlow,
    AdGuardHomeOptionsFlow,
)
from custom_components.adguard_home_extended.const import DEFAULT_SCAN_INTERVAL


class TestConfigFlow:
    """Tests for the config flow."""

    @pytest.mark.asyncio
    async def test_form_user_success(self, hass: HomeAssistant) -> None:
        """Test successful user form submission."""
        flow = AdGuardHomeConfigFlow()
        flow.hass = hass

        # Get the form first
        result = await flow.async_step_user()
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"

        # Now submit the form with mocked client
        with patch(
            "custom_components.adguard_home_extended.config_flow.AdGuardHomeClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_status = AdGuardHomeStatus(
                protection_enabled=True,
                running=True,
                version="0.107.43",
            )
            mock_client.get_status = AsyncMock(return_value=mock_status)
            mock_client_class.return_value = mock_client

            result = await flow.async_step_user(
                user_input={
                    "host": "192.168.1.1",
                    "port": 3000,
                    "username": "admin",
                    "password": "password",
                    "ssl": False,
                    "verify_ssl": True,
                }
            )

            assert result["type"] == FlowResultType.CREATE_ENTRY
            assert "192.168.1.1" in result["title"]
            assert result["data"]["host"] == "192.168.1.1"
            assert result["data"]["port"] == 3000

    @pytest.mark.asyncio
    async def test_form_user_cannot_connect(self, hass: HomeAssistant) -> None:
        """Test connection failure."""
        from custom_components.adguard_home_extended.api.client import (
            AdGuardHomeConnectionError,
        )

        flow = AdGuardHomeConfigFlow()
        flow.hass = hass

        with patch(
            "custom_components.adguard_home_extended.config_flow.AdGuardHomeClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_status = AsyncMock(
                side_effect=AdGuardHomeConnectionError("Connection failed")
            )
            mock_client_class.return_value = mock_client

            result = await flow.async_step_user(
                user_input={
                    "host": "192.168.1.1",
                    "port": 3000,
                    "username": "admin",
                    "password": "wrong",
                    "ssl": False,
                    "verify_ssl": True,
                }
            )

            assert result["type"] == FlowResultType.FORM
            assert result["errors"] == {"base": "cannot_connect"}

    @pytest.mark.asyncio
    async def test_form_user_invalid_auth(self, hass: HomeAssistant) -> None:
        """Test invalid authentication."""
        from custom_components.adguard_home_extended.api.client import (
            AdGuardHomeAuthError,
        )

        flow = AdGuardHomeConfigFlow()
        flow.hass = hass

        with patch(
            "custom_components.adguard_home_extended.config_flow.AdGuardHomeClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_status = AsyncMock(
                side_effect=AdGuardHomeAuthError("Invalid credentials")
            )
            mock_client_class.return_value = mock_client

            result = await flow.async_step_user(
                user_input={
                    "host": "192.168.1.1",
                    "port": 3000,
                    "username": "admin",
                    "password": "wrong",
                    "ssl": False,
                    "verify_ssl": True,
                }
            )

            assert result["type"] == FlowResultType.FORM
            assert result["errors"] == {"base": "invalid_auth"}


class TestOptionsFlow:
    """Tests for the options flow."""

    @pytest.mark.asyncio
    async def test_options_flow_init_shows_form(self, hass: HomeAssistant) -> None:
        """Test options flow shows form with current values."""
        # Create a mock config entry
        mock_entry = MagicMock()
        mock_entry.options = {CONF_SCAN_INTERVAL: 60}

        flow = AdGuardHomeOptionsFlow(mock_entry)
        flow.hass = hass

        result = await flow.async_step_init()

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "init"
        # Check that the schema has the scan_interval field
        assert CONF_SCAN_INTERVAL in str(result["data_schema"].schema)

    @pytest.mark.asyncio
    async def test_options_flow_init_default_value(self, hass: HomeAssistant) -> None:
        """Test options flow uses default when no options set."""
        # Create a mock config entry with no options
        mock_entry = MagicMock()
        mock_entry.options = {}

        flow = AdGuardHomeOptionsFlow(mock_entry)
        flow.hass = hass

        result = await flow.async_step_init()

        assert result["type"] == FlowResultType.FORM
        # The default value should be DEFAULT_SCAN_INTERVAL
        schema = result["data_schema"].schema
        scan_interval_key = next(k for k in schema if k.schema == CONF_SCAN_INTERVAL)
        assert scan_interval_key.default() == DEFAULT_SCAN_INTERVAL

    @pytest.mark.asyncio
    async def test_options_flow_submit(self, hass: HomeAssistant) -> None:
        """Test options flow saves new values."""
        mock_entry = MagicMock()
        mock_entry.options = {CONF_SCAN_INTERVAL: 30}

        flow = AdGuardHomeOptionsFlow(mock_entry)
        flow.hass = hass

        result = await flow.async_step_init(user_input={CONF_SCAN_INTERVAL: 120})

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"] == {CONF_SCAN_INTERVAL: 120}

    def test_config_flow_has_options_flow_handler(self) -> None:
        """Test that config flow has options flow handler."""
        mock_entry = MagicMock()

        # The @staticmethod decorator means we call it on the class, not instance
        options_flow = AdGuardHomeConfigFlow.async_get_options_flow(mock_entry)

        assert isinstance(options_flow, AdGuardHomeOptionsFlow)


# Note: already_configured and reauth tests require full integration setup
# These should be tested via integration tests with a real Home Assistant instance
