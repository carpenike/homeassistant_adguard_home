"""Fixtures for AdGuard Home Extended tests."""
from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.adguard_home_extended.api.models import (
    AdGuardHomeStatus,
    AdGuardHomeStats,
    FilteringStatus,
    DhcpStatus,
    BlockedService,
)


@pytest.fixture
def mock_adguard_client() -> Generator[AsyncMock, None, None]:
    """Return a mocked AdGuard Home client."""
    with patch(
        "custom_components.adguard_home_extended.api.client.AdGuardHomeClient",
        autospec=True,
    ) as mock_client_class:
        client = mock_client_class.return_value
        
        # Mock status
        client.get_status = AsyncMock(return_value=AdGuardHomeStatus(
            protection_enabled=True,
            running=True,
            dns_addresses=["192.168.1.1"],
            dns_port=53,
            http_port=3000,
            version="0.107.43",
        ))
        
        # Mock stats
        client.get_stats = AsyncMock(return_value=AdGuardHomeStats(
            dns_queries=12345,
            blocked_filtering=1234,
            replaced_safebrowsing=10,
            replaced_parental=5,
            replaced_safesearch=2,
            avg_processing_time=15.5,
            top_queried_domains=[{"example.com": 100}, {"google.com": 80}],
            top_blocked_domains=[{"ads.example.com": 50}, {"tracker.com": 30}],
            top_clients=[{"192.168.1.100": 500}, {"192.168.1.101": 300}],
        ))
        
        # Mock filtering status
        client.get_filtering_status = AsyncMock(return_value=FilteringStatus(
            enabled=True,
            interval=24,
            filters=[
                {"id": 1, "name": "AdGuard Base", "url": "https://example.com/base.txt", "enabled": True}
            ],
            whitelist_filters=[],
            user_rules=[],
        ))
        
        # Mock blocked services
        client.get_all_blocked_services = AsyncMock(return_value=[
            BlockedService(id="facebook", name="Facebook", icon_svg=""),
            BlockedService(id="youtube", name="YouTube", icon_svg=""),
            BlockedService(id="tiktok", name="TikTok", icon_svg=""),
            BlockedService(id="instagram", name="Instagram", icon_svg=""),
        ])
        client.get_blocked_services = AsyncMock(return_value=["facebook", "tiktok"])
        client.set_blocked_services = AsyncMock()
        
        # Mock clients
        client.get_clients = AsyncMock(return_value=[])
        client.update_client = AsyncMock()
        
        # Mock DHCP
        client.get_dhcp_status = AsyncMock(return_value=DhcpStatus(
            enabled=False,
            leases=[],
        ))
        
        # Mock protection toggles
        client.set_protection = AsyncMock()
        client.set_safebrowsing = AsyncMock()
        client.set_parental = AsyncMock()
        client.set_safesearch = AsyncMock()
        
        # Mock filter management
        client.add_filter_url = AsyncMock()
        client.remove_filter_url = AsyncMock()
        client.refresh_filters = AsyncMock()
        
        # Mock connection test
        client.test_connection = AsyncMock(return_value=True)
        
        yield client


@pytest.fixture
def mock_config_entry() -> MagicMock:
    """Return a mock config entry."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.data = {
        "host": "192.168.1.1",
        "port": 3000,
        "username": "admin",
        "password": "password",
        "ssl": False,
        "verify_ssl": True,
    }
    entry.options = {}
    return entry


@pytest.fixture
def mock_hass() -> MagicMock:
    """Return a mock Home Assistant instance."""
    hass = MagicMock()
    hass.data = {}
    hass.services = MagicMock()
    hass.services.has_service = MagicMock(return_value=False)
    hass.services.async_register = MagicMock()
    return hass
