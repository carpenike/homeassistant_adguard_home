"""Tests for the AdGuard Home Extended per-client entities."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.adguard_home_extended.client_entities import (
    AdGuardClientBlockedServiceSwitch,
    AdGuardClientFilteringSwitch,
    AdGuardClientParentalSwitch,
    AdGuardClientUseGlobalSettingsSwitch,
    create_client_entities,
)
from custom_components.adguard_home_extended.coordinator import AdGuardHomeData


class TestCreateClientEntities:
    """Tests for create_client_entities function."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Return a mock coordinator with client data."""
        coordinator = MagicMock()
        coordinator.config_entry = MagicMock()
        coordinator.config_entry.entry_id = "test_entry"
        coordinator.data = AdGuardHomeData()
        coordinator.data.clients = [
            {
                "name": "Kids Tablet",
                "ids": ["192.168.1.100"],
                "use_global_settings": False,
                "filtering_enabled": True,
                "parental_enabled": True,
                "safebrowsing_enabled": True,
                "safesearch_enabled": True,
                "use_global_blocked_services": False,
                "blocked_services": ["tiktok", "youtube"],
                "tags": ["device:tablet"],
            },
            {
                "name": "Office PC",
                "ids": ["192.168.1.101"],
                "use_global_settings": True,
                "filtering_enabled": True,
                "parental_enabled": False,
                "safebrowsing_enabled": False,
                "safesearch_enabled": False,
                "use_global_blocked_services": True,
                "blocked_services": [],
                "tags": [],
            },
        ]
        # Add available services for per-client blocked service switches
        coordinator.data.available_services = [
            {"id": "youtube", "name": "YouTube"},
            {"id": "tiktok", "name": "TikTok"},
            {"id": "facebook", "name": "Facebook"},
        ]
        coordinator.client = AsyncMock()
        coordinator.client.update_client = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()
        return coordinator

    @pytest.fixture
    def mock_coordinator_no_services(self) -> MagicMock:
        """Return a mock coordinator with client data but no available services."""
        coordinator = MagicMock()
        coordinator.config_entry = MagicMock()
        coordinator.config_entry.entry_id = "test_entry"
        coordinator.data = AdGuardHomeData()
        coordinator.data.clients = [
            {
                "name": "Kids Tablet",
                "ids": ["192.168.1.100"],
                "use_global_settings": False,
                "filtering_enabled": True,
                "parental_enabled": True,
                "safebrowsing_enabled": True,
                "safesearch_enabled": True,
                "use_global_blocked_services": False,
                "blocked_services": ["tiktok"],
                "tags": [],
            },
        ]
        coordinator.data.available_services = []
        coordinator.client = AsyncMock()
        coordinator.client.update_client = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()
        return coordinator

    @pytest.mark.asyncio
    async def test_create_entities_for_clients(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test creating entities for all clients."""
        hass = MagicMock()
        entry = MagicMock()

        entities = await create_client_entities(hass, entry, mock_coordinator)

        # 2 clients × (6 base switches + 3 blocked service switches) = 18 entities
        assert len(entities) == 18

    @pytest.mark.asyncio
    async def test_create_entities_no_available_services(
        self, mock_coordinator_no_services: MagicMock
    ) -> None:
        """Test creating entities when no available services exist."""
        hass = MagicMock()
        entry = MagicMock()

        entities = await create_client_entities(
            hass, entry, mock_coordinator_no_services
        )

        # 1 client × 6 base switches = 6 entities (no blocked service switches)
        assert len(entities) == 6

    @pytest.mark.asyncio
    async def test_create_entities_no_clients(self) -> None:
        """Test creating entities with no clients."""
        coordinator = MagicMock()
        coordinator.data = AdGuardHomeData()
        coordinator.data.clients = []

        hass = MagicMock()
        entry = MagicMock()

        entities = await create_client_entities(hass, entry, coordinator)
        assert len(entities) == 0

    @pytest.mark.asyncio
    async def test_create_entities_none_data(self) -> None:
        """Test creating entities with None data."""
        coordinator = MagicMock()
        coordinator.data = None

        hass = MagicMock()
        entry = MagicMock()

        entities = await create_client_entities(hass, entry, coordinator)
        assert len(entities) == 0


class TestClientFilteringSwitch:
    """Tests for AdGuardClientFilteringSwitch."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Return a mock coordinator."""
        coordinator = MagicMock()
        coordinator.config_entry = MagicMock()
        coordinator.config_entry.entry_id = "test_entry"
        coordinator.data = AdGuardHomeData()
        coordinator.data.clients = [
            {
                "name": "Kids Tablet",
                "ids": ["192.168.1.100"],
                "filtering_enabled": True,
                "parental_enabled": True,
                "safebrowsing_enabled": False,
                "safesearch_enabled": False,
                "use_global_settings": False,
                "use_global_blocked_services": True,
                "blocked_services": [],
                "tags": ["device:tablet"],
            },
        ]
        coordinator.client = AsyncMock()
        coordinator.client.update_client = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()
        coordinator.last_update_success = True
        return coordinator

    def test_switch_name(self, mock_coordinator: MagicMock) -> None:
        """Test switch name."""
        switch = AdGuardClientFilteringSwitch(mock_coordinator, "Kids Tablet")
        assert switch.name == "Filtering"

    def test_is_on(self, mock_coordinator: MagicMock) -> None:
        """Test is_on property."""
        switch = AdGuardClientFilteringSwitch(mock_coordinator, "Kids Tablet")
        assert switch.is_on is True

    def test_is_on_client_not_found(self, mock_coordinator: MagicMock) -> None:
        """Test is_on property when client not found returns None."""
        switch = AdGuardClientFilteringSwitch(mock_coordinator, "Nonexistent")
        assert switch.is_on is None

    def test_device_info(self, mock_coordinator: MagicMock) -> None:
        """Test device info for client."""
        switch = AdGuardClientFilteringSwitch(mock_coordinator, "Kids Tablet")
        device_info = switch.device_info

        assert device_info["name"] == "AdGuard Client: Kids Tablet"
        assert device_info["manufacturer"] == "AdGuard"
        assert device_info["model"] == "Client"

    def test_extra_state_attributes(self, mock_coordinator: MagicMock) -> None:
        """Test extra state attributes."""
        switch = AdGuardClientFilteringSwitch(mock_coordinator, "Kids Tablet")
        attrs = switch.extra_state_attributes

        assert attrs["client_name"] == "Kids Tablet"
        assert attrs["client_ids"] == ["192.168.1.100"]
        assert attrs["tags"] == ["device:tablet"]

    @pytest.mark.asyncio
    async def test_turn_on(self, mock_coordinator: MagicMock) -> None:
        """Test turning on filtering."""
        mock_coordinator.data.clients[0]["filtering_enabled"] = False

        switch = AdGuardClientFilteringSwitch(mock_coordinator, "Kids Tablet")
        await switch.async_turn_on()

        mock_coordinator.client.update_client.assert_called_once()
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_turn_off(self, mock_coordinator: MagicMock) -> None:
        """Test turning off filtering."""
        switch = AdGuardClientFilteringSwitch(mock_coordinator, "Kids Tablet")
        await switch.async_turn_off()

        mock_coordinator.client.update_client.assert_called_once()
        mock_coordinator.async_request_refresh.assert_called_once()


class TestClientParentalSwitch:
    """Tests for AdGuardClientParentalSwitch."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Return a mock coordinator."""
        coordinator = MagicMock()
        coordinator.config_entry = MagicMock()
        coordinator.config_entry.entry_id = "test_entry"
        coordinator.data = AdGuardHomeData()
        coordinator.data.clients = [
            {
                "name": "Kids Tablet",
                "ids": ["192.168.1.100"],
                "parental_enabled": True,
                "filtering_enabled": True,
                "safebrowsing_enabled": False,
                "safesearch_enabled": False,
                "use_global_settings": False,
                "use_global_blocked_services": True,
                "blocked_services": [],
                "tags": [],
            },
        ]
        coordinator.client = AsyncMock()
        coordinator.client.update_client = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()
        coordinator.last_update_success = True
        return coordinator

    def test_switch_name(self, mock_coordinator: MagicMock) -> None:
        """Test switch name."""
        switch = AdGuardClientParentalSwitch(mock_coordinator, "Kids Tablet")
        assert switch.name == "Parental Control"

    def test_is_on(self, mock_coordinator: MagicMock) -> None:
        """Test is_on property when parental is enabled."""
        switch = AdGuardClientParentalSwitch(mock_coordinator, "Kids Tablet")
        assert switch.is_on is True

    def test_is_on_client_not_found(self, mock_coordinator: MagicMock) -> None:
        """Test is_on property when client not found returns None."""
        switch = AdGuardClientParentalSwitch(mock_coordinator, "Nonexistent")
        assert switch.is_on is None

    def test_icon(self, mock_coordinator: MagicMock) -> None:
        """Test switch icon."""
        switch = AdGuardClientParentalSwitch(mock_coordinator, "Kids Tablet")
        assert switch._attr_icon == "mdi:account-child"


class TestClientUseGlobalSettingsSwitch:
    """Tests for AdGuardClientUseGlobalSettingsSwitch."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Return a mock coordinator."""
        coordinator = MagicMock()
        coordinator.config_entry = MagicMock()
        coordinator.config_entry.entry_id = "test_entry"
        coordinator.data = AdGuardHomeData()
        coordinator.data.clients = [
            {
                "name": "Office PC",
                "ids": ["192.168.1.101"],
                "use_global_settings": True,
                "filtering_enabled": True,
                "parental_enabled": False,
                "safebrowsing_enabled": False,
                "safesearch_enabled": False,
                "use_global_blocked_services": True,
                "blocked_services": [],
                "tags": [],
            },
        ]
        coordinator.client = AsyncMock()
        coordinator.client.update_client = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()
        coordinator.last_update_success = True
        return coordinator

    def test_switch_name(self, mock_coordinator: MagicMock) -> None:
        """Test switch name."""
        switch = AdGuardClientUseGlobalSettingsSwitch(mock_coordinator, "Office PC")
        assert switch.name == "Use Global Settings"

    def test_is_on_when_using_global(self, mock_coordinator: MagicMock) -> None:
        """Test is_on when using global settings."""
        switch = AdGuardClientUseGlobalSettingsSwitch(mock_coordinator, "Office PC")
        assert switch.is_on is True

    def test_icon(self, mock_coordinator: MagicMock) -> None:
        """Test switch icon."""
        switch = AdGuardClientUseGlobalSettingsSwitch(mock_coordinator, "Office PC")
        assert switch._attr_icon == "mdi:earth"

    @pytest.mark.asyncio
    async def test_turn_off_enables_custom_settings(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test turning off enables custom client settings."""
        switch = AdGuardClientUseGlobalSettingsSwitch(mock_coordinator, "Office PC")
        await switch.async_turn_off()

        # Verify update was called
        mock_coordinator.client.update_client.assert_called_once()
        call_args = mock_coordinator.client.update_client.call_args
        assert call_args[0][0] == "Office PC"  # client name


class TestClientAvailability:
    """Tests for client entity availability."""

    def test_available_when_client_exists(self) -> None:
        """Test entity is available when client exists."""
        coordinator = MagicMock()
        coordinator.config_entry = MagicMock()
        coordinator.config_entry.entry_id = "test_entry"
        coordinator.data = AdGuardHomeData()
        coordinator.data.clients = [
            {"name": "Test Client", "ids": [], "filtering_enabled": True},
        ]
        coordinator.last_update_success = True

        switch = AdGuardClientFilteringSwitch(coordinator, "Test Client")
        assert switch.available is True

    def test_unavailable_when_client_missing(self) -> None:
        """Test entity is unavailable when client is missing."""
        coordinator = MagicMock()
        coordinator.config_entry = MagicMock()
        coordinator.config_entry.entry_id = "test_entry"
        coordinator.data = AdGuardHomeData()
        coordinator.data.clients = []
        coordinator.last_update_success = True

        switch = AdGuardClientFilteringSwitch(coordinator, "Nonexistent Client")
        assert switch.available is False

    def test_unavailable_when_coordinator_fails(self) -> None:
        """Test entity is unavailable when coordinator fails."""
        coordinator = MagicMock()
        coordinator.config_entry = MagicMock()
        coordinator.config_entry.entry_id = "test_entry"
        coordinator.data = AdGuardHomeData()
        coordinator.data.clients = [
            {"name": "Test Client", "ids": [], "filtering_enabled": True},
        ]
        coordinator.last_update_success = False

        switch = AdGuardClientFilteringSwitch(coordinator, "Test Client")
        assert switch.available is False


class TestClientSafeBrowsingSwitch:
    """Tests for AdGuardClientSafeBrowsingSwitch."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Return a mock coordinator."""
        coordinator = MagicMock()
        coordinator.config_entry = MagicMock()
        coordinator.config_entry.entry_id = "test_entry"
        coordinator.data = AdGuardHomeData()
        coordinator.data.clients = [
            {
                "name": "Secure PC",
                "ids": ["192.168.1.102"],
                "safebrowsing_enabled": True,
                "filtering_enabled": True,
                "parental_enabled": False,
                "safesearch_enabled": False,
                "use_global_settings": True,
                "use_global_blocked_services": True,
                "blocked_services": [],
                "tags": [],
            },
        ]
        coordinator.client = AsyncMock()
        coordinator.client.update_client = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()
        coordinator.last_update_success = True
        return coordinator

    def test_switch_name(self, mock_coordinator: MagicMock) -> None:
        """Test switch name."""
        from custom_components.adguard_home_extended.client_entities import (
            AdGuardClientSafeBrowsingSwitch,
        )

        switch = AdGuardClientSafeBrowsingSwitch(mock_coordinator, "Secure PC")
        assert switch.name == "Safe Browsing"

    def test_is_on(self, mock_coordinator: MagicMock) -> None:
        """Test is_on property when safe browsing is enabled."""
        from custom_components.adguard_home_extended.client_entities import (
            AdGuardClientSafeBrowsingSwitch,
        )

        switch = AdGuardClientSafeBrowsingSwitch(mock_coordinator, "Secure PC")
        assert switch.is_on is True

    def test_is_on_when_disabled(self, mock_coordinator: MagicMock) -> None:
        """Test is_on property when safe browsing is disabled."""
        from custom_components.adguard_home_extended.client_entities import (
            AdGuardClientSafeBrowsingSwitch,
        )

        mock_coordinator.data.clients[0]["safebrowsing_enabled"] = False
        switch = AdGuardClientSafeBrowsingSwitch(mock_coordinator, "Secure PC")
        assert switch.is_on is False

    def test_is_on_client_not_found(self, mock_coordinator: MagicMock) -> None:
        """Test is_on property when client not found returns None."""
        from custom_components.adguard_home_extended.client_entities import (
            AdGuardClientSafeBrowsingSwitch,
        )

        switch = AdGuardClientSafeBrowsingSwitch(mock_coordinator, "Nonexistent")
        assert switch.is_on is None

    def test_icon(self, mock_coordinator: MagicMock) -> None:
        """Test switch icon."""
        from custom_components.adguard_home_extended.client_entities import (
            AdGuardClientSafeBrowsingSwitch,
        )

        switch = AdGuardClientSafeBrowsingSwitch(mock_coordinator, "Secure PC")
        assert switch._attr_icon == "mdi:shield-check"

    @pytest.mark.asyncio
    async def test_turn_on(self, mock_coordinator: MagicMock) -> None:
        """Test turning on safe browsing."""
        from custom_components.adguard_home_extended.client_entities import (
            AdGuardClientSafeBrowsingSwitch,
        )

        switch = AdGuardClientSafeBrowsingSwitch(mock_coordinator, "Secure PC")
        await switch.async_turn_on()

        mock_coordinator.client.update_client.assert_called_once()

    @pytest.mark.asyncio
    async def test_turn_off(self, mock_coordinator: MagicMock) -> None:
        """Test turning off safe browsing."""
        from custom_components.adguard_home_extended.client_entities import (
            AdGuardClientSafeBrowsingSwitch,
        )

        switch = AdGuardClientSafeBrowsingSwitch(mock_coordinator, "Secure PC")
        await switch.async_turn_off()

        mock_coordinator.client.update_client.assert_called_once()


class TestClientSafeSearchSwitch:
    """Tests for AdGuardClientSafeSearchSwitch."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Return a mock coordinator."""
        coordinator = MagicMock()
        coordinator.config_entry = MagicMock()
        coordinator.config_entry.entry_id = "test_entry"
        coordinator.data = AdGuardHomeData()
        coordinator.data.clients = [
            {
                "name": "Family PC",
                "ids": ["192.168.1.103"],
                "safesearch_enabled": True,
                "filtering_enabled": True,
                "parental_enabled": False,
                "safebrowsing_enabled": False,
                "use_global_settings": True,
                "use_global_blocked_services": True,
                "blocked_services": [],
                "tags": [],
            },
        ]
        coordinator.client = AsyncMock()
        coordinator.client.update_client = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()
        coordinator.last_update_success = True
        return coordinator

    def test_switch_name(self, mock_coordinator: MagicMock) -> None:
        """Test switch name."""
        from custom_components.adguard_home_extended.client_entities import (
            AdGuardClientSafeSearchSwitch,
        )

        switch = AdGuardClientSafeSearchSwitch(mock_coordinator, "Family PC")
        assert switch.name == "Safe Search"

    def test_is_on(self, mock_coordinator: MagicMock) -> None:
        """Test is_on property when safe search is enabled."""
        from custom_components.adguard_home_extended.client_entities import (
            AdGuardClientSafeSearchSwitch,
        )

        switch = AdGuardClientSafeSearchSwitch(mock_coordinator, "Family PC")
        assert switch.is_on is True

    def test_is_on_when_disabled(self, mock_coordinator: MagicMock) -> None:
        """Test is_on property when safe search is disabled."""
        from custom_components.adguard_home_extended.client_entities import (
            AdGuardClientSafeSearchSwitch,
        )

        mock_coordinator.data.clients[0]["safesearch_enabled"] = False
        switch = AdGuardClientSafeSearchSwitch(mock_coordinator, "Family PC")
        assert switch.is_on is False

    def test_is_on_client_not_found(self, mock_coordinator: MagicMock) -> None:
        """Test is_on property when client not found returns None."""
        from custom_components.adguard_home_extended.client_entities import (
            AdGuardClientSafeSearchSwitch,
        )

        switch = AdGuardClientSafeSearchSwitch(mock_coordinator, "Nonexistent")
        assert switch.is_on is None

    def test_icon(self, mock_coordinator: MagicMock) -> None:
        """Test switch icon."""
        from custom_components.adguard_home_extended.client_entities import (
            AdGuardClientSafeSearchSwitch,
        )

        switch = AdGuardClientSafeSearchSwitch(mock_coordinator, "Family PC")
        assert switch._attr_icon == "mdi:magnify-close"

    @pytest.mark.asyncio
    async def test_turn_on(self, mock_coordinator: MagicMock) -> None:
        """Test turning on safe search."""
        from custom_components.adguard_home_extended.client_entities import (
            AdGuardClientSafeSearchSwitch,
        )

        switch = AdGuardClientSafeSearchSwitch(mock_coordinator, "Family PC")
        await switch.async_turn_on()

        mock_coordinator.client.update_client.assert_called_once()

    @pytest.mark.asyncio
    async def test_turn_off(self, mock_coordinator: MagicMock) -> None:
        """Test turning off safe search."""
        from custom_components.adguard_home_extended.client_entities import (
            AdGuardClientSafeSearchSwitch,
        )

        switch = AdGuardClientSafeSearchSwitch(mock_coordinator, "Family PC")
        await switch.async_turn_off()

        mock_coordinator.client.update_client.assert_called_once()


class TestClientUseGlobalBlockedServicesSwitch:
    """Tests for AdGuardClientUseGlobalBlockedServicesSwitch."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Return a mock coordinator."""
        coordinator = MagicMock()
        coordinator.config_entry = MagicMock()
        coordinator.config_entry.entry_id = "test_entry"
        coordinator.data = AdGuardHomeData()
        coordinator.data.clients = [
            {
                "name": "Gaming PC",
                "ids": ["192.168.1.104"],
                "use_global_blocked_services": True,
                "filtering_enabled": True,
                "parental_enabled": False,
                "safebrowsing_enabled": False,
                "safesearch_enabled": False,
                "use_global_settings": True,
                "blocked_services": [],
                "tags": [],
            },
        ]
        coordinator.client = AsyncMock()
        coordinator.client.update_client = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()
        coordinator.last_update_success = True
        return coordinator

    def test_switch_name(self, mock_coordinator: MagicMock) -> None:
        """Test switch name."""
        from custom_components.adguard_home_extended.client_entities import (
            AdGuardClientUseGlobalBlockedServicesSwitch,
        )

        switch = AdGuardClientUseGlobalBlockedServicesSwitch(
            mock_coordinator, "Gaming PC"
        )
        assert switch.name == "Use Global Blocked Services"

    def test_is_on(self, mock_coordinator: MagicMock) -> None:
        """Test is_on property when using global blocked services."""
        from custom_components.adguard_home_extended.client_entities import (
            AdGuardClientUseGlobalBlockedServicesSwitch,
        )

        switch = AdGuardClientUseGlobalBlockedServicesSwitch(
            mock_coordinator, "Gaming PC"
        )
        assert switch.is_on is True

    def test_is_on_when_disabled(self, mock_coordinator: MagicMock) -> None:
        """Test is_on property when using custom blocked services."""
        from custom_components.adguard_home_extended.client_entities import (
            AdGuardClientUseGlobalBlockedServicesSwitch,
        )

        mock_coordinator.data.clients[0]["use_global_blocked_services"] = False
        switch = AdGuardClientUseGlobalBlockedServicesSwitch(
            mock_coordinator, "Gaming PC"
        )
        assert switch.is_on is False

    def test_is_on_client_not_found(self, mock_coordinator: MagicMock) -> None:
        """Test is_on property when client not found returns None."""
        from custom_components.adguard_home_extended.client_entities import (
            AdGuardClientUseGlobalBlockedServicesSwitch,
        )

        switch = AdGuardClientUseGlobalBlockedServicesSwitch(
            mock_coordinator, "Nonexistent"
        )
        assert switch.is_on is None

    def test_icon(self, mock_coordinator: MagicMock) -> None:
        """Test switch icon."""
        from custom_components.adguard_home_extended.client_entities import (
            AdGuardClientUseGlobalBlockedServicesSwitch,
        )

        switch = AdGuardClientUseGlobalBlockedServicesSwitch(
            mock_coordinator, "Gaming PC"
        )
        assert switch._attr_icon == "mdi:earth-box"

    @pytest.mark.asyncio
    async def test_turn_on(self, mock_coordinator: MagicMock) -> None:
        """Test turning on global blocked services."""
        from custom_components.adguard_home_extended.client_entities import (
            AdGuardClientUseGlobalBlockedServicesSwitch,
        )

        switch = AdGuardClientUseGlobalBlockedServicesSwitch(
            mock_coordinator, "Gaming PC"
        )
        await switch.async_turn_on()

        mock_coordinator.client.update_client.assert_called_once()

    @pytest.mark.asyncio
    async def test_turn_off(self, mock_coordinator: MagicMock) -> None:
        """Test turning off global blocked services."""
        from custom_components.adguard_home_extended.client_entities import (
            AdGuardClientUseGlobalBlockedServicesSwitch,
        )

        switch = AdGuardClientUseGlobalBlockedServicesSwitch(
            mock_coordinator, "Gaming PC"
        )
        await switch.async_turn_off()

        mock_coordinator.client.update_client.assert_called_once()


class TestClientBaseSwitchEdgeCases:
    """Tests for edge cases in AdGuardClientBaseSwitch."""

    def test_get_client_data_returns_none_when_data_is_none(self) -> None:
        """Test _get_client_data returns None when coordinator.data is None."""
        coordinator = MagicMock()
        coordinator.config_entry = MagicMock()
        coordinator.config_entry.entry_id = "test_entry"
        coordinator.data = None
        coordinator.last_update_success = True

        switch = AdGuardClientFilteringSwitch(coordinator, "Test Client")
        assert switch._get_client_data() is None

    def test_extra_state_attributes_returns_empty_when_client_not_found(self) -> None:
        """Test extra_state_attributes returns empty dict when client not found."""
        coordinator = MagicMock()
        coordinator.config_entry = MagicMock()
        coordinator.config_entry.entry_id = "test_entry"
        coordinator.data = AdGuardHomeData()
        coordinator.data.clients = []
        coordinator.last_update_success = True

        switch = AdGuardClientFilteringSwitch(coordinator, "Nonexistent")
        assert switch.extra_state_attributes == {}

    @pytest.mark.asyncio
    async def test_async_update_client_does_nothing_when_client_not_found(self) -> None:
        """Test _async_update_client returns early when client not found."""
        coordinator = MagicMock()
        coordinator.config_entry = MagicMock()
        coordinator.config_entry.entry_id = "test_entry"
        coordinator.data = AdGuardHomeData()
        coordinator.data.clients = []
        coordinator.client = AsyncMock()
        coordinator.client.update_client = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()
        coordinator.last_update_success = True

        switch = AdGuardClientFilteringSwitch(coordinator, "Nonexistent")
        await switch.async_turn_on()

        # update_client should not be called since client doesn't exist
        coordinator.client.update_client.assert_not_called()


class TestClientUseGlobalSettingsSwitchAdditional:
    """Additional tests for AdGuardClientUseGlobalSettingsSwitch."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Return a mock coordinator."""
        coordinator = MagicMock()
        coordinator.config_entry = MagicMock()
        coordinator.config_entry.entry_id = "test_entry"
        coordinator.data = AdGuardHomeData()
        coordinator.data.clients = [
            {
                "name": "Server",
                "ids": ["192.168.1.200"],
                "use_global_settings": False,
                "filtering_enabled": True,
                "parental_enabled": False,
                "safebrowsing_enabled": False,
                "safesearch_enabled": False,
                "use_global_blocked_services": True,
                "blocked_services": [],
                "tags": [],
            },
        ]
        coordinator.client = AsyncMock()
        coordinator.client.update_client = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()
        coordinator.last_update_success = True
        return coordinator

    @pytest.mark.asyncio
    async def test_turn_on_enables_global_settings(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test turning on enables global settings."""
        from custom_components.adguard_home_extended.client_entities import (
            AdGuardClientUseGlobalSettingsSwitch,
        )

        switch = AdGuardClientUseGlobalSettingsSwitch(mock_coordinator, "Server")
        await switch.async_turn_on()

        mock_coordinator.client.update_client.assert_called_once()

    def test_is_on_when_not_using_global(self, mock_coordinator: MagicMock) -> None:
        """Test is_on when not using global settings."""
        from custom_components.adguard_home_extended.client_entities import (
            AdGuardClientUseGlobalSettingsSwitch,
        )

        switch = AdGuardClientUseGlobalSettingsSwitch(mock_coordinator, "Server")
        assert switch.is_on is False

    def test_is_on_client_not_found(self, mock_coordinator: MagicMock) -> None:
        """Test is_on property when client not found returns None."""
        from custom_components.adguard_home_extended.client_entities import (
            AdGuardClientUseGlobalSettingsSwitch,
        )

        switch = AdGuardClientUseGlobalSettingsSwitch(mock_coordinator, "Nonexistent")
        assert switch.is_on is None


class TestClientParentalSwitchAdditional:
    """Additional tests for AdGuardClientParentalSwitch."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Return a mock coordinator."""
        coordinator = MagicMock()
        coordinator.config_entry = MagicMock()
        coordinator.config_entry.entry_id = "test_entry"
        coordinator.data = AdGuardHomeData()
        coordinator.data.clients = [
            {
                "name": "Kids Tablet",
                "ids": ["192.168.1.105"],
                "parental_enabled": True,
                "filtering_enabled": True,
                "safebrowsing_enabled": False,
                "safesearch_enabled": False,
                "use_global_settings": True,
                "use_global_blocked_services": True,
                "blocked_services": [],
                "tags": [],
            },
        ]
        coordinator.client = AsyncMock()
        coordinator.client.update_client = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()
        coordinator.last_update_success = True
        return coordinator

    @pytest.mark.asyncio
    async def test_turn_on(self, mock_coordinator: MagicMock) -> None:
        """Test turning on parental control."""
        switch = AdGuardClientParentalSwitch(mock_coordinator, "Kids Tablet")
        await switch.async_turn_on()

        mock_coordinator.client.update_client.assert_called_once()

    @pytest.mark.asyncio
    async def test_turn_off(self, mock_coordinator: MagicMock) -> None:
        """Test turning off parental control."""
        switch = AdGuardClientParentalSwitch(mock_coordinator, "Kids Tablet")
        await switch.async_turn_off()

        mock_coordinator.client.update_client.assert_called_once()


class TestClientEntityManager:
    """Tests for ClientEntityManager."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Return a mock coordinator."""
        coordinator = MagicMock()
        coordinator.config_entry = MagicMock()
        coordinator.config_entry.entry_id = "test_entry"
        coordinator.data = AdGuardHomeData()
        coordinator.data.clients = [
            {
                "name": "Client1",
                "ids": ["192.168.1.100"],
                "filtering_enabled": True,
                "parental_enabled": False,
                "safebrowsing_enabled": False,
                "safesearch_enabled": False,
                "use_global_settings": True,
                "use_global_blocked_services": True,
                "blocked_services": [],
                "tags": [],
            },
        ]
        coordinator.hass = MagicMock()
        coordinator.async_add_listener = MagicMock(return_value=MagicMock())
        return coordinator

    @pytest.mark.asyncio
    async def test_initial_setup_creates_entities(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test that initial setup creates entities for existing clients."""
        from custom_components.adguard_home_extended.switch import ClientEntityManager

        async_add_entities = MagicMock()

        manager = ClientEntityManager(mock_coordinator, async_add_entities)
        await manager.async_setup()

        # Should have created 6 entities for 1 client
        assert async_add_entities.call_count == 1
        entities = async_add_entities.call_args[0][0]
        assert len(entities) == 6
        assert manager._tracked_clients == {"Client1"}

    @pytest.mark.asyncio
    async def test_new_client_adds_entities(self, mock_coordinator: MagicMock) -> None:
        """Test that new clients get entities added."""
        from custom_components.adguard_home_extended.switch import ClientEntityManager

        async_add_entities = MagicMock()

        manager = ClientEntityManager(mock_coordinator, async_add_entities)
        await manager.async_setup()

        # Reset the mock
        async_add_entities.reset_mock()

        # Add a new client
        mock_coordinator.data.clients.append(
            {
                "name": "Client2",
                "ids": ["192.168.1.101"],
                "filtering_enabled": True,
                "parental_enabled": False,
                "safebrowsing_enabled": False,
                "safesearch_enabled": False,
                "use_global_settings": True,
                "use_global_blocked_services": True,
                "blocked_services": [],
                "tags": [],
            }
        )

        # Manually trigger the check (normally called by listener)
        await manager._async_add_new_client_entities()

        # Should have added 6 entities for the new client
        assert async_add_entities.call_count == 1
        entities = async_add_entities.call_args[0][0]
        assert len(entities) == 6
        assert manager._tracked_clients == {"Client1", "Client2"}

    @pytest.mark.asyncio
    async def test_existing_client_not_duplicated(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test that existing clients don't get duplicate entities."""
        from custom_components.adguard_home_extended.switch import ClientEntityManager

        async_add_entities = MagicMock()

        manager = ClientEntityManager(mock_coordinator, async_add_entities)
        await manager.async_setup()

        # Reset the mock
        async_add_entities.reset_mock()

        # Trigger another check without changes
        await manager._async_add_new_client_entities()

        # Should not have added any entities
        assert async_add_entities.call_count == 0

    @pytest.mark.asyncio
    async def test_no_clients_no_entities(self) -> None:
        """Test that no clients results in no entities."""
        from custom_components.adguard_home_extended.switch import ClientEntityManager

        coordinator = MagicMock()
        coordinator.data = AdGuardHomeData()
        coordinator.data.clients = []
        coordinator.async_add_listener = MagicMock(return_value=MagicMock())

        async_add_entities = MagicMock()

        manager = ClientEntityManager(coordinator, async_add_entities)
        await manager.async_setup()

        # Should not have called async_add_entities
        assert async_add_entities.call_count == 0

    def test_unsubscribe(self, mock_coordinator: MagicMock) -> None:
        """Test that unsubscribe removes the listener."""
        from custom_components.adguard_home_extended.switch import ClientEntityManager

        unsubscribe_mock = MagicMock()
        mock_coordinator.async_add_listener = MagicMock(return_value=unsubscribe_mock)

        async_add_entities = MagicMock()

        manager = ClientEntityManager(mock_coordinator, async_add_entities)
        manager._unsubscribe = unsubscribe_mock

        manager.async_unsubscribe()

        unsubscribe_mock.assert_called_once()
        assert manager._unsubscribe is None


class TestClientBlockedServiceSwitch:
    """Tests for AdGuardClientBlockedServiceSwitch."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Return a mock coordinator with client using per-client blocked services."""
        coordinator = MagicMock()
        coordinator.config_entry = MagicMock()
        coordinator.config_entry.entry_id = "test_entry"
        coordinator.data = AdGuardHomeData()
        coordinator.data.clients = [
            {
                "name": "Kids Tablet",
                "ids": ["192.168.1.100"],
                "filtering_enabled": True,
                "parental_enabled": False,
                "safebrowsing_enabled": False,
                "safesearch_enabled": False,
                "use_global_settings": False,
                "use_global_blocked_services": False,
                "blocked_services": ["youtube", "tiktok"],
                "tags": ["device:tablet"],
            },
        ]
        coordinator.data.available_services = [
            {"id": "youtube", "name": "YouTube"},
            {"id": "tiktok", "name": "TikTok"},
            {"id": "facebook", "name": "Facebook"},
        ]
        coordinator.client = AsyncMock()
        coordinator.client.update_client = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()
        coordinator.last_update_success = True
        return coordinator

    @pytest.fixture
    def mock_coordinator_global_services(self) -> MagicMock:
        """Return a mock coordinator with client using global blocked services."""
        coordinator = MagicMock()
        coordinator.config_entry = MagicMock()
        coordinator.config_entry.entry_id = "test_entry"
        coordinator.data = AdGuardHomeData()
        coordinator.data.clients = [
            {
                "name": "Office PC",
                "ids": ["192.168.1.101"],
                "filtering_enabled": True,
                "parental_enabled": False,
                "safebrowsing_enabled": False,
                "safesearch_enabled": False,
                "use_global_settings": True,
                "use_global_blocked_services": True,
                "blocked_services": [],
                "tags": [],
            },
        ]
        coordinator.data.available_services = [
            {"id": "youtube", "name": "YouTube"},
        ]
        coordinator.client = AsyncMock()
        coordinator.client.update_client = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()
        coordinator.last_update_success = True
        return coordinator

    def test_switch_name(self, mock_coordinator: MagicMock) -> None:
        """Test switch name includes service name."""
        switch = AdGuardClientBlockedServiceSwitch(
            mock_coordinator, "Kids Tablet", "youtube", "YouTube"
        )
        assert switch.name == "Block YouTube"

    def test_unique_id(self, mock_coordinator: MagicMock) -> None:
        """Test unique ID includes client and service."""
        switch = AdGuardClientBlockedServiceSwitch(
            mock_coordinator, "Kids Tablet", "youtube", "YouTube"
        )
        assert "Kids Tablet" in switch.unique_id
        assert "block_youtube" in switch.unique_id

    def test_is_on_when_service_blocked(self, mock_coordinator: MagicMock) -> None:
        """Test is_on returns True when service is in blocked list."""
        switch = AdGuardClientBlockedServiceSwitch(
            mock_coordinator, "Kids Tablet", "youtube", "YouTube"
        )
        assert switch.is_on is True

    def test_is_on_when_service_not_blocked(self, mock_coordinator: MagicMock) -> None:
        """Test is_on returns False when service is not in blocked list."""
        switch = AdGuardClientBlockedServiceSwitch(
            mock_coordinator, "Kids Tablet", "facebook", "Facebook"
        )
        assert switch.is_on is False

    def test_is_on_client_not_found(self, mock_coordinator: MagicMock) -> None:
        """Test is_on returns None when client not found."""
        switch = AdGuardClientBlockedServiceSwitch(
            mock_coordinator, "Nonexistent", "youtube", "YouTube"
        )
        assert switch.is_on is None

    def test_available_when_per_client_services(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test switch is available when client uses per-client blocked services."""
        switch = AdGuardClientBlockedServiceSwitch(
            mock_coordinator, "Kids Tablet", "youtube", "YouTube"
        )
        assert switch.available is True

    def test_unavailable_when_global_services(
        self, mock_coordinator_global_services: MagicMock
    ) -> None:
        """Test switch is unavailable when client uses global blocked services."""
        switch = AdGuardClientBlockedServiceSwitch(
            mock_coordinator_global_services, "Office PC", "youtube", "YouTube"
        )
        assert switch.available is False

    def test_unavailable_when_coordinator_fails(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test switch is unavailable when coordinator update fails."""
        mock_coordinator.last_update_success = False
        switch = AdGuardClientBlockedServiceSwitch(
            mock_coordinator, "Kids Tablet", "youtube", "YouTube"
        )
        assert switch.available is False

    def test_unavailable_when_client_not_found(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test switch is unavailable when client doesn't exist."""
        switch = AdGuardClientBlockedServiceSwitch(
            mock_coordinator, "Nonexistent", "youtube", "YouTube"
        )
        assert switch.available is False

    def test_icon_for_known_category(self, mock_coordinator: MagicMock) -> None:
        """Test icon is set based on service category."""
        switch = AdGuardClientBlockedServiceSwitch(
            mock_coordinator, "Kids Tablet", "youtube", "YouTube"
        )
        # YouTube is in video_streaming category
        assert switch.icon == "mdi:video"

    def test_icon_for_unknown_service(self, mock_coordinator: MagicMock) -> None:
        """Test icon defaults to block-helper for unknown services."""
        switch = AdGuardClientBlockedServiceSwitch(
            mock_coordinator, "Kids Tablet", "unknown_service", "Unknown"
        )
        assert switch.icon == "mdi:block-helper"

    def test_extra_state_attributes(self, mock_coordinator: MagicMock) -> None:
        """Test extra state attributes include service info."""
        switch = AdGuardClientBlockedServiceSwitch(
            mock_coordinator, "Kids Tablet", "youtube", "YouTube"
        )
        attrs = switch.extra_state_attributes

        assert attrs["service_id"] == "youtube"
        assert attrs["service_name"] == "YouTube"
        assert attrs["category"] == "Video Streaming"
        assert attrs["uses_global_blocked_services"] is False
        assert attrs["client_name"] == "Kids Tablet"

    def test_extra_state_attributes_global_services(
        self, mock_coordinator_global_services: MagicMock
    ) -> None:
        """Test extra state attributes when using global services."""
        switch = AdGuardClientBlockedServiceSwitch(
            mock_coordinator_global_services, "Office PC", "youtube", "YouTube"
        )
        attrs = switch.extra_state_attributes

        assert attrs["uses_global_blocked_services"] is True

    def test_device_info(self, mock_coordinator: MagicMock) -> None:
        """Test device info links to client device."""
        switch = AdGuardClientBlockedServiceSwitch(
            mock_coordinator, "Kids Tablet", "youtube", "YouTube"
        )
        device_info = switch.device_info

        assert device_info["name"] == "AdGuard Client: Kids Tablet"
        assert device_info["manufacturer"] == "AdGuard"
        assert device_info["model"] == "Client"

    @pytest.mark.asyncio
    async def test_turn_on_blocks_service(self, mock_coordinator: MagicMock) -> None:
        """Test turning on adds service to blocked list."""
        switch = AdGuardClientBlockedServiceSwitch(
            mock_coordinator, "Kids Tablet", "facebook", "Facebook"
        )
        await switch.async_turn_on()

        mock_coordinator.client.update_client.assert_called_once()
        call_args = mock_coordinator.client.update_client.call_args
        updated_client = call_args[0][1]

        # Should have facebook added to blocked services
        assert "facebook" in updated_client.blocked_services
        # Should also still have the existing blocked services
        assert "youtube" in updated_client.blocked_services
        assert "tiktok" in updated_client.blocked_services
        # Should disable global blocked services
        assert updated_client.use_global_blocked_services is False

        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_turn_off_unblocks_service(self, mock_coordinator: MagicMock) -> None:
        """Test turning off removes service from blocked list."""
        switch = AdGuardClientBlockedServiceSwitch(
            mock_coordinator, "Kids Tablet", "youtube", "YouTube"
        )
        await switch.async_turn_off()

        mock_coordinator.client.update_client.assert_called_once()
        call_args = mock_coordinator.client.update_client.call_args
        updated_client = call_args[0][1]

        # Should have youtube removed from blocked services
        assert "youtube" not in updated_client.blocked_services
        # Should still have tiktok blocked
        assert "tiktok" in updated_client.blocked_services
        # Should keep using per-client blocked services
        assert updated_client.use_global_blocked_services is False

        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_turn_on_does_nothing_when_client_not_found(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test turning on does nothing when client doesn't exist."""
        switch = AdGuardClientBlockedServiceSwitch(
            mock_coordinator, "Nonexistent", "youtube", "YouTube"
        )
        await switch.async_turn_on()

        mock_coordinator.client.update_client.assert_not_called()

    @pytest.mark.asyncio
    async def test_turn_off_does_nothing_when_client_not_found(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test turning off does nothing when client doesn't exist."""
        switch = AdGuardClientBlockedServiceSwitch(
            mock_coordinator, "Nonexistent", "youtube", "YouTube"
        )
        await switch.async_turn_off()

        mock_coordinator.client.update_client.assert_not_called()

    def test_entity_category_is_config(self, mock_coordinator: MagicMock) -> None:
        """Test entity category is CONFIG for organization."""
        from homeassistant.const import EntityCategory

        switch = AdGuardClientBlockedServiceSwitch(
            mock_coordinator, "Kids Tablet", "youtube", "YouTube"
        )
        assert switch.entity_category == EntityCategory.CONFIG

    def test_icon_for_social_media_service(self, mock_coordinator: MagicMock) -> None:
        """Test icon for social media category."""
        switch = AdGuardClientBlockedServiceSwitch(
            mock_coordinator, "Kids Tablet", "facebook", "Facebook"
        )
        assert switch.icon == "mdi:account-group"

    def test_icon_for_tiktok(self, mock_coordinator: MagicMock) -> None:
        """Test icon for TikTok (social media)."""
        switch = AdGuardClientBlockedServiceSwitch(
            mock_coordinator, "Kids Tablet", "tiktok", "TikTok"
        )
        assert switch.icon == "mdi:account-group"
