"""Tests for the AdGuard Home Extended per-client entities."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.adguard_home_extended.client_entities import (
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

        # 2 clients × 6 switches per client = 12 entities
        assert len(entities) == 12

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
