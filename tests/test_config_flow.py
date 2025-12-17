"""Tests for the AdGuard Home Extended config flow."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.adguard_home_extended.const import DOMAIN


class TestConfigFlow:
    """Tests for the config flow."""

    @pytest.mark.asyncio
    async def test_form_user(self, hass: HomeAssistant) -> None:
        """Test we get the user form."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"

    @pytest.mark.asyncio
    async def test_form_user_success(self, hass: HomeAssistant) -> None:
        """Test successful user form submission."""
        with patch(
            "custom_components.adguard_home_extended.config_flow.AdGuardHomeClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client.test_connection = AsyncMock(return_value=True)
            mock_client_class.return_value = mock_client

            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )

            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    "host": "192.168.1.1",
                    "port": 3000,
                    "username": "admin",
                    "password": "password",
                    "ssl": False,
                    "verify_ssl": True,
                },
            )

            assert result["type"] == FlowResultType.CREATE_ENTRY
            assert result["title"] == "192.168.1.1"
            assert result["data"]["host"] == "192.168.1.1"
            assert result["data"]["port"] == 3000

    @pytest.mark.asyncio
    async def test_form_user_cannot_connect(self, hass: HomeAssistant) -> None:
        """Test connection failure."""
        with patch(
            "custom_components.adguard_home_extended.config_flow.AdGuardHomeClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client.test_connection = AsyncMock(return_value=False)
            mock_client_class.return_value = mock_client

            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )

            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    "host": "192.168.1.1",
                    "port": 3000,
                    "username": "admin",
                    "password": "wrong",
                    "ssl": False,
                    "verify_ssl": True,
                },
            )

            assert result["type"] == FlowResultType.FORM
            assert result["errors"] == {"base": "cannot_connect"}

    @pytest.mark.asyncio
    async def test_form_user_invalid_auth(self, hass: HomeAssistant) -> None:
        """Test invalid authentication."""
        from custom_components.adguard_home_extended.api.client import (
            AdGuardHomeAuthError,
        )

        with patch(
            "custom_components.adguard_home_extended.config_flow.AdGuardHomeClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client.test_connection = AsyncMock(
                side_effect=AdGuardHomeAuthError("Invalid credentials")
            )
            mock_client_class.return_value = mock_client

            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )

            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    "host": "192.168.1.1",
                    "port": 3000,
                    "username": "admin",
                    "password": "wrong",
                    "ssl": False,
                    "verify_ssl": True,
                },
            )

            assert result["type"] == FlowResultType.FORM
            assert result["errors"] == {"base": "invalid_auth"}

    @pytest.mark.asyncio
    async def test_form_user_already_configured(self, hass: HomeAssistant) -> None:
        """Test already configured error."""
        # First, add an existing entry
        entry = config_entries.ConfigEntry(
            version=1,
            minor_version=1,
            domain=DOMAIN,
            title="192.168.1.1",
            data={
                "host": "192.168.1.1",
                "port": 3000,
            },
            source=config_entries.SOURCE_USER,
            unique_id="192.168.1.1:3000",
        )
        entry.add_to_hass(hass)

        with patch(
            "custom_components.adguard_home_extended.config_flow.AdGuardHomeClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client.test_connection = AsyncMock(return_value=True)
            mock_client_class.return_value = mock_client

            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )

            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    "host": "192.168.1.1",
                    "port": 3000,
                    "username": "admin",
                    "password": "password",
                    "ssl": False,
                    "verify_ssl": True,
                },
            )

            assert result["type"] == FlowResultType.ABORT
            assert result["reason"] == "already_configured"


class TestReauthFlow:
    """Tests for reauthentication flow."""

    @pytest.mark.asyncio
    async def test_reauth_success(self, hass: HomeAssistant) -> None:
        """Test successful reauthentication."""
        # Add existing entry
        entry = config_entries.ConfigEntry(
            version=1,
            minor_version=1,
            domain=DOMAIN,
            title="192.168.1.1",
            data={
                "host": "192.168.1.1",
                "port": 3000,
                "username": "admin",
                "password": "old_password",
                "ssl": False,
                "verify_ssl": True,
            },
            source=config_entries.SOURCE_USER,
            unique_id="192.168.1.1:3000",
        )
        entry.add_to_hass(hass)

        with patch(
            "custom_components.adguard_home_extended.config_flow.AdGuardHomeClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client.test_connection = AsyncMock(return_value=True)
            mock_client_class.return_value = mock_client

            result = await hass.config_entries.flow.async_init(
                DOMAIN,
                context={
                    "source": config_entries.SOURCE_REAUTH,
                    "entry_id": entry.entry_id,
                },
                data=entry.data,
            )

            assert result["type"] == FlowResultType.FORM
            assert result["step_id"] == "reauth_confirm"

            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    "username": "admin",
                    "password": "new_password",
                },
            )

            assert result["type"] == FlowResultType.ABORT
            assert result["reason"] == "reauth_successful"
