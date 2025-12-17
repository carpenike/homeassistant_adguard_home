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
