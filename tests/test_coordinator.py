"""Tests for the AdGuard Home Extended coordinator."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.adguard_home_extended.api.client import (
    AdGuardHomeAuthError,
    AdGuardHomeConnectionError,
)
from custom_components.adguard_home_extended.api.models import (
    AdGuardHomeClient,
    AdGuardHomeStats,
    AdGuardHomeStatus,
    SafeSearchSettings,
)
from custom_components.adguard_home_extended.const import (
    CONF_QUERY_LOG_LIMIT,
    DEFAULT_QUERY_LOG_LIMIT,
    DEFAULT_SCAN_INTERVAL,
)
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
        assert data.dns_info is None
        assert data.blocked_services == []
        assert data.available_services == []
        assert data.clients == []
        assert data.dhcp is None

    def test_version_property_with_status(self) -> None:
        """Test version property returns parsed version from status."""
        data = AdGuardHomeData()
        data.status = AdGuardHomeStatus(
            protection_enabled=True,
            running=True,
            version="0.107.65",
        )

        version = data.version
        assert version.parsed == (0, 107, 65)
        assert version.supports_new_blocked_services is True
        assert version.supports_querylog_response_status is False

    def test_version_property_without_status(self) -> None:
        """Test version property returns empty version when no status."""
        data = AdGuardHomeData()

        version = data.version
        assert version.parsed == (0, 0, 0)
        assert version.supports_stats_config is False

    def test_version_property_with_empty_version(self) -> None:
        """Test version property handles empty version string."""
        data = AdGuardHomeData()
        data.status = AdGuardHomeStatus(
            protection_enabled=True,
            running=True,
            version="",
        )

        version = data.version
        assert version.parsed == (0, 0, 0)


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
        client.get_dns_info = AsyncMock(
            return_value={
                "cache_enabled": True,
                "cache_size": 4194304,
            }
        )
        client.get_blocked_services_with_schedule = AsyncMock(
            return_value={"ids": ["facebook"], "schedule": {}}
        )
        client.get_all_blocked_services = AsyncMock(return_value=[])
        client.get_clients = AsyncMock(return_value=[])
        client.get_dhcp_status = AsyncMock(return_value=MagicMock(enabled=False))
        client.get_rewrites = AsyncMock(return_value=[])
        client.get_query_log = AsyncMock(return_value=[])
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
        assert data.dns_info is not None
        assert data.dns_info.cache_enabled is True

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
        """Test device info property returns DeviceInfo TypedDict."""
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

        # DeviceInfo is a TypedDict, verify required keys are present
        assert "identifiers" in device_info
        assert "name" in device_info
        assert "manufacturer" in device_info
        assert "sw_version" in device_info
        assert "AdGuard Home" in device_info["name"]
        assert device_info["manufacturer"] == "AdGuard"
        assert device_info["sw_version"] == "0.107.43"

    @pytest.mark.asyncio
    async def test_query_log_limit_default(
        self, hass: HomeAssistant, mock_client: AsyncMock, mock_entry: MagicMock
    ) -> None:
        """Test coordinator uses default query log limit when no options set."""
        mock_entry.options = {}
        mock_client.get_query_log = AsyncMock(return_value=[])
        mock_client.get_rewrites = AsyncMock(return_value=[])

        coordinator = AdGuardHomeDataUpdateCoordinator(hass, mock_client, mock_entry)
        await coordinator._async_update_data()

        # Should be called with default limit
        mock_client.get_query_log.assert_called_once_with(limit=DEFAULT_QUERY_LOG_LIMIT)

    @pytest.mark.asyncio
    async def test_query_log_limit_from_options(
        self, hass: HomeAssistant, mock_client: AsyncMock, mock_entry: MagicMock
    ) -> None:
        """Test coordinator uses query log limit from options."""
        mock_entry.options = {CONF_QUERY_LOG_LIMIT: 500}
        mock_client.get_query_log = AsyncMock(return_value=[])
        mock_client.get_rewrites = AsyncMock(return_value=[])

        coordinator = AdGuardHomeDataUpdateCoordinator(hass, mock_client, mock_entry)
        await coordinator._async_update_data()

        # Should be called with custom limit
        mock_client.get_query_log.assert_called_once_with(limit=500)

    @pytest.mark.asyncio
    async def test_dns_info_failure_continues(
        self, hass: HomeAssistant, mock_client: AsyncMock, mock_entry: MagicMock
    ) -> None:
        """Test that DNS info failure doesn't break update."""
        mock_client.get_dns_info = AsyncMock(
            side_effect=AdGuardHomeConnectionError("DNS endpoint unavailable")
        )

        coordinator = AdGuardHomeDataUpdateCoordinator(hass, mock_client, mock_entry)
        data = await coordinator._async_update_data()

        # Should still have status and stats
        assert data.status is not None
        assert data.stats is not None
        # DNS info should be None
        assert data.dns_info is None

    @pytest.mark.asyncio
    async def test_blocked_services_failure_continues(
        self, hass: HomeAssistant, mock_client: AsyncMock, mock_entry: MagicMock
    ) -> None:
        """Test that blocked services failure doesn't break update."""
        mock_client.get_blocked_services_with_schedule = AsyncMock(
            side_effect=AdGuardHomeConnectionError("Services endpoint unavailable")
        )

        coordinator = AdGuardHomeDataUpdateCoordinator(hass, mock_client, mock_entry)
        data = await coordinator._async_update_data()

        # Should still have status and stats
        assert data.status is not None
        assert data.stats is not None
        # Blocked services should be empty default
        assert data.blocked_services == []

    @pytest.mark.asyncio
    async def test_clients_failure_continues(
        self, hass: HomeAssistant, mock_client: AsyncMock, mock_entry: MagicMock
    ) -> None:
        """Test that clients failure doesn't break update."""
        mock_client.get_clients = AsyncMock(
            side_effect=AdGuardHomeConnectionError("Clients endpoint unavailable")
        )

        coordinator = AdGuardHomeDataUpdateCoordinator(hass, mock_client, mock_entry)
        data = await coordinator._async_update_data()

        # Should still have status and stats
        assert data.status is not None
        assert data.stats is not None
        # Clients should be empty default
        assert data.clients == []

    @pytest.mark.asyncio
    async def test_dhcp_failure_continues(
        self, hass: HomeAssistant, mock_client: AsyncMock, mock_entry: MagicMock
    ) -> None:
        """Test that DHCP failure doesn't break update."""
        mock_client.get_dhcp_status = AsyncMock(
            side_effect=AdGuardHomeConnectionError("DHCP endpoint unavailable")
        )

        coordinator = AdGuardHomeDataUpdateCoordinator(hass, mock_client, mock_entry)
        data = await coordinator._async_update_data()

        # Should still have status and stats
        assert data.status is not None
        assert data.stats is not None
        # DHCP should be None
        assert data.dhcp is None

    @pytest.mark.asyncio
    async def test_rewrites_failure_continues(
        self, hass: HomeAssistant, mock_client: AsyncMock, mock_entry: MagicMock
    ) -> None:
        """Test that rewrites failure doesn't break update."""
        mock_client.get_rewrites = AsyncMock(
            side_effect=AdGuardHomeConnectionError("Rewrites endpoint unavailable")
        )

        coordinator = AdGuardHomeDataUpdateCoordinator(hass, mock_client, mock_entry)
        data = await coordinator._async_update_data()

        # Should still have status and stats
        assert data.status is not None
        assert data.stats is not None
        # Rewrites should be empty default
        assert data.rewrites == []

    @pytest.mark.asyncio
    async def test_query_log_failure_continues(
        self, hass: HomeAssistant, mock_client: AsyncMock, mock_entry: MagicMock
    ) -> None:
        """Test that query log failure doesn't break update."""
        mock_client.get_query_log = AsyncMock(
            side_effect=AdGuardHomeConnectionError("Query log endpoint unavailable")
        )

        coordinator = AdGuardHomeDataUpdateCoordinator(hass, mock_client, mock_entry)
        data = await coordinator._async_update_data()

        # Should still have status and stats
        assert data.status is not None
        assert data.stats is not None
        # Query log should be empty default
        assert data.query_log == []

    @pytest.mark.asyncio
    async def test_stats_failure_raises(
        self, hass: HomeAssistant, mock_entry: MagicMock
    ) -> None:
        """Test that stats failure raises UpdateFailed (required endpoint)."""
        mock_client = AsyncMock()
        mock_client.get_status = AsyncMock(
            return_value=AdGuardHomeStatus(
                protection_enabled=True, running=True, version="0.107.43"
            )
        )
        mock_client.get_stats = AsyncMock(
            side_effect=AdGuardHomeConnectionError("Stats endpoint unavailable")
        )

        coordinator = AdGuardHomeDataUpdateCoordinator(hass, mock_client, mock_entry)

        with pytest.raises(UpdateFailed, match="Error communicating with AdGuard Home"):
            await coordinator._async_update_data()

    def test_device_info_unknown_version(
        self, hass: HomeAssistant, mock_entry: MagicMock
    ) -> None:
        """Test device info when version is unknown."""
        mock_client = AsyncMock()

        mock_entry_with_data = MagicMock()
        mock_entry_with_data.entry_id = "test_entry"
        mock_entry_with_data.data = {"host": "192.168.1.1"}
        mock_entry_with_data.options = {}

        coordinator = AdGuardHomeDataUpdateCoordinator(
            hass, mock_client, mock_entry_with_data
        )
        # Set data without status (simulating no data yet)
        coordinator.data = None

        device_info = coordinator.device_info

        assert device_info["sw_version"] == "unknown"

    def test_device_info_status_no_version(
        self, hass: HomeAssistant, mock_entry: MagicMock
    ) -> None:
        """Test device info when status exists but version is None."""
        mock_client = AsyncMock()

        mock_entry_with_data = MagicMock()
        mock_entry_with_data.entry_id = "test_entry"
        mock_entry_with_data.data = {"host": "192.168.1.1"}
        mock_entry_with_data.options = {}

        coordinator = AdGuardHomeDataUpdateCoordinator(
            hass, mock_client, mock_entry_with_data
        )
        coordinator.data = AdGuardHomeData()
        coordinator.data.status = AdGuardHomeStatus(
            protection_enabled=True,
            running=True,
            version=None,  # Version not available
        )

        device_info = coordinator.device_info

        # Should handle None version gracefully
        assert device_info["sw_version"] is None

    @pytest.mark.asyncio
    async def test_async_setup_success(
        self, hass: HomeAssistant, mock_client: AsyncMock, mock_entry: MagicMock
    ) -> None:
        """Test _async_setup fetches version and available services."""
        from custom_components.adguard_home_extended.api.models import BlockedService

        mock_client.get_all_blocked_services = AsyncMock(
            return_value=[
                BlockedService(id="facebook", name="Facebook"),
                BlockedService(id="youtube", name="YouTube"),
            ]
        )

        coordinator = AdGuardHomeDataUpdateCoordinator(hass, mock_client, mock_entry)

        await coordinator._async_setup()

        # Should have cached the version
        assert coordinator._server_version is not None
        assert coordinator._server_version.parsed == (0, 107, 43)

        # Should have cached available services
        assert len(coordinator._available_services) == 2
        assert coordinator._available_services[0]["id"] == "facebook"
        assert coordinator._available_services[1]["name"] == "YouTube"

    @pytest.mark.asyncio
    async def test_async_setup_auth_error(
        self, hass: HomeAssistant, mock_entry: MagicMock
    ) -> None:
        """Test _async_setup raises ConfigEntryAuthFailed on auth error."""
        mock_client = AsyncMock()
        mock_client.get_status = AsyncMock(
            side_effect=AdGuardHomeAuthError("Invalid credentials")
        )

        coordinator = AdGuardHomeDataUpdateCoordinator(hass, mock_client, mock_entry)

        with pytest.raises(ConfigEntryAuthFailed, match="Authentication failed"):
            await coordinator._async_setup()

    @pytest.mark.asyncio
    async def test_async_setup_connection_error(
        self, hass: HomeAssistant, mock_entry: MagicMock
    ) -> None:
        """Test _async_setup raises UpdateFailed on connection error."""
        mock_client = AsyncMock()
        mock_client.get_status = AsyncMock(
            side_effect=AdGuardHomeConnectionError("Cannot connect")
        )

        coordinator = AdGuardHomeDataUpdateCoordinator(hass, mock_client, mock_entry)

        with pytest.raises(UpdateFailed, match="Error during coordinator setup"):
            await coordinator._async_setup()

    @pytest.mark.asyncio
    async def test_update_data_uses_cached_services(
        self, hass: HomeAssistant, mock_client: AsyncMock, mock_entry: MagicMock
    ) -> None:
        """Test _async_update_data uses cached available_services from _async_setup."""
        from custom_components.adguard_home_extended.api.models import BlockedService

        mock_client.get_all_blocked_services = AsyncMock(
            return_value=[
                BlockedService(id="tiktok", name="TikTok"),
            ]
        )

        coordinator = AdGuardHomeDataUpdateCoordinator(hass, mock_client, mock_entry)

        # Run setup to cache services
        await coordinator._async_setup()

        # Reset the mock to track calls during update
        mock_client.get_all_blocked_services.reset_mock()

        # Run update
        data = await coordinator._async_update_data()

        # available_services should come from cache
        assert data.available_services == [{"id": "tiktok", "name": "TikTok"}]

        # Should NOT have called get_all_blocked_services during update
        mock_client.get_all_blocked_services.assert_not_called()

    def test_server_version_when_not_set(
        self, hass: HomeAssistant, mock_client: AsyncMock, mock_entry: MagicMock
    ) -> None:
        """Test server_version property returns empty version when not set."""
        coordinator = AdGuardHomeDataUpdateCoordinator(hass, mock_client, mock_entry)

        # Server version is None before _async_setup
        version = coordinator.server_version
        assert version.parsed == (0, 0, 0)

    @pytest.mark.asyncio
    async def test_stats_config_connection_error(
        self, hass: HomeAssistant, mock_entry: MagicMock
    ) -> None:
        """Test stats config connection error is handled gracefully."""
        mock_client = AsyncMock()
        mock_client.get_status = AsyncMock(
            return_value=AdGuardHomeStatus(
                protection_enabled=True,
                running=True,
                version="0.107.43",  # Supports stats config
            )
        )
        mock_client.get_stats = AsyncMock(
            return_value=AdGuardHomeStats(dns_queries=100, blocked_filtering=10)
        )
        mock_client.get_filtering_status = AsyncMock(return_value=MagicMock())
        mock_client.get_dns_info = AsyncMock(return_value={"cache_enabled": True})
        mock_client.get_blocked_services_with_schedule = AsyncMock(
            return_value={"ids": [], "schedule": {}}
        )
        mock_client.get_all_blocked_services = AsyncMock(return_value=[])
        mock_client.get_clients = AsyncMock(return_value=[])
        mock_client.get_dhcp_status = AsyncMock(return_value=MagicMock(enabled=False))
        mock_client.get_rewrites = AsyncMock(return_value=[])
        mock_client.get_query_log = AsyncMock(return_value=[])
        # Make stats config fail
        mock_client.get_stats_config = AsyncMock(
            side_effect=AdGuardHomeConnectionError("Stats config failed")
        )
        mock_client.get_querylog_config = AsyncMock(return_value=MagicMock())

        coordinator = AdGuardHomeDataUpdateCoordinator(hass, mock_client, mock_entry)

        # Run setup first to set server version
        await coordinator._async_setup()

        # Run update - should not raise despite stats_config error
        data = await coordinator._async_update_data()

        assert data is not None
        assert data.stats_config is None  # Failed to fetch

    @pytest.mark.asyncio
    async def test_querylog_config_connection_error(
        self, hass: HomeAssistant, mock_entry: MagicMock
    ) -> None:
        """Test querylog config connection error is handled gracefully."""
        mock_client = AsyncMock()
        mock_client.get_status = AsyncMock(
            return_value=AdGuardHomeStatus(
                protection_enabled=True,
                running=True,
                version="0.107.43",  # Supports querylog config
            )
        )
        mock_client.get_stats = AsyncMock(
            return_value=AdGuardHomeStats(dns_queries=100, blocked_filtering=10)
        )
        mock_client.get_filtering_status = AsyncMock(return_value=MagicMock())
        mock_client.get_dns_info = AsyncMock(return_value={"cache_enabled": True})
        mock_client.get_blocked_services_with_schedule = AsyncMock(
            return_value={"ids": [], "schedule": {}}
        )
        mock_client.get_all_blocked_services = AsyncMock(return_value=[])
        mock_client.get_clients = AsyncMock(return_value=[])
        mock_client.get_dhcp_status = AsyncMock(return_value=MagicMock(enabled=False))
        mock_client.get_rewrites = AsyncMock(return_value=[])
        mock_client.get_query_log = AsyncMock(return_value=[])
        mock_client.get_stats_config = AsyncMock(return_value=MagicMock())
        # Make querylog config fail
        mock_client.get_querylog_config = AsyncMock(
            side_effect=AdGuardHomeConnectionError("Querylog config failed")
        )

        coordinator = AdGuardHomeDataUpdateCoordinator(hass, mock_client, mock_entry)

        # Run setup first to set server version
        await coordinator._async_setup()

        # Run update - should not raise despite querylog_config error
        data = await coordinator._async_update_data()

        assert data is not None
        assert data.querylog_config is None  # Failed to fetch

    @pytest.mark.asyncio
    async def test_clients_data_transformation(
        self, hass: HomeAssistant, mock_client: AsyncMock, mock_entry: MagicMock
    ) -> None:
        """Test that client data is correctly transformed with all fields."""
        # Create a client with all fields populated (matching actual API response)
        safe_search = SafeSearchSettings(
            enabled=True,
            bing=True,
            duckduckgo=True,
            ecosia=False,
            google=True,
            pixabay=True,
            yandex=False,
            youtube=True,
        )
        test_client = AdGuardHomeClient(
            name="Test Client",
            ids=["10.0.0.1", "aa:bb:cc:dd:ee:ff"],
            use_global_settings=False,
            filtering_enabled=True,
            parental_enabled=True,
            safebrowsing_enabled=True,
            safesearch_enabled=True,
            safe_search=safe_search,
            use_global_blocked_services=False,
            blocked_services=["facebook", "instagram"],
            blocked_services_schedule={
                "time_zone": "UTC",
                "mon": {"start": 0, "end": 86400},
            },
            upstreams=["8.8.8.8", "1.1.1.1"],
            tags=["device_laptop", "user_admin"],
            upstreams_cache_enabled=True,
            upstreams_cache_size=8192,
            ignore_querylog=True,
            ignore_statistics=True,
        )

        mock_client.get_clients = AsyncMock(return_value=[test_client])

        coordinator = AdGuardHomeDataUpdateCoordinator(hass, mock_client, mock_entry)
        data = await coordinator._async_update_data()

        # Verify clients list has one entry
        assert len(data.clients) == 1
        client_data = data.clients[0]

        # Verify all basic fields
        assert client_data["name"] == "Test Client"
        assert client_data["ids"] == ["10.0.0.1", "aa:bb:cc:dd:ee:ff"]
        assert client_data["use_global_settings"] is False
        assert client_data["filtering_enabled"] is True
        assert client_data["parental_enabled"] is True
        assert client_data["safebrowsing_enabled"] is True
        assert client_data["safesearch_enabled"] is True

        # Verify safe_search object is converted to dict
        assert client_data["safe_search"] is not None
        assert client_data["safe_search"]["enabled"] is True
        assert client_data["safe_search"]["google"] is True
        assert client_data["safe_search"]["ecosia"] is False
        assert client_data["safe_search"]["yandex"] is False

        # Verify blocked services fields
        assert client_data["use_global_blocked_services"] is False
        assert client_data["blocked_services"] == ["facebook", "instagram"]
        assert client_data["blocked_services_schedule"] == {
            "time_zone": "UTC",
            "mon": {"start": 0, "end": 86400},
        }

        # Verify custom upstream fields
        assert client_data["upstreams"] == ["8.8.8.8", "1.1.1.1"]
        assert client_data["upstreams_cache_enabled"] is True
        assert client_data["upstreams_cache_size"] == 8192

        # Verify other fields
        assert client_data["tags"] == ["device_laptop", "user_admin"]
        assert client_data["ignore_querylog"] is True
        assert client_data["ignore_statistics"] is True

    @pytest.mark.asyncio
    async def test_clients_data_transformation_minimal(
        self, hass: HomeAssistant, mock_client: AsyncMock, mock_entry: MagicMock
    ) -> None:
        """Test client data transformation with minimal fields (defaults)."""
        # Client with minimal data - safe_search is None
        test_client = AdGuardHomeClient(
            name="Minimal Client",
            ids=["10.0.0.2"],
        )

        mock_client.get_clients = AsyncMock(return_value=[test_client])

        coordinator = AdGuardHomeDataUpdateCoordinator(hass, mock_client, mock_entry)
        data = await coordinator._async_update_data()

        assert len(data.clients) == 1
        client_data = data.clients[0]

        # Verify defaults
        assert client_data["name"] == "Minimal Client"
        assert client_data["ids"] == ["10.0.0.2"]
        assert client_data["use_global_settings"] is True
        assert client_data["filtering_enabled"] is True
        assert client_data["safe_search"] is None  # No safe_search object
        assert client_data["use_global_blocked_services"] is True
        assert client_data["blocked_services"] == []
        assert client_data["blocked_services_schedule"] is None
        assert client_data["upstreams"] == []
        assert client_data["tags"] == []
        assert client_data["upstreams_cache_enabled"] is False
        assert client_data["upstreams_cache_size"] == 0
        assert client_data["ignore_querylog"] is False
        assert client_data["ignore_statistics"] is False
