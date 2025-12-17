"""Tests for the AdGuard Home Extended config flow."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.adguard_home_extended.const import DOMAIN
from custom_components.adguard_home_extended.config_flow import AdGuardHomeConfigFlow
from custom_components.adguard_home_extended.api.models import AdGuardHomeStatus


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


# Note: already_configured and reauth tests require full integration setup
# These should be tested via integration tests with a real Home Assistant instance
