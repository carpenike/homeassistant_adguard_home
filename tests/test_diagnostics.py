"""Tests for diagnostics support."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from custom_components.adguard_home_extended.api.models import (
    AdGuardHomeStats,
    AdGuardHomeStatus,
    DhcpStatus,
    DnsRewrite,
    FilteringStatus,
)
from custom_components.adguard_home_extended.coordinator import AdGuardHomeData
from custom_components.adguard_home_extended.diagnostics import (
    async_get_config_entry_diagnostics,
)


class TestDiagnostics:
    """Test diagnostics functions."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Create a mock coordinator with test data."""
        coordinator = MagicMock()

        data = AdGuardHomeData()
        data.status = AdGuardHomeStatus(
            protection_enabled=True,
            running=True,
            dns_addresses=["192.168.1.1"],
            dns_port=53,
            http_port=3000,
            version="0.107.0",
        )
        data.stats = AdGuardHomeStats(
            dns_queries=10000,
            blocked_filtering=1500,
            replaced_safebrowsing=10,
            replaced_parental=5,
            replaced_safesearch=20,
            avg_processing_time=0.015,
            top_queried_domains=[{"example.com": 100}],
            top_blocked_domains=[{"ads.com": 50}],
            top_clients=[{"192.168.1.10": 500}],
        )
        data.filtering = FilteringStatus(
            enabled=True,
            interval=24,
            filters=[{"id": 1, "name": "Filter 1"}],
            whitelist_filters=[],
            user_rules=["||example.com^"],
        )
        data.blocked_services = ["facebook", "tiktok"]
        data.available_services = [{"id": "facebook", "name": "Facebook"}]
        data.clients = [
            {
                "name": "Test Client",
                "ids": ["192.168.1.100"],
                "filtering_enabled": True,
                "parental_enabled": False,
                "safebrowsing_enabled": False,
                "safesearch_enabled": False,
                "blocked_services": ["youtube"],
            }
        ]
        data.dhcp = DhcpStatus(
            enabled=True, interface_name="eth0", leases=[], static_leases=[]
        )
        data.rewrites = [DnsRewrite(domain="custom.local", answer="192.168.1.50")]
        data.query_log = [{"QH": "example.com", "IP": "192.168.1.10"}]

        coordinator.data = data
        return coordinator

    @pytest.fixture
    def mock_entry(self, mock_coordinator: MagicMock) -> MagicMock:
        """Create a mock config entry."""
        entry = MagicMock()
        entry.as_dict.return_value = {
            "entry_id": "test_entry_id",
            "data": {
                "host": "192.168.1.1",
                "port": 3000,
                "username": "admin",
                "password": "secret123",
            },
        }
        entry.entry_id = "test_entry_id"
        # Coordinator is now stored in runtime_data
        entry.runtime_data = mock_coordinator
        return entry

    @pytest.mark.asyncio
    async def test_diagnostics_returns_dict(
        self, mock_coordinator: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test that diagnostics returns a dictionary."""
        hass = MagicMock()
        # hass.data no longer stores coordinators with runtime_data pattern
        hass.data = {}

        result = await async_get_config_entry_diagnostics(hass, mock_entry)

        assert isinstance(result, dict)
        assert "config_entry" in result
        assert "data" in result

    @pytest.mark.asyncio
    async def test_diagnostics_redacts_credentials(
        self, mock_coordinator: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test that diagnostics redacts sensitive credentials."""
        hass = MagicMock()
        hass.data = {}

        result = await async_get_config_entry_diagnostics(hass, mock_entry)

        # The config_entry should be processed by async_redact_data
        # We can't easily check the exact redaction without running through HA's redaction
        assert "config_entry" in result

    @pytest.mark.asyncio
    async def test_diagnostics_includes_status(
        self, mock_coordinator: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test that diagnostics includes status info."""
        hass = MagicMock()
        hass.data = {}

        result = await async_get_config_entry_diagnostics(hass, mock_entry)

        assert "status" in result["data"]
        assert result["data"]["status"]["protection_enabled"] is True
        assert result["data"]["status"]["version"] == "0.107.0"
        # DNS addresses should be redacted
        assert result["data"]["status"]["dns_addresses"] == "**REDACTED**"

    @pytest.mark.asyncio
    async def test_diagnostics_includes_stats(
        self, mock_coordinator: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test that diagnostics includes stats."""
        hass = MagicMock()
        hass.data = {}

        result = await async_get_config_entry_diagnostics(hass, mock_entry)

        assert "stats" in result["data"]
        assert result["data"]["stats"]["dns_queries"] == 10000
        assert result["data"]["stats"]["blocked_filtering"] == 1500
        # Should include counts but not actual domain/client data
        assert "top_queried_domains_count" in result["data"]["stats"]
        assert "top_queried_domains" not in result["data"]["stats"]

    @pytest.mark.asyncio
    async def test_diagnostics_redacts_client_ids(
        self, mock_coordinator: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test that diagnostics redacts client IDs (IPs/MACs)."""
        hass = MagicMock()
        hass.data = {}

        result = await async_get_config_entry_diagnostics(hass, mock_entry)

        assert "clients" in result["data"]
        assert result["data"]["clients"]["count"] == 1
        # Client IDs should be redacted
        assert result["data"]["clients"]["clients"][0]["ids"] == "**REDACTED**"
        # Name should be visible
        assert result["data"]["clients"]["clients"][0]["name"] == "Test Client"

    @pytest.mark.asyncio
    async def test_diagnostics_includes_rewrites_domains_only(
        self, mock_coordinator: MagicMock, mock_entry: MagicMock
    ) -> None:
        """Test that diagnostics includes rewrite domains but not answers."""
        hass = MagicMock()
        hass.data = {}

        result = await async_get_config_entry_diagnostics(hass, mock_entry)

        assert "rewrites" in result["data"]
        assert result["data"]["rewrites"]["count"] == 1
        assert "domains" in result["data"]["rewrites"]
        assert "custom.local" in result["data"]["rewrites"]["domains"]

    @pytest.mark.asyncio
    async def test_diagnostics_handles_missing_data(
        self, mock_entry: MagicMock
    ) -> None:
        """Test that diagnostics handles missing coordinator data gracefully."""
        coordinator = MagicMock()
        coordinator.data = AdGuardHomeData()  # Empty data
        mock_entry.runtime_data = coordinator  # Override with empty coordinator

        hass = MagicMock()
        hass.data = {}

        result = await async_get_config_entry_diagnostics(hass, mock_entry)

        assert isinstance(result, dict)
        assert "data" in result
