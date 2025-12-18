"""Tests for filter list switches."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.adguard_home_extended.api.models import FilteringStatus
from custom_components.adguard_home_extended.coordinator import AdGuardHomeData
from custom_components.adguard_home_extended.filter_lists import (
    FilterListSwitch,
    _get_filter_unique_id,
)


class TestFilterUniqueId:
    """Tests for filter unique ID generation."""

    def test_unique_id_consistency(self) -> None:
        """Test that same URL produces same unique ID."""
        url = "https://example.com/filters.txt"
        id1 = _get_filter_unique_id(url)
        id2 = _get_filter_unique_id(url)
        assert id1 == id2

    def test_unique_id_different_urls(self) -> None:
        """Test that different URLs produce different IDs."""
        id1 = _get_filter_unique_id("https://example.com/filter1.txt")
        id2 = _get_filter_unique_id("https://example.com/filter2.txt")
        assert id1 != id2

    def test_unique_id_whitelist_prefix(self) -> None:
        """Test that whitelist filters have different prefix."""
        url = "https://example.com/filters.txt"
        blocklist_id = _get_filter_unique_id(url, whitelist=False)
        whitelist_id = _get_filter_unique_id(url, whitelist=True)
        assert blocklist_id.startswith("filter_")
        assert whitelist_id.startswith("whitelist_")
        assert blocklist_id != whitelist_id


class TestFilterListSwitch:
    """Tests for FilterListSwitch entity."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Return a mock coordinator."""
        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_id"
        coordinator.device_info = {"identifiers": {("test", "test")}}
        coordinator.last_update_success = True
        coordinator.client = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()
        return coordinator

    @pytest.fixture
    def filter_data(self) -> dict:
        """Return sample filter data."""
        return {
            "url": "https://example.com/adblock.txt",
            "name": "Example Adblock",
            "enabled": True,
            "rules_count": 50000,
            "last_updated": "2025-01-01T00:00:00Z",
            "id": 1,
        }

    @pytest.fixture
    def data_with_filters(self, filter_data: dict) -> AdGuardHomeData:
        """Return coordinator data with filters."""
        data = AdGuardHomeData()
        data.filtering = FilteringStatus(
            enabled=True,
            filters=[filter_data],
            whitelist_filters=[
                {
                    "url": "https://example.com/whitelist.txt",
                    "name": "Whitelist",
                    "enabled": True,
                    "rules_count": 100,
                    "last_updated": "2025-01-01T00:00:00Z",
                    "id": 2,
                }
            ],
        )
        return data

    def test_switch_name_blocklist(
        self, mock_coordinator: MagicMock, filter_data: dict
    ) -> None:
        """Test switch name for blocklist filters."""
        switch = FilterListSwitch(mock_coordinator, filter_data, whitelist=False)
        assert switch.name == "Filter: Example Adblock"

    def test_switch_name_whitelist(self, mock_coordinator: MagicMock) -> None:
        """Test switch name for whitelist filters."""
        filter_data = {
            "url": "https://example.com/whitelist.txt",
            "name": "My Whitelist",
        }
        switch = FilterListSwitch(mock_coordinator, filter_data, whitelist=True)
        assert switch.name == "Whitelist: My Whitelist"

    def test_switch_icon_blocklist(
        self, mock_coordinator: MagicMock, filter_data: dict
    ) -> None:
        """Test switch icon for blocklist filters."""
        switch = FilterListSwitch(mock_coordinator, filter_data, whitelist=False)
        assert switch.icon == "mdi:filter-outline"

    def test_switch_icon_whitelist(
        self, mock_coordinator: MagicMock, filter_data: dict
    ) -> None:
        """Test switch icon for whitelist filters."""
        switch = FilterListSwitch(mock_coordinator, filter_data, whitelist=True)
        assert switch.icon == "mdi:format-list-checks"

    def test_switch_is_on_when_enabled(
        self,
        mock_coordinator: MagicMock,
        filter_data: dict,
        data_with_filters: AdGuardHomeData,
    ) -> None:
        """Test switch is_on returns True when filter is enabled."""
        mock_coordinator.data = data_with_filters
        switch = FilterListSwitch(mock_coordinator, filter_data, whitelist=False)
        assert switch.is_on is True

    def test_switch_is_off_when_disabled(
        self,
        mock_coordinator: MagicMock,
        data_with_filters: AdGuardHomeData,
    ) -> None:
        """Test switch is_on returns False when filter is disabled."""
        data_with_filters.filtering.filters[0]["enabled"] = False
        mock_coordinator.data = data_with_filters
        filter_data = data_with_filters.filtering.filters[0]
        switch = FilterListSwitch(mock_coordinator, filter_data, whitelist=False)
        assert switch.is_on is False

    def test_switch_is_on_none_when_not_found(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test switch is_on returns None when filter not found."""
        data = AdGuardHomeData()
        data.filtering = FilteringStatus(enabled=True, filters=[])
        mock_coordinator.data = data

        filter_data = {"url": "https://nonexistent.com/filter.txt", "name": "Missing"}
        switch = FilterListSwitch(mock_coordinator, filter_data, whitelist=False)
        assert switch.is_on is None

    def test_switch_available(
        self,
        mock_coordinator: MagicMock,
        filter_data: dict,
        data_with_filters: AdGuardHomeData,
    ) -> None:
        """Test switch is available when filter exists."""
        mock_coordinator.data = data_with_filters
        switch = FilterListSwitch(mock_coordinator, filter_data, whitelist=False)
        assert switch.available is True

    def test_switch_unavailable_when_missing(
        self,
        mock_coordinator: MagicMock,
    ) -> None:
        """Test switch is unavailable when filter doesn't exist."""
        data = AdGuardHomeData()
        data.filtering = FilteringStatus(enabled=True, filters=[])
        mock_coordinator.data = data

        filter_data = {"url": "https://nonexistent.com/filter.txt", "name": "Missing"}
        switch = FilterListSwitch(mock_coordinator, filter_data, whitelist=False)
        assert switch.available is False

    def test_extra_state_attributes(
        self,
        mock_coordinator: MagicMock,
        filter_data: dict,
        data_with_filters: AdGuardHomeData,
    ) -> None:
        """Test extra state attributes."""
        mock_coordinator.data = data_with_filters
        switch = FilterListSwitch(mock_coordinator, filter_data, whitelist=False)
        attrs = switch.extra_state_attributes

        assert attrs["url"] == "https://example.com/adblock.txt"
        assert attrs["name"] == "Example Adblock"
        assert attrs["rules_count"] == 50000
        assert attrs["whitelist"] is False
        assert attrs["filter_id"] == 1

    @pytest.mark.asyncio
    async def test_turn_on(
        self,
        mock_coordinator: MagicMock,
        filter_data: dict,
        data_with_filters: AdGuardHomeData,
    ) -> None:
        """Test turning on a filter."""
        mock_coordinator.data = data_with_filters
        switch = FilterListSwitch(mock_coordinator, filter_data, whitelist=False)

        await switch.async_turn_on()

        mock_coordinator.client.set_filter_enabled.assert_called_once_with(
            url="https://example.com/adblock.txt",
            enabled=True,
            whitelist=False,
        )
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_turn_off(
        self,
        mock_coordinator: MagicMock,
        filter_data: dict,
        data_with_filters: AdGuardHomeData,
    ) -> None:
        """Test turning off a filter."""
        mock_coordinator.data = data_with_filters
        switch = FilterListSwitch(mock_coordinator, filter_data, whitelist=False)

        await switch.async_turn_off()

        mock_coordinator.client.set_filter_enabled.assert_called_once_with(
            url="https://example.com/adblock.txt",
            enabled=False,
            whitelist=False,
        )
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_turn_on_whitelist(
        self,
        mock_coordinator: MagicMock,
        data_with_filters: AdGuardHomeData,
    ) -> None:
        """Test turning on a whitelist filter."""
        mock_coordinator.data = data_with_filters
        filter_data = data_with_filters.filtering.whitelist_filters[0]
        switch = FilterListSwitch(mock_coordinator, filter_data, whitelist=True)

        await switch.async_turn_on()

        mock_coordinator.client.set_filter_enabled.assert_called_once_with(
            url="https://example.com/whitelist.txt",
            enabled=True,
            whitelist=True,
        )


class TestSetFilterEnabledApi:
    """Tests for set_filter_enabled API method."""

    @pytest.mark.asyncio
    async def test_set_filter_enabled(self) -> None:
        """Test enabling a filter via API."""
        from unittest.mock import AsyncMock, MagicMock, patch

        from custom_components.adguard_home_extended.api.client import AdGuardHomeClient

        with patch.object(
            AdGuardHomeClient, "_post", new_callable=AsyncMock
        ) as mock_post:
            client = AdGuardHomeClient(
                host="192.168.1.1",
                port=3000,
                session=MagicMock(),
            )

            await client.set_filter_enabled(
                url="https://example.com/filter.txt",
                enabled=True,
                whitelist=False,
            )

            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "/control/filtering/set_url" in call_args[0][0]
            assert call_args[0][1]["url"] == "https://example.com/filter.txt"
            assert call_args[0][1]["data"]["enabled"] is True
            assert call_args[0][1]["whitelist"] is False

    @pytest.mark.asyncio
    async def test_set_whitelist_filter_disabled(self) -> None:
        """Test disabling a whitelist filter via API."""
        from unittest.mock import AsyncMock, MagicMock, patch

        from custom_components.adguard_home_extended.api.client import AdGuardHomeClient

        with patch.object(
            AdGuardHomeClient, "_post", new_callable=AsyncMock
        ) as mock_post:
            client = AdGuardHomeClient(
                host="192.168.1.1",
                port=3000,
                session=MagicMock(),
            )

            await client.set_filter_enabled(
                url="https://example.com/whitelist.txt",
                enabled=False,
                whitelist=True,
            )

            call_args = mock_post.call_args
            assert call_args[0][1]["data"]["enabled"] is False
            assert call_args[0][1]["whitelist"] is True


class TestFilterListEntityManager:
    """Tests for FilterListEntityManager."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Return a mock coordinator."""
        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_id"
        coordinator.device_info = {"identifiers": {("test", "test")}}
        coordinator.last_update_success = True
        coordinator.hass = MagicMock()
        coordinator.hass.async_create_task = MagicMock()
        coordinator.data = AdGuardHomeData()
        coordinator.data.filtering = None
        coordinator.async_add_listener = MagicMock(return_value=lambda: None)
        return coordinator

    @pytest.mark.asyncio
    async def test_manager_setup_no_filtering_data(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test manager setup with no filtering data."""
        from custom_components.adguard_home_extended.filter_lists import (
            FilterListEntityManager,
        )

        added_entities = []
        mock_add_entities = MagicMock(side_effect=lambda e: added_entities.extend(e))

        manager = FilterListEntityManager(mock_coordinator, mock_add_entities)
        await manager.async_setup()

        assert len(added_entities) == 0
        mock_coordinator.async_add_listener.assert_called_once()

    @pytest.mark.asyncio
    async def test_manager_setup_with_filters(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test manager setup with existing filters."""
        from custom_components.adguard_home_extended.filter_lists import (
            FilterListEntityManager,
        )

        mock_coordinator.data.filtering = FilteringStatus(
            enabled=True,
            filters=[
                {"url": "https://example.com/filter1.txt", "name": "Filter 1"},
                {"url": "https://example.com/filter2.txt", "name": "Filter 2"},
            ],
            whitelist_filters=[
                {"url": "https://example.com/whitelist.txt", "name": "Whitelist"},
            ],
        )

        added_entities = []
        mock_add_entities = MagicMock(side_effect=lambda e: added_entities.extend(e))

        manager = FilterListEntityManager(mock_coordinator, mock_add_entities)
        await manager.async_setup()

        # Should add 2 blocklist + 1 whitelist = 3 entities
        assert len(added_entities) == 3

    @pytest.mark.asyncio
    async def test_manager_handles_new_filters(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test manager adds entities for new filters."""
        from custom_components.adguard_home_extended.filter_lists import (
            FilterListEntityManager,
        )

        added_entities = []
        mock_add_entities = MagicMock(side_effect=lambda e: added_entities.extend(e))

        manager = FilterListEntityManager(mock_coordinator, mock_add_entities)
        await manager.async_setup()

        # Initially no filters
        assert len(added_entities) == 0

        # Add filters
        mock_coordinator.data.filtering = FilteringStatus(
            enabled=True,
            filters=[{"url": "https://example.com/new.txt", "name": "New"}],
            whitelist_filters=[],
        )

        await manager._async_add_new_filter_entities()

        assert len(added_entities) == 1

    @pytest.mark.asyncio
    async def test_manager_skips_existing_filters(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test manager doesn't duplicate existing filters."""
        from custom_components.adguard_home_extended.filter_lists import (
            FilterListEntityManager,
        )

        mock_coordinator.data.filtering = FilteringStatus(
            enabled=True,
            filters=[{"url": "https://example.com/filter.txt", "name": "Filter"}],
            whitelist_filters=[],
        )

        added_entities = []
        mock_add_entities = MagicMock(side_effect=lambda e: added_entities.extend(e))

        manager = FilterListEntityManager(mock_coordinator, mock_add_entities)
        await manager.async_setup()

        initial_count = len(added_entities)

        # Call again - should not duplicate
        await manager._async_add_new_filter_entities()

        assert len(added_entities) == initial_count

    def test_manager_unsubscribe(self, mock_coordinator: MagicMock) -> None:
        """Test manager unsubscribe."""
        from custom_components.adguard_home_extended.filter_lists import (
            FilterListEntityManager,
        )

        unsubscribe_called = []
        mock_coordinator.async_add_listener = MagicMock(
            return_value=lambda: unsubscribe_called.append(True)
        )

        manager = FilterListEntityManager(mock_coordinator, MagicMock())
        manager._unsubscribe = mock_coordinator.async_add_listener()

        manager.async_unsubscribe()

        assert len(unsubscribe_called) == 1
        assert manager._unsubscribe is None

    def test_manager_handle_coordinator_update(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test manager coordinator update callback."""
        from custom_components.adguard_home_extended.filter_lists import (
            FilterListEntityManager,
        )

        manager = FilterListEntityManager(mock_coordinator, MagicMock())

        manager._handle_coordinator_update()

        mock_coordinator.hass.async_create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_manager_handles_none_data(self, mock_coordinator: MagicMock) -> None:
        """Test manager handles None coordinator data gracefully."""
        from custom_components.adguard_home_extended.filter_lists import (
            FilterListEntityManager,
        )

        mock_coordinator.data = None

        added_entities = []
        mock_add_entities = MagicMock(side_effect=lambda e: added_entities.extend(e))

        manager = FilterListEntityManager(mock_coordinator, mock_add_entities)
        await manager._async_add_new_filter_entities()

        # Should not crash and add no entities
        assert len(added_entities) == 0


class TestFilterListSwitchAdditional:
    """Additional tests for FilterListSwitch edge cases."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Return a mock coordinator."""
        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test_entry_id"
        coordinator.device_info = {"identifiers": {("test", "test")}}
        coordinator.last_update_success = True
        coordinator.client = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()
        return coordinator

    def test_switch_uses_url_as_name_fallback(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test switch uses URL as name when name is missing."""
        filter_data = {"url": "https://example.com/filter.txt"}
        switch = FilterListSwitch(mock_coordinator, filter_data, whitelist=False)
        # Name should include the URL since name is not provided
        assert "https://example.com/filter.txt" in switch.name

    def test_extra_state_attributes_empty_when_no_filter(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test extra_state_attributes returns empty dict when filter not found."""
        data = AdGuardHomeData()
        data.filtering = FilteringStatus(enabled=True, filters=[])
        mock_coordinator.data = data

        filter_data = {"url": "https://missing.com/filter.txt", "name": "Missing"}
        switch = FilterListSwitch(mock_coordinator, filter_data, whitelist=False)
        assert switch.extra_state_attributes == {}

    def test_get_filter_data_no_filtering(self, mock_coordinator: MagicMock) -> None:
        """Test _get_filter_data returns None when no filtering data."""
        mock_coordinator.data = AdGuardHomeData()
        mock_coordinator.data.filtering = None

        filter_data = {"url": "https://example.com/filter.txt", "name": "Filter"}
        switch = FilterListSwitch(mock_coordinator, filter_data, whitelist=False)
        assert switch._get_filter_data() is None

    def test_get_filter_data_no_data(self, mock_coordinator: MagicMock) -> None:
        """Test _get_filter_data returns None when no coordinator data."""
        mock_coordinator.data = None

        filter_data = {"url": "https://example.com/filter.txt", "name": "Filter"}
        switch = FilterListSwitch(mock_coordinator, filter_data, whitelist=False)
        assert switch._get_filter_data() is None

    def test_get_filter_data_whitelist(self, mock_coordinator: MagicMock) -> None:
        """Test _get_filter_data searches whitelist filters correctly."""
        data = AdGuardHomeData()
        data.filtering = FilteringStatus(
            enabled=True,
            filters=[],
            whitelist_filters=[
                {
                    "url": "https://example.com/whitelist.txt",
                    "name": "Whitelist",
                    "enabled": True,
                }
            ],
        )
        mock_coordinator.data = data

        filter_data = {"url": "https://example.com/whitelist.txt", "name": "Whitelist"}
        switch = FilterListSwitch(mock_coordinator, filter_data, whitelist=True)
        result = switch._get_filter_data()

        assert result is not None
        assert result["url"] == "https://example.com/whitelist.txt"
