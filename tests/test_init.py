"""Tests for the AdGuard Home Extended integration init."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError

from custom_components.adguard_home_extended import (
    _get_coordinator,
    async_unload_entry,
)
from custom_components.adguard_home_extended.const import DOMAIN


class TestAsyncUnloadEntry:
    """Tests for async_unload_entry."""

    @pytest.fixture
    def mock_hass(self) -> MagicMock:
        """Return a mock Home Assistant instance."""
        hass = MagicMock(spec=HomeAssistant)
        hass.config_entries = MagicMock()
        hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
        hass.config_entries.async_entries = MagicMock(return_value=[])
        hass.services = MagicMock()
        hass.services.async_remove = MagicMock()
        return hass

    @pytest.fixture
    def mock_entry(self) -> MagicMock:
        """Return a mock config entry."""
        entry = MagicMock()
        entry.entry_id = "test_entry_123"
        entry.runtime_data = MagicMock()  # Coordinator is now in runtime_data
        return entry

    @pytest.mark.asyncio
    async def test_unload_cleans_up_client_manager(
        self, mock_hass: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test that unload cleans up ClientEntityManager."""
        # Setup mock client manager
        mock_client_manager = MagicMock()
        mock_client_manager.async_unsubscribe = MagicMock()

        # Only managers are in hass.data now, coordinator is in runtime_data
        mock_hass.data = {
            DOMAIN: {
                "client_managers": {
                    mock_entry.entry_id: mock_client_manager,
                },
            }
        }
        # No other entries loaded
        mock_hass.config_entries.async_entries = MagicMock(return_value=[mock_entry])

        result = await async_unload_entry(mock_hass, mock_entry)

        assert result is True
        # Verify client manager was unsubscribed
        mock_client_manager.async_unsubscribe.assert_called_once()
        # Verify client_managers dict was cleaned up (empty dict removed)
        assert "client_managers" not in mock_hass.data[DOMAIN]

    @pytest.mark.asyncio
    async def test_unload_without_client_manager(
        self, mock_hass: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test unload works when there's no client manager."""
        # Only coordinator in runtime_data, no managers
        mock_hass.data = {DOMAIN: {}}
        # No other entries loaded
        mock_hass.config_entries.async_entries = MagicMock(return_value=[mock_entry])

        result = await async_unload_entry(mock_hass, mock_entry)

        assert result is True
        # Nothing to clean up from hass.data since coordinator is in runtime_data

    @pytest.mark.asyncio
    async def test_unload_removes_services_when_last_entry(
        self, mock_hass: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test that services are removed when last entry is unloaded."""
        mock_hass.data = {DOMAIN: {}}
        # Only this entry exists
        mock_hass.config_entries.async_entries = MagicMock(return_value=[mock_entry])

        result = await async_unload_entry(mock_hass, mock_entry)

        assert result is True
        # Verify services were removed
        assert mock_hass.services.async_remove.call_count >= 7  # All services removed

    @pytest.mark.asyncio
    async def test_unload_keeps_services_when_other_entries_exist(
        self, mock_hass: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test that services are kept when other entries still exist."""
        other_entry = MagicMock()
        other_entry.entry_id = "other_entry_456"
        other_entry.runtime_data = MagicMock()

        mock_hass.data = {DOMAIN: {}}
        # Multiple entries exist
        mock_hass.config_entries.async_entries = MagicMock(
            return_value=[mock_entry, other_entry]
        )

        result = await async_unload_entry(mock_hass, mock_entry)

        assert result is True
        # Services should not be removed (other entries still exist)
        mock_hass.services.async_remove.assert_not_called()

    @pytest.mark.asyncio
    async def test_unload_cleans_up_empty_client_managers_dict(
        self, mock_hass: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test that empty client_managers dict is cleaned up."""
        mock_client_manager = MagicMock()
        mock_client_manager.async_unsubscribe = MagicMock()

        mock_hass.data = {
            DOMAIN: {
                "client_managers": {
                    mock_entry.entry_id: mock_client_manager,
                },
            }
        }
        # Only this entry loaded
        mock_hass.config_entries.async_entries = MagicMock(return_value=[mock_entry])

        result = await async_unload_entry(mock_hass, mock_entry)

        assert result is True
        # Empty client_managers should be removed
        assert "client_managers" not in mock_hass.data[DOMAIN]

    @pytest.mark.asyncio
    async def test_unload_returns_false_on_platform_unload_failure(
        self, mock_hass: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test that unload returns False when platform unload fails."""
        mock_hass.config_entries.async_unload_platforms = AsyncMock(return_value=False)
        mock_hass.data = {DOMAIN: {}}
        mock_hass.config_entries.async_entries = MagicMock(return_value=[mock_entry])

        result = await async_unload_entry(mock_hass, mock_entry)

        assert result is False


class TestAsyncMigrateEntry:
    """Tests for async_migrate_entry."""

    @pytest.fixture
    def mock_hass(self) -> MagicMock:
        """Return a mock Home Assistant instance."""
        return MagicMock(spec=HomeAssistant)

    @pytest.fixture
    def mock_entry(self) -> MagicMock:
        """Return a mock config entry."""
        entry = MagicMock()
        entry.entry_id = "test_entry_123"
        entry.version = 1
        return entry

    @pytest.mark.asyncio
    async def test_migrate_entry_version_1(
        self, mock_hass: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test migration of version 1 entry (current version)."""
        from custom_components.adguard_home_extended import async_migrate_entry

        mock_entry.version = 1

        result = await async_migrate_entry(mock_hass, mock_entry)

        assert result is True

    @pytest.mark.asyncio
    async def test_migrate_entry_future_version_fails(
        self, mock_hass: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test that migration from future version fails."""
        from custom_components.adguard_home_extended import async_migrate_entry

        mock_entry.version = 999  # Future version

        result = await async_migrate_entry(mock_hass, mock_entry)

        assert result is False


class TestAsyncRemoveEntry:
    """Tests for async_remove_entry."""

    @pytest.fixture
    def mock_hass(self) -> MagicMock:
        """Return a mock Home Assistant instance."""
        hass = MagicMock(spec=HomeAssistant)
        return hass

    @pytest.fixture
    def mock_entry(self) -> MagicMock:
        """Return a mock config entry."""
        entry = MagicMock()
        entry.entry_id = "test_entry_123"
        entry.runtime_data = MagicMock()
        return entry

    @pytest.mark.asyncio
    async def test_remove_entry_cleans_up_domain_data(
        self, mock_hass: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test that remove entry cleans up domain data."""
        from custom_components.adguard_home_extended import async_remove_entry

        # With runtime_data, hass.data only has managers, not coordinators
        mock_hass.data = {DOMAIN: {}}

        await async_remove_entry(mock_hass, mock_entry)

        # Domain data should be cleaned up completely if empty
        assert DOMAIN not in mock_hass.data

    @pytest.mark.asyncio
    async def test_remove_entry_cleans_up_client_managers(
        self, mock_hass: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test that remove entry cleans up client_managers."""
        from custom_components.adguard_home_extended import async_remove_entry

        mock_hass.data = {
            DOMAIN: {
                "client_managers": {
                    mock_entry.entry_id: MagicMock(),
                },
            }
        }

        await async_remove_entry(mock_hass, mock_entry)

        # Domain data should be cleaned up completely if empty
        assert DOMAIN not in mock_hass.data

    @pytest.mark.asyncio
    async def test_remove_entry_preserves_other_managers(
        self, mock_hass: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test that remove entry preserves other managers."""
        from custom_components.adguard_home_extended import async_remove_entry

        other_entry_id = "other_entry_456"
        mock_hass.data = {
            DOMAIN: {
                "client_managers": {
                    mock_entry.entry_id: MagicMock(),
                    other_entry_id: MagicMock(),
                }
            }
        }

        await async_remove_entry(mock_hass, mock_entry)

        # Domain data should still exist with other manager
        assert DOMAIN in mock_hass.data
        assert other_entry_id in mock_hass.data[DOMAIN]["client_managers"]

    @pytest.mark.asyncio
    async def test_remove_entry_no_data(
        self, mock_hass: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test that remove entry handles missing data gracefully."""
        from custom_components.adguard_home_extended import async_remove_entry

        mock_hass.data = {}  # No DOMAIN data

        # Should not raise
        await async_remove_entry(mock_hass, mock_entry)


class TestCheckHostService:
    """Tests for the check_host service."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Return a mock coordinator."""
        coordinator = MagicMock()
        coordinator.client = MagicMock()
        coordinator.client.check_host = AsyncMock(
            return_value={
                "reason": "FilteredBlackList",
                "rule": "||ads.example.com^",
            }
        )
        return coordinator

    @pytest.fixture
    def mock_hass(self, mock_coordinator: MagicMock) -> MagicMock:
        """Return a mock Home Assistant instance."""
        hass = MagicMock(spec=HomeAssistant)
        hass.bus = MagicMock()
        hass.bus.async_fire = MagicMock()
        hass.data = {DOMAIN: {"test_entry": mock_coordinator}}
        return hass

    @pytest.mark.asyncio
    async def test_check_host_service_basic(
        self, mock_hass: MagicMock, mock_coordinator: MagicMock
    ) -> None:
        """Test check_host service with basic domain query."""

        # Call the coordinator method directly (simulating service handler)
        result = await mock_coordinator.client.check_host(
            name="ads.example.com",
            client=None,
            qtype=None,
        )

        assert result["reason"] == "FilteredBlackList"
        assert result["rule"] == "||ads.example.com^"
        mock_coordinator.client.check_host.assert_called_once_with(
            name="ads.example.com",
            client=None,
            qtype=None,
        )

    @pytest.mark.asyncio
    async def test_check_host_service_with_client_and_qtype(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test check_host service with client and qtype parameters."""
        mock_coordinator.client.check_host = AsyncMock(
            return_value={
                "reason": "NotFilteredAllowList",
            }
        )

        result = await mock_coordinator.client.check_host(
            name="allowed.example.com",
            client="192.168.1.100",
            qtype="AAAA",
        )

        assert result["reason"] == "NotFilteredAllowList"
        mock_coordinator.client.check_host.assert_called_once_with(
            name="allowed.example.com",
            client="192.168.1.100",
            qtype="AAAA",
        )


class TestGetQueryLogService:
    """Tests for the get_query_log service."""

    @pytest.fixture
    def mock_query_log_entries(self) -> list[dict]:
        """Return mock query log entries."""
        return [
            {
                "answer": [{"value": "93.184.216.34", "type": "A", "ttl": 300}],
                "client": "192.168.1.100",
                "client_proto": "dns",
                "elapsedMs": "5.123",
                "question": {"class": "IN", "name": "example.com", "type": "A"},
                "reason": "NotFilteredNotFound",
                "status": "NOERROR",
                "time": "2024-01-15T10:30:00Z",
            },
            {
                "answer": [],
                "client": "192.168.1.101",
                "client_proto": "dns",
                "elapsedMs": "1.234",
                "question": {"class": "IN", "name": "ads.example.com", "type": "A"},
                "reason": "FilteredBlackList",
                "rule": "||ads.example.com^",
                "status": "NXDOMAIN",
                "time": "2024-01-15T10:30:01Z",
            },
        ]

    @pytest.fixture
    def mock_coordinator(self, mock_query_log_entries: list[dict]) -> MagicMock:
        """Return a mock coordinator."""
        coordinator = MagicMock()
        coordinator.client = MagicMock()
        coordinator.client.get_query_log = AsyncMock(
            return_value=mock_query_log_entries
        )
        return coordinator

    @pytest.fixture
    def mock_hass(self, mock_coordinator: MagicMock) -> MagicMock:
        """Return a mock Home Assistant instance."""
        hass = MagicMock(spec=HomeAssistant)
        hass.data = {DOMAIN: {"test_entry": mock_coordinator}}
        return hass

    @pytest.mark.asyncio
    async def test_get_query_log_default_params(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test get_query_log with default parameters."""
        result = await mock_coordinator.client.get_query_log(
            limit=100,
            offset=0,
            search=None,
            response_status=None,
        )

        assert len(result) == 2
        assert result[0]["question"]["name"] == "example.com"
        assert result[1]["reason"] == "FilteredBlackList"
        mock_coordinator.client.get_query_log.assert_called_once_with(
            limit=100,
            offset=0,
            search=None,
            response_status=None,
        )

    @pytest.mark.asyncio
    async def test_get_query_log_with_pagination(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test get_query_log with pagination parameters."""
        mock_coordinator.client.get_query_log = AsyncMock(return_value=[])

        result = await mock_coordinator.client.get_query_log(
            limit=50,
            offset=100,
            search=None,
            response_status=None,
        )

        assert result == []
        mock_coordinator.client.get_query_log.assert_called_once_with(
            limit=50,
            offset=100,
            search=None,
            response_status=None,
        )

    @pytest.mark.asyncio
    async def test_get_query_log_with_search(
        self, mock_coordinator: MagicMock, mock_query_log_entries: list[dict]
    ) -> None:
        """Test get_query_log with domain search filter."""
        # Simulate filtered results
        filtered = [e for e in mock_query_log_entries if "ads" in e["question"]["name"]]
        mock_coordinator.client.get_query_log = AsyncMock(return_value=filtered)

        result = await mock_coordinator.client.get_query_log(
            limit=100,
            offset=0,
            search="ads",
            response_status=None,
        )

        assert len(result) == 1
        assert result[0]["question"]["name"] == "ads.example.com"
        mock_coordinator.client.get_query_log.assert_called_once_with(
            limit=100,
            offset=0,
            search="ads",
            response_status=None,
        )

    @pytest.mark.asyncio
    async def test_get_query_log_with_response_status(
        self, mock_coordinator: MagicMock, mock_query_log_entries: list[dict]
    ) -> None:
        """Test get_query_log with response_status filter (v0.107.68+)."""
        # Simulate filtered-only results
        filtered = [
            e for e in mock_query_log_entries if e["reason"] == "FilteredBlackList"
        ]
        mock_coordinator.client.get_query_log = AsyncMock(return_value=filtered)

        result = await mock_coordinator.client.get_query_log(
            limit=100,
            offset=0,
            search=None,
            response_status="filtered",
        )

        assert len(result) == 1
        assert result[0]["reason"] == "FilteredBlackList"
        mock_coordinator.client.get_query_log.assert_called_once_with(
            limit=100,
            offset=0,
            search=None,
            response_status="filtered",
        )

    @pytest.mark.asyncio
    async def test_get_query_log_response_format(
        self, mock_coordinator: MagicMock, mock_query_log_entries: list[dict]
    ) -> None:
        """Test the expected response format from the service."""
        # Simulate the service handler response format
        entries = await mock_coordinator.client.get_query_log(
            limit=100,
            offset=0,
            search=None,
            response_status=None,
        )

        response = {
            "entries": entries,
            "count": len(entries),
            "limit": 100,
            "offset": 0,
            "search": None,
            "response_status": None,
        }

        assert response["count"] == 2
        assert response["limit"] == 100
        assert response["offset"] == 0
        assert len(response["entries"]) == 2


class TestGetCoordinator:
    """Tests for the _get_coordinator helper function."""

    @pytest.fixture
    def mock_hass(self) -> MagicMock:
        """Return a mock Home Assistant instance."""
        hass = MagicMock(spec=HomeAssistant)
        hass.config_entries = MagicMock()
        return hass

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Return a mock coordinator."""
        return MagicMock()

    @pytest.fixture
    def mock_entry(self, mock_coordinator: MagicMock) -> MagicMock:
        """Return a mock config entry with runtime_data."""
        entry = MagicMock()
        entry.entry_id = "test_entry_123"
        entry.runtime_data = mock_coordinator
        return entry

    def test_get_coordinator_no_entries(self, mock_hass: MagicMock) -> None:
        """Test _get_coordinator raises when no entries exist."""
        mock_hass.config_entries.async_entries = MagicMock(return_value=[])

        with pytest.raises(HomeAssistantError, match="No AdGuard Home instances"):
            _get_coordinator(mock_hass, None)

    def test_get_coordinator_with_entry_id(
        self, mock_hass: MagicMock, mock_entry: MagicMock, mock_coordinator: MagicMock
    ) -> None:
        """Test _get_coordinator returns coordinator for specified entry_id."""
        mock_hass.config_entries.async_entries = MagicMock(return_value=[mock_entry])

        result = _get_coordinator(mock_hass, "test_entry_123")

        assert result == mock_coordinator

    def test_get_coordinator_entry_id_not_found(
        self, mock_hass: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test _get_coordinator raises when entry_id not found."""
        mock_hass.config_entries.async_entries = MagicMock(return_value=[mock_entry])

        with pytest.raises(HomeAssistantError, match="not found"):
            _get_coordinator(mock_hass, "nonexistent_entry")

    def test_get_coordinator_single_entry_no_id(
        self, mock_hass: MagicMock, mock_entry: MagicMock, mock_coordinator: MagicMock
    ) -> None:
        """Test _get_coordinator returns single entry when no entry_id specified."""
        mock_hass.config_entries.async_entries = MagicMock(return_value=[mock_entry])

        result = _get_coordinator(mock_hass, None)

        assert result == mock_coordinator

    def test_get_coordinator_multiple_entries_no_id(
        self, mock_hass: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test _get_coordinator raises when multiple entries and no entry_id."""
        other_entry = MagicMock()
        other_entry.entry_id = "other_entry_456"
        other_entry.runtime_data = MagicMock()
        mock_hass.config_entries.async_entries = MagicMock(
            return_value=[mock_entry, other_entry]
        )

        with pytest.raises(HomeAssistantError, match="Multiple AdGuard Home instances"):
            _get_coordinator(mock_hass, None)


class TestServiceHandlers:
    """Tests for the service handler functions."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Return a mock coordinator."""
        coordinator = MagicMock()
        coordinator.client = MagicMock()
        coordinator.client.set_blocked_services = AsyncMock()
        coordinator.client.add_filter_url = AsyncMock()
        coordinator.client.remove_filter_url = AsyncMock()
        coordinator.client.refresh_filters = AsyncMock()
        coordinator.client.update_client = AsyncMock()
        coordinator.client.add_rewrite = AsyncMock()
        coordinator.client.delete_rewrite = AsyncMock()
        coordinator.client.check_host = AsyncMock(
            return_value={"reason": "NotFilteredNotFound"}
        )
        coordinator.client.get_query_log = AsyncMock(return_value=[])
        coordinator.client.clear_query_log = AsyncMock()
        coordinator.client.reset_stats = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()
        coordinator.data = MagicMock()
        coordinator.data.clients = []
        return coordinator

    @pytest.fixture
    def mock_entry(self, mock_coordinator: MagicMock) -> MagicMock:
        """Return a mock config entry."""
        entry = MagicMock()
        entry.entry_id = "test_entry_123"
        entry.runtime_data = mock_coordinator
        return entry

    @pytest.fixture
    def mock_hass(self, mock_entry: MagicMock) -> MagicMock:
        """Return a mock Home Assistant instance."""
        hass = MagicMock(spec=HomeAssistant)
        hass.config_entries = MagicMock()
        hass.config_entries.async_entries = MagicMock(return_value=[mock_entry])
        hass.services = MagicMock()
        hass.services.async_register = MagicMock()
        hass.services.has_service = MagicMock(return_value=False)
        hass.bus = MagicMock()
        hass.bus.async_fire = MagicMock()
        hass.data = {DOMAIN: {}}
        return hass

    @pytest.mark.asyncio
    async def test_handle_set_blocked_services(
        self, mock_hass: MagicMock, mock_coordinator: MagicMock
    ) -> None:
        """Test handle_set_blocked_services service handler."""
        from custom_components.adguard_home_extended import _async_setup_services

        await _async_setup_services(mock_hass)

        # Get the registered handler
        calls = mock_hass.services.async_register.call_args_list
        handler = None
        for call in calls:
            if call[0][1] == "set_blocked_services":
                handler = call[0][2]
                break

        assert handler is not None

        # Create service call
        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {
            "services": ["facebook", "youtube"],
        }

        await handler(service_call)

        mock_coordinator.client.set_blocked_services.assert_called_once_with(
            ["facebook", "youtube"], None
        )
        mock_coordinator.async_request_refresh.assert_called()

    @pytest.mark.asyncio
    async def test_handle_set_blocked_services_with_schedule(
        self, mock_hass: MagicMock, mock_coordinator: MagicMock
    ) -> None:
        """Test handle_set_blocked_services with schedule parameter."""
        from custom_components.adguard_home_extended import _async_setup_services

        await _async_setup_services(mock_hass)

        calls = mock_hass.services.async_register.call_args_list
        handler = None
        for call in calls:
            if call[0][1] == "set_blocked_services":
                handler = call[0][2]
                break

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {
            "services": ["tiktok"],
            "schedule": {"mon": [{"start": 540, "end": 1020}]},
        }

        await handler(service_call)

        mock_coordinator.client.set_blocked_services.assert_called_once_with(
            ["tiktok"], {"mon": [{"start": 540, "end": 1020}]}
        )

    @pytest.mark.asyncio
    async def test_handle_add_filter_url(
        self, mock_hass: MagicMock, mock_coordinator: MagicMock
    ) -> None:
        """Test handle_add_filter_url service handler."""
        from custom_components.adguard_home_extended import _async_setup_services

        await _async_setup_services(mock_hass)

        calls = mock_hass.services.async_register.call_args_list
        handler = None
        for call in calls:
            if call[0][1] == "add_filter_url":
                handler = call[0][2]
                break

        assert handler is not None

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {
            "name": "Test Filter",
            "url": "https://example.com/filter.txt",
        }

        await handler(service_call)

        mock_coordinator.client.add_filter_url.assert_called_once_with(
            "Test Filter", "https://example.com/filter.txt", False
        )
        mock_coordinator.async_request_refresh.assert_called()

    @pytest.mark.asyncio
    async def test_handle_add_filter_url_whitelist(
        self, mock_hass: MagicMock, mock_coordinator: MagicMock
    ) -> None:
        """Test handle_add_filter_url with whitelist parameter."""
        from custom_components.adguard_home_extended import _async_setup_services

        await _async_setup_services(mock_hass)

        calls = mock_hass.services.async_register.call_args_list
        handler = None
        for call in calls:
            if call[0][1] == "add_filter_url":
                handler = call[0][2]
                break

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {
            "name": "Allowlist",
            "url": "https://example.com/allowlist.txt",
            "whitelist": True,
        }

        await handler(service_call)

        mock_coordinator.client.add_filter_url.assert_called_once_with(
            "Allowlist", "https://example.com/allowlist.txt", True
        )

    @pytest.mark.asyncio
    async def test_handle_remove_filter_url(
        self, mock_hass: MagicMock, mock_coordinator: MagicMock
    ) -> None:
        """Test handle_remove_filter_url service handler."""
        from custom_components.adguard_home_extended import _async_setup_services

        await _async_setup_services(mock_hass)

        calls = mock_hass.services.async_register.call_args_list
        handler = None
        for call in calls:
            if call[0][1] == "remove_filter_url":
                handler = call[0][2]
                break

        assert handler is not None

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {
            "url": "https://example.com/filter.txt",
        }

        await handler(service_call)

        mock_coordinator.client.remove_filter_url.assert_called_once_with(
            "https://example.com/filter.txt", False
        )
        mock_coordinator.async_request_refresh.assert_called()

    @pytest.mark.asyncio
    async def test_handle_refresh_filters(
        self, mock_hass: MagicMock, mock_coordinator: MagicMock
    ) -> None:
        """Test handle_refresh_filters service handler."""
        from custom_components.adguard_home_extended import _async_setup_services

        await _async_setup_services(mock_hass)

        calls = mock_hass.services.async_register.call_args_list
        handler = None
        for call in calls:
            if call[0][1] == "refresh_filters":
                handler = call[0][2]
                break

        assert handler is not None

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {}

        await handler(service_call)

        mock_coordinator.client.refresh_filters.assert_called_once()
        mock_coordinator.async_request_refresh.assert_called()

    @pytest.mark.asyncio
    async def test_handle_set_client_blocked_services(
        self, mock_hass: MagicMock, mock_coordinator: MagicMock
    ) -> None:
        """Test handle_set_client_blocked_services service handler."""
        from custom_components.adguard_home_extended import _async_setup_services

        await _async_setup_services(mock_hass)

        # Setup mock client data
        mock_coordinator.data.clients = [
            {
                "name": "laptop",
                "ids": ["192.168.1.100"],
                "use_global_settings": True,
                "filtering_enabled": True,
                "parental_enabled": False,
                "safebrowsing_enabled": False,
                "safesearch_enabled": False,
                "use_global_blocked_services": True,
                "blocked_services": [],
                "tags": [],
            }
        ]

        calls = mock_hass.services.async_register.call_args_list
        handler = None
        for call in calls:
            if call[0][1] == "set_client_blocked_services":
                handler = call[0][2]
                break

        assert handler is not None

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {
            "client_name": "laptop",
            "services": ["facebook", "tiktok"],
        }

        await handler(service_call)

        mock_coordinator.client.update_client.assert_called_once()
        mock_coordinator.async_request_refresh.assert_called()

    @pytest.mark.asyncio
    async def test_handle_set_client_blocked_services_preserves_all_fields(
        self, mock_hass: MagicMock, mock_coordinator: MagicMock
    ) -> None:
        """Test handle_set_client_blocked_services preserves all client fields."""
        from custom_components.adguard_home_extended import _async_setup_services
        from custom_components.adguard_home_extended.api.models import (
            AdGuardHomeClient,
        )

        await _async_setup_services(mock_hass)

        # Setup mock client data with all fields that should be preserved
        mock_coordinator.data.clients = [
            {
                "name": "laptop",
                "ids": ["192.168.1.100"],
                "uid": "abc123",
                "use_global_settings": False,
                "filtering_enabled": True,
                "parental_enabled": True,
                "safebrowsing_enabled": True,
                "safesearch_enabled": True,
                "safe_search": {
                    "enabled": True,
                    "bing": True,
                    "duckduckgo": True,
                    "ecosia": True,
                    "google": True,
                    "pixabay": True,
                    "yandex": True,
                    "youtube": True,
                },
                "use_global_blocked_services": True,
                "blocked_services": ["youtube"],
                "blocked_services_schedule": {"time_zone": "America/New_York"},
                "upstreams": ["https://1.1.1.1/dns-query"],
                "tags": ["device_laptop"],
                "upstreams_cache_enabled": True,
                "upstreams_cache_size": 4096,
                "ignore_querylog": True,
                "ignore_statistics": True,
            }
        ]

        calls = mock_hass.services.async_register.call_args_list
        handler = None
        for call in calls:
            if call[0][1] == "set_client_blocked_services":
                handler = call[0][2]
                break

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {
            "client_name": "laptop",
            "services": ["facebook", "tiktok"],
        }

        await handler(service_call)

        # Verify update_client was called with preserved fields
        mock_coordinator.client.update_client.assert_called_once()
        call_args = mock_coordinator.client.update_client.call_args
        client_arg: AdGuardHomeClient = call_args[0][1]

        # Verify the blocked services were updated
        assert client_arg.blocked_services == ["facebook", "tiktok"]
        assert client_arg.use_global_blocked_services is False

        # Verify all other fields were preserved
        assert client_arg.name == "laptop"
        assert client_arg.ids == ["192.168.1.100"]
        assert client_arg.uid == "abc123"
        assert client_arg.use_global_settings is False
        assert client_arg.filtering_enabled is True
        assert client_arg.parental_enabled is True
        assert client_arg.safebrowsing_enabled is True
        assert client_arg.safesearch_enabled is True
        assert client_arg.safe_search is not None
        assert client_arg.safe_search.enabled is True
        assert client_arg.blocked_services_schedule == {"time_zone": "America/New_York"}
        assert client_arg.upstreams == ["https://1.1.1.1/dns-query"]
        assert client_arg.tags == ["device_laptop"]
        assert client_arg.upstreams_cache_enabled is True
        assert client_arg.upstreams_cache_size == 4096
        assert client_arg.ignore_querylog is True
        assert client_arg.ignore_statistics is True

    @pytest.mark.asyncio
    async def test_handle_set_client_blocked_services_client_not_found(
        self, mock_hass: MagicMock, mock_coordinator: MagicMock
    ) -> None:
        """Test handle_set_client_blocked_services raises when client not found."""
        from custom_components.adguard_home_extended import _async_setup_services

        await _async_setup_services(mock_hass)

        mock_coordinator.data.clients = []

        calls = mock_hass.services.async_register.call_args_list
        handler = None
        for call in calls:
            if call[0][1] == "set_client_blocked_services":
                handler = call[0][2]
                break

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {
            "client_name": "nonexistent",
            "services": ["facebook"],
        }

        with pytest.raises(HomeAssistantError, match="not found"):
            await handler(service_call)

    @pytest.mark.asyncio
    async def test_handle_set_client_blocked_services_no_data(
        self, mock_hass: MagicMock, mock_coordinator: MagicMock
    ) -> None:
        """Test handle_set_client_blocked_services raises when no data."""
        from custom_components.adguard_home_extended import _async_setup_services

        await _async_setup_services(mock_hass)

        mock_coordinator.data = None

        calls = mock_hass.services.async_register.call_args_list
        handler = None
        for call in calls:
            if call[0][1] == "set_client_blocked_services":
                handler = call[0][2]
                break

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {
            "client_name": "laptop",
            "services": ["facebook"],
        }

        with pytest.raises(HomeAssistantError, match="No data available"):
            await handler(service_call)

    @pytest.mark.asyncio
    async def test_handle_add_dns_rewrite(
        self, mock_hass: MagicMock, mock_coordinator: MagicMock
    ) -> None:
        """Test handle_add_dns_rewrite service handler."""
        from custom_components.adguard_home_extended import _async_setup_services

        await _async_setup_services(mock_hass)

        calls = mock_hass.services.async_register.call_args_list
        handler = None
        for call in calls:
            if call[0][1] == "add_dns_rewrite":
                handler = call[0][2]
                break

        assert handler is not None

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {
            "domain": "example.local",
            "answer": "192.168.1.100",
        }

        await handler(service_call)

        mock_coordinator.client.add_rewrite.assert_called_once_with(
            "example.local", "192.168.1.100"
        )
        mock_coordinator.async_request_refresh.assert_called()

    @pytest.mark.asyncio
    async def test_handle_remove_dns_rewrite(
        self, mock_hass: MagicMock, mock_coordinator: MagicMock
    ) -> None:
        """Test handle_remove_dns_rewrite service handler."""
        from custom_components.adguard_home_extended import _async_setup_services

        await _async_setup_services(mock_hass)

        calls = mock_hass.services.async_register.call_args_list
        handler = None
        for call in calls:
            if call[0][1] == "remove_dns_rewrite":
                handler = call[0][2]
                break

        assert handler is not None

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {
            "domain": "example.local",
            "answer": "192.168.1.100",
        }

        await handler(service_call)

        mock_coordinator.client.delete_rewrite.assert_called_once_with(
            "example.local", "192.168.1.100"
        )
        mock_coordinator.async_request_refresh.assert_called()

    @pytest.mark.asyncio
    async def test_handle_check_host(
        self, mock_hass: MagicMock, mock_coordinator: MagicMock
    ) -> None:
        """Test handle_check_host service handler."""
        from custom_components.adguard_home_extended import _async_setup_services

        await _async_setup_services(mock_hass)

        calls = mock_hass.services.async_register.call_args_list
        handler = None
        for call in calls:
            if call[0][1] == "check_host":
                handler = call[0][2]
                break

        assert handler is not None

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {
            "domain": "ads.example.com",
        }

        result = await handler(service_call)

        mock_coordinator.client.check_host.assert_called_once_with(
            name="ads.example.com",
            client=None,
            qtype=None,
        )
        mock_hass.bus.async_fire.assert_called_once()
        assert result == {"reason": "NotFilteredNotFound"}

    @pytest.mark.asyncio
    async def test_handle_check_host_with_client_and_qtype(
        self, mock_hass: MagicMock, mock_coordinator: MagicMock
    ) -> None:
        """Test handle_check_host with client and qtype parameters."""
        from custom_components.adguard_home_extended import _async_setup_services

        await _async_setup_services(mock_hass)

        calls = mock_hass.services.async_register.call_args_list
        handler = None
        for call in calls:
            if call[0][1] == "check_host":
                handler = call[0][2]
                break

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {
            "domain": "example.com",
            "client": "192.168.1.100",
            "qtype": "AAAA",
        }

        await handler(service_call)

        mock_coordinator.client.check_host.assert_called_once_with(
            name="example.com",
            client="192.168.1.100",
            qtype="AAAA",
        )

    @pytest.mark.asyncio
    async def test_handle_get_query_log(
        self, mock_hass: MagicMock, mock_coordinator: MagicMock
    ) -> None:
        """Test handle_get_query_log service handler."""
        from custom_components.adguard_home_extended import _async_setup_services

        mock_coordinator.client.get_query_log = AsyncMock(
            return_value=[{"question": {"name": "example.com"}}]
        )

        await _async_setup_services(mock_hass)

        calls = mock_hass.services.async_register.call_args_list
        handler = None
        for call in calls:
            if call[0][1] == "get_query_log":
                handler = call[0][2]
                break

        assert handler is not None

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {}

        result = await handler(service_call)

        mock_coordinator.client.get_query_log.assert_called_once_with(
            limit=100,
            offset=0,
            search=None,
            response_status=None,
        )
        assert result["count"] == 1
        assert result["limit"] == 100
        assert result["offset"] == 0

    @pytest.mark.asyncio
    async def test_handle_get_query_log_with_params(
        self, mock_hass: MagicMock, mock_coordinator: MagicMock
    ) -> None:
        """Test handle_get_query_log with all parameters."""
        from custom_components.adguard_home_extended import _async_setup_services

        await _async_setup_services(mock_hass)

        calls = mock_hass.services.async_register.call_args_list
        handler = None
        for call in calls:
            if call[0][1] == "get_query_log":
                handler = call[0][2]
                break

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {
            "limit": 50,
            "offset": 100,
            "search": "example",
            "response_status": "filtered",
        }

        await handler(service_call)

        mock_coordinator.client.get_query_log.assert_called_once_with(
            limit=50,
            offset=100,
            search="example",
            response_status="filtered",
        )

    @pytest.mark.asyncio
    async def test_handle_clear_query_log(
        self, mock_hass: MagicMock, mock_coordinator: MagicMock
    ) -> None:
        """Test handle_clear_query_log service handler."""
        from custom_components.adguard_home_extended import _async_setup_services

        await _async_setup_services(mock_hass)

        calls = mock_hass.services.async_register.call_args_list
        handler = None
        for call in calls:
            if call[0][1] == "clear_query_log":
                handler = call[0][2]
                break

        assert handler is not None

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {}

        await handler(service_call)

        mock_coordinator.client.clear_query_log.assert_called_once()
        mock_coordinator.async_request_refresh.assert_called()

    @pytest.mark.asyncio
    async def test_handle_reset_stats(
        self, mock_hass: MagicMock, mock_coordinator: MagicMock
    ) -> None:
        """Test handle_reset_stats service handler."""
        from custom_components.adguard_home_extended import _async_setup_services

        await _async_setup_services(mock_hass)

        calls = mock_hass.services.async_register.call_args_list
        handler = None
        for call in calls:
            if call[0][1] == "reset_stats":
                handler = call[0][2]
                break

        assert handler is not None

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {}

        await handler(service_call)

        mock_coordinator.client.reset_stats.assert_called_once()
        mock_coordinator.async_request_refresh.assert_called()

    @pytest.mark.asyncio
    async def test_services_registered_with_entry_id(
        self, mock_hass: MagicMock, mock_coordinator: MagicMock
    ) -> None:
        """Test service handlers work with explicit entry_id."""
        from custom_components.adguard_home_extended import _async_setup_services

        await _async_setup_services(mock_hass)

        # Get refresh_filters handler
        calls = mock_hass.services.async_register.call_args_list
        handler = None
        for call in calls:
            if call[0][1] == "refresh_filters":
                handler = call[0][2]
                break

        service_call = MagicMock(spec=ServiceCall)
        service_call.data = {"entry_id": "test_entry_123"}

        await handler(service_call)

        mock_coordinator.client.refresh_filters.assert_called_once()


class TestAsyncSetupEntry:
    """Tests for async_setup_entry."""

    @pytest.fixture
    def mock_hass(self) -> MagicMock:
        """Return a mock Home Assistant instance."""
        hass = MagicMock(spec=HomeAssistant)
        hass.config_entries = MagicMock()
        hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
        hass.services = MagicMock()
        hass.services.has_service = MagicMock(return_value=True)
        hass.data = {}
        return hass

    @pytest.fixture
    def mock_entry(self) -> MagicMock:
        """Return a mock config entry."""
        entry = MagicMock()
        entry.entry_id = "test_entry_123"
        entry.data = {
            "host": "192.168.1.1",
            "port": 80,
            "username": "admin",
            "password": "secret",
            "ssl": False,
            "verify_ssl": True,
        }
        entry.async_on_unload = MagicMock()
        entry.add_update_listener = MagicMock()
        return entry

    @pytest.mark.asyncio
    async def test_setup_entry_success(
        self, mock_hass: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test successful setup of config entry."""
        from custom_components.adguard_home_extended import async_setup_entry

        with (
            patch("custom_components.adguard_home_extended.async_get_clientsession"),
            patch(
                "custom_components.adguard_home_extended.api.client.AdGuardHomeClient"
            ) as mock_client_class,
            patch(
                "custom_components.adguard_home_extended.AdGuardHomeDataUpdateCoordinator"
            ) as mock_coordinator_class,
        ):
            mock_client_instance = MagicMock()
            mock_client_class.return_value = mock_client_instance

            mock_coordinator_instance = MagicMock()
            mock_coordinator_instance.async_config_entry_first_refresh = AsyncMock()
            mock_coordinator_class.return_value = mock_coordinator_instance

            result = await async_setup_entry(mock_hass, mock_entry)

            assert result is True
            assert mock_entry.runtime_data == mock_coordinator_instance
            mock_coordinator_instance.async_config_entry_first_refresh.assert_called_once()
            mock_hass.config_entries.async_forward_entry_setups.assert_called_once()
            mock_entry.async_on_unload.assert_called_once()

    @pytest.mark.asyncio
    async def test_setup_entry_registers_services_when_not_registered(
        self, mock_hass: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test that setup entry registers services when not already registered."""
        from custom_components.adguard_home_extended import async_setup_entry

        # Services not yet registered
        mock_hass.services.has_service = MagicMock(return_value=False)
        mock_hass.services.async_register = MagicMock()

        with (
            patch("custom_components.adguard_home_extended.async_get_clientsession"),
            patch(
                "custom_components.adguard_home_extended.api.client.AdGuardHomeClient"
            ),
            patch(
                "custom_components.adguard_home_extended.AdGuardHomeDataUpdateCoordinator"
            ) as mock_coordinator_class,
        ):
            mock_coordinator_instance = MagicMock()
            mock_coordinator_instance.async_config_entry_first_refresh = AsyncMock()
            mock_coordinator_class.return_value = mock_coordinator_instance

            result = await async_setup_entry(mock_hass, mock_entry)

            assert result is True
            # Should have registered 11 services
            assert mock_hass.services.async_register.call_count == 11


class TestAsyncUpdateListener:
    """Tests for _async_update_listener."""

    @pytest.mark.asyncio
    async def test_update_listener_reloads_entry(self) -> None:
        """Test that update listener reloads the config entry."""
        from custom_components.adguard_home_extended import _async_update_listener

        mock_hass = MagicMock(spec=HomeAssistant)
        mock_hass.config_entries = MagicMock()
        mock_hass.config_entries.async_reload = AsyncMock()

        mock_entry = MagicMock()
        mock_entry.entry_id = "test_entry_123"

        await _async_update_listener(mock_hass, mock_entry)

        mock_hass.config_entries.async_reload.assert_called_once_with("test_entry_123")


class TestAsyncUnloadEntryRewriteManagers:
    """Tests for async_unload_entry with rewrite managers."""

    @pytest.fixture
    def mock_hass(self) -> MagicMock:
        """Return a mock Home Assistant instance."""
        hass = MagicMock(spec=HomeAssistant)
        hass.config_entries = MagicMock()
        hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
        hass.config_entries.async_entries = MagicMock(return_value=[])
        hass.services = MagicMock()
        hass.services.async_remove = MagicMock()
        return hass

    @pytest.fixture
    def mock_entry(self) -> MagicMock:
        """Return a mock config entry."""
        entry = MagicMock()
        entry.entry_id = "test_entry_123"
        entry.runtime_data = MagicMock()
        return entry

    @pytest.mark.asyncio
    async def test_unload_cleans_up_rewrite_manager(
        self, mock_hass: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test that unload cleans up DnsRewriteEntityManager."""
        mock_rewrite_manager = MagicMock()
        mock_rewrite_manager.async_unsubscribe = MagicMock()

        mock_hass.data = {
            DOMAIN: {
                "rewrite_managers": {
                    mock_entry.entry_id: mock_rewrite_manager,
                },
            }
        }
        mock_hass.config_entries.async_entries = MagicMock(return_value=[mock_entry])

        result = await async_unload_entry(mock_hass, mock_entry)

        assert result is True
        mock_rewrite_manager.async_unsubscribe.assert_called_once()
        assert "rewrite_managers" not in mock_hass.data[DOMAIN]

    @pytest.mark.asyncio
    async def test_unload_cleans_up_both_managers(
        self, mock_hass: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test that unload cleans up both client and rewrite managers."""
        mock_client_manager = MagicMock()
        mock_client_manager.async_unsubscribe = MagicMock()

        mock_rewrite_manager = MagicMock()
        mock_rewrite_manager.async_unsubscribe = MagicMock()

        mock_hass.data = {
            DOMAIN: {
                "client_managers": {
                    mock_entry.entry_id: mock_client_manager,
                },
                "rewrite_managers": {
                    mock_entry.entry_id: mock_rewrite_manager,
                },
            }
        }
        mock_hass.config_entries.async_entries = MagicMock(return_value=[mock_entry])

        result = await async_unload_entry(mock_hass, mock_entry)

        assert result is True
        mock_client_manager.async_unsubscribe.assert_called_once()
        mock_rewrite_manager.async_unsubscribe.assert_called_once()


class TestAsyncRemoveEntryRewriteManagers:
    """Tests for async_remove_entry with rewrite managers."""

    @pytest.fixture
    def mock_hass(self) -> MagicMock:
        """Return a mock Home Assistant instance."""
        return MagicMock(spec=HomeAssistant)

    @pytest.fixture
    def mock_entry(self) -> MagicMock:
        """Return a mock config entry."""
        entry = MagicMock()
        entry.entry_id = "test_entry_123"
        entry.runtime_data = MagicMock()
        return entry

    @pytest.mark.asyncio
    async def test_remove_entry_cleans_up_rewrite_managers(
        self, mock_hass: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test that remove entry cleans up rewrite_managers."""
        from custom_components.adguard_home_extended import async_remove_entry

        mock_hass.data = {
            DOMAIN: {
                "rewrite_managers": {
                    mock_entry.entry_id: MagicMock(),
                },
            }
        }

        await async_remove_entry(mock_hass, mock_entry)

        assert DOMAIN not in mock_hass.data

    @pytest.mark.asyncio
    async def test_remove_entry_preserves_other_rewrite_managers(
        self, mock_hass: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test that remove entry preserves other rewrite managers."""
        from custom_components.adguard_home_extended import async_remove_entry

        other_entry_id = "other_entry_456"
        mock_hass.data = {
            DOMAIN: {
                "rewrite_managers": {
                    mock_entry.entry_id: MagicMock(),
                    other_entry_id: MagicMock(),
                }
            }
        }

        await async_remove_entry(mock_hass, mock_entry)

        assert DOMAIN in mock_hass.data
        assert other_entry_id in mock_hass.data[DOMAIN]["rewrite_managers"]
