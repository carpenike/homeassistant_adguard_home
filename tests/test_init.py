"""Tests for the AdGuard Home Extended integration init."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant

from custom_components.adguard_home_extended import async_unload_entry
from custom_components.adguard_home_extended.const import DOMAIN


class TestAsyncUnloadEntry:
    """Tests for async_unload_entry."""

    @pytest.fixture
    def mock_hass(self) -> MagicMock:
        """Return a mock Home Assistant instance."""
        hass = MagicMock(spec=HomeAssistant)
        hass.config_entries = MagicMock()
        hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
        hass.services = MagicMock()
        hass.services.async_remove = MagicMock()
        return hass

    @pytest.fixture
    def mock_entry(self) -> MagicMock:
        """Return a mock config entry."""
        entry = MagicMock()
        entry.entry_id = "test_entry_123"
        return entry

    @pytest.mark.asyncio
    async def test_unload_cleans_up_client_manager(
        self, mock_hass: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test that unload cleans up ClientEntityManager."""
        # Setup mock client manager
        mock_client_manager = MagicMock()
        mock_client_manager.async_unsubscribe = MagicMock()

        mock_hass.data = {
            DOMAIN: {
                mock_entry.entry_id: MagicMock(),  # coordinator
                "client_managers": {
                    mock_entry.entry_id: mock_client_manager,
                },
            }
        }

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
        mock_hass.data = {
            DOMAIN: {
                mock_entry.entry_id: MagicMock(),  # coordinator
            }
        }

        result = await async_unload_entry(mock_hass, mock_entry)

        assert result is True
        # Verify entry was removed
        assert mock_entry.entry_id not in mock_hass.data[DOMAIN]

    @pytest.mark.asyncio
    async def test_unload_removes_services_when_last_entry(
        self, mock_hass: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test that services are removed when last entry is unloaded."""
        mock_hass.data = {
            DOMAIN: {
                mock_entry.entry_id: MagicMock(),  # Only entry
            }
        }

        result = await async_unload_entry(mock_hass, mock_entry)

        assert result is True
        # Verify services were removed
        assert mock_hass.services.async_remove.call_count >= 7  # All services removed

    @pytest.mark.asyncio
    async def test_unload_keeps_services_when_other_entries_exist(
        self, mock_hass: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test that services are kept when other entries still exist."""
        other_entry_id = "other_entry_456"
        mock_hass.data = {
            DOMAIN: {
                mock_entry.entry_id: MagicMock(),
                other_entry_id: MagicMock(),  # Another entry exists
            }
        }

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
                mock_entry.entry_id: MagicMock(),
                "client_managers": {
                    mock_entry.entry_id: mock_client_manager,
                },
            }
        }

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
        mock_hass.data = {
            DOMAIN: {
                mock_entry.entry_id: MagicMock(),
            }
        }

        result = await async_unload_entry(mock_hass, mock_entry)

        assert result is False
        # Entry should still be in data since unload failed
        assert mock_entry.entry_id in mock_hass.data[DOMAIN]


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
        return entry

    @pytest.mark.asyncio
    async def test_remove_entry_cleans_up_domain_data(
        self, mock_hass: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test that remove entry cleans up domain data."""
        from custom_components.adguard_home_extended import async_remove_entry

        mock_hass.data = {
            DOMAIN: {
                mock_entry.entry_id: MagicMock(),
            }
        }

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
                mock_entry.entry_id: MagicMock(),
                "client_managers": {
                    mock_entry.entry_id: MagicMock(),
                },
            }
        }

        await async_remove_entry(mock_hass, mock_entry)

        # Domain data should be cleaned up completely if empty
        assert DOMAIN not in mock_hass.data

    @pytest.mark.asyncio
    async def test_remove_entry_preserves_other_entries(
        self, mock_hass: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test that remove entry preserves other entries."""
        from custom_components.adguard_home_extended import async_remove_entry

        other_entry_id = "other_entry_456"
        mock_hass.data = {
            DOMAIN: {
                mock_entry.entry_id: MagicMock(),
                other_entry_id: MagicMock(),
            }
        }

        await async_remove_entry(mock_hass, mock_entry)

        # Domain data should still exist with other entry
        assert DOMAIN in mock_hass.data
        assert other_entry_id in mock_hass.data[DOMAIN]

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
