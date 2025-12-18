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
