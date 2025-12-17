"""Tests for the AdGuard Home Extended coordinator."""
from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.adguard_home_extended.api.client import (
    AdGuardHomeAuthError,
    AdGuardHomeConnectionError,
)
from custom_components.adguard_home_extended.api.models import (
    AdGuardHomeStats,
    AdGuardHomeStatus,
)
from custom_components.adguard_home_extended.const import DEFAULT_SCAN_INTERVAL
from custom_components.adguard_home_extended.coordinator import (
    AdGuardHomeData,
    AdGuardHomeDataUpdateCoordinator,
)


class TestAdGuardHomeData:
    """Tests for AdGuardHomeData container."""

    def test_init(self) -> None:
        """Test data container initialization."""
        data = AdGuardHomeData()

        assert data.status is None
        assert data.stats is None
        assert data.filtering is None
        assert data.blocked_services == []
        assert data.available_services == []
        assert data.clients == []
        assert data.dhcp is None


class TestAdGuardHomeDataUpdateCoordinator:
    """Tests for AdGuardHomeDataUpdateCoordinator."""

    @pytest.fixture
    def mock_client(self) -> AsyncMock:
        """Return a mock AdGuard Home client."""
        client = AsyncMock()
        client.get_status = AsyncMock(
            return_value=AdGuardHomeStatus(
                protection_enabled=True,
                running=True,
                version="0.107.43",
            )
        )
        client.get_stats = AsyncMock(
            return_value=AdGuardHomeStats(
                dns_queries=1000,
                blocked_filtering=100,
            )
        )
        client.get_filtering_status = AsyncMock(return_value=MagicMock())
        client.get_blocked_services = AsyncMock(return_value=["facebook"])
        client.get_all_blocked_services = AsyncMock(return_value=[])
        client.get_clients = AsyncMock(return_value=[])
        client.get_dhcp_status = AsyncMock(return_value=MagicMock(enabled=False))
        return client

    @pytest.fixture
    def mock_entry(self) -> MagicMock:
        """Return a mock config entry."""
        entry = MagicMock()
        entry.entry_id = "test_entry"
        entry.options = {}  # Empty options, should use default
        return entry

    def test_scan_interval_default(
        self, hass: HomeAssistant, mock_client: AsyncMock, mock_entry: MagicMock
    ) -> None:
        """Test coordinator uses default scan interval when no options set."""
        mock_entry.options = {}

        coordinator = AdGuardHomeDataUpdateCoordinator(hass, mock_client, mock_entry)

        assert coordinator.update_interval == timedelta(seconds=DEFAULT_SCAN_INTERVAL)

    def test_scan_interval_from_options(
        self, hass: HomeAssistant, mock_client: AsyncMock, mock_entry: MagicMock
    ) -> None:
        """Test coordinator uses scan interval from options."""
        mock_entry.options = {CONF_SCAN_INTERVAL: 120}

        coordinator = AdGuardHomeDataUpdateCoordinator(hass, mock_client, mock_entry)

        assert coordinator.update_interval == timedelta(seconds=120)

    @pytest.mark.asyncio
    async def test_update_data_success(
        self, hass: HomeAssistant, mock_client: AsyncMock, mock_entry: MagicMock
    ) -> None:
        """Test successful data update."""
        coordinator = AdGuardHomeDataUpdateCoordinator(hass, mock_client, mock_entry)

        data = await coordinator._async_update_data()

        assert data is not None
        assert data.status is not None
        assert data.status.protection_enabled is True
        assert data.status.running is True
        assert data.stats is not None
        assert data.stats.dns_queries == 1000

    @pytest.mark.asyncio
    async def test_update_data_connection_error(
        self, hass: HomeAssistant, mock_entry: MagicMock
    ) -> None:
        """Test data update with connection error."""
        mock_client = AsyncMock()
        mock_client.get_status = AsyncMock(
            side_effect=AdGuardHomeConnectionError("Connection failed")
        )

        coordinator = AdGuardHomeDataUpdateCoordinator(hass, mock_client, mock_entry)

        with pytest.raises(UpdateFailed, match="Error communicating with AdGuard Home"):
            await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_update_data_auth_error(
        self, hass: HomeAssistant, mock_entry: MagicMock
    ) -> None:
        """Test data update with authentication error."""
        from homeassistant.exceptions import ConfigEntryAuthFailed

        mock_client = AsyncMock()
        mock_client.get_status = AsyncMock(
            side_effect=AdGuardHomeAuthError("Invalid credentials")
        )

        coordinator = AdGuardHomeDataUpdateCoordinator(hass, mock_client, mock_entry)

        with pytest.raises(ConfigEntryAuthFailed):
            await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_update_data_partial_failure(
        self, hass: HomeAssistant, mock_client: AsyncMock, mock_entry: MagicMock
    ) -> None:
        """Test data update with partial failure (non-critical endpoints)."""
        # Make filtering status fail, but status and stats succeed
        mock_client.get_filtering_status = AsyncMock(
            side_effect=AdGuardHomeConnectionError("Endpoint not available")
        )

        coordinator = AdGuardHomeDataUpdateCoordinator(hass, mock_client, mock_entry)

        data = await coordinator._async_update_data()

        # Should still succeed with required data
        assert data is not None
        assert data.status is not None
        assert data.stats is not None
        # Filtering should be None due to error
        assert data.filtering is None

    def test_device_info(self, hass: HomeAssistant, mock_entry: MagicMock) -> None:
        """Test device info property."""
        # Create a fresh mock client for this test
        mock_client = AsyncMock()

        # Create a proper mock entry with data dict and options
        mock_entry_with_data = MagicMock()
        mock_entry_with_data.entry_id = "test_entry"
        mock_entry_with_data.data = {"host": "192.168.1.1", "port": 3000}
        mock_entry_with_data.options = {}  # Empty options, use default scan interval

        coordinator = AdGuardHomeDataUpdateCoordinator(
            hass, mock_client, mock_entry_with_data
        )
        # Set data manually for testing
        coordinator.data = AdGuardHomeData()
        coordinator.data.status = AdGuardHomeStatus(
            protection_enabled=True,
            running=True,
            version="0.107.43",
        )

        device_info = coordinator.device_info

        assert "AdGuard Home" in device_info["name"]
        assert device_info["manufacturer"] == "AdGuard"
        assert device_info["sw_version"] == "0.107.43"
