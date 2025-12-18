"""Fixtures for AdGuard Home Extended tests.

# TODO: Update pytest-homeassistant-custom-component when a version > 0.13.205 is released
# that includes the fix for _run_safe_shutdown_loop thread cleanup in verify_cleanup.
# The fix adds `or "_run_safe_shutdown_loop" in thread.name` to the thread assertion.
# See: https://github.com/MatthewFlamm/pytest-homeassistant-custom-component/blob/main/src/pytest_homeassistant_custom_component/plugins.py
# Current version 0.13.205 causes a spurious teardown error on some tests.
"""
from __future__ import annotations

import builtins
import threading
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.adguard_home_extended.api.models import (
    AdGuardHomeStats,
    AdGuardHomeStatus,
    BlockedService,
    DhcpStatus,
    FilteringStatus,
)

# Monkey-patch threading._DummyThread to allow _run_safe_shutdown_loop threads
# This works around a bug in pytest-homeassistant-custom-component < 0.13.206
_original_isinstance = isinstance


def _patched_isinstance(obj, classinfo):
    """Allow aiohttp shutdown threads to pass verify_cleanup."""
    if classinfo is threading._DummyThread and hasattr(obj, "name"):
        if "_run_safe_shutdown_loop" in obj.name:
            return True
    return _original_isinstance(obj, classinfo)


# Apply the patch at module load time
builtins.isinstance = _patched_isinstance


@pytest.fixture
def mock_adguard_client() -> Generator[AsyncMock, None, None]:
    """Return a mocked AdGuard Home client."""
    with patch(
        "custom_components.adguard_home_extended.api.client.AdGuardHomeClient",
        autospec=True,
    ) as mock_client_class:
        client = mock_client_class.return_value

        # Mock status - includes all required fields per OpenAPI ServerStatus schema
        client.get_status = AsyncMock(
            return_value=AdGuardHomeStatus(
                protection_enabled=True,
                running=True,
                dns_addresses=["192.168.1.1"],
                dns_port=53,
                http_port=3000,
                version="0.107.43",
                language="en",
                protection_disabled_until=None,
                dhcp_available=True,
            )
        )

        # Mock stats - matches OpenAPI Stats schema structure
        # Note: Our model uses snake_case property names that map from API's num_* prefixed fields
        client.get_stats = AsyncMock(
            return_value=AdGuardHomeStats(
                dns_queries=12345,
                blocked_filtering=1234,
                replaced_safebrowsing=10,
                replaced_parental=5,
                replaced_safesearch=2,
                avg_processing_time=15.5,
                top_queried_domains=[{"example.com": 100}, {"google.com": 80}],
                top_blocked_domains=[{"ads.example.com": 50}, {"tracker.com": 30}],
                top_clients=[{"192.168.1.100": 500}, {"192.168.1.101": 300}],
                # v0.107.36+ fields
                top_upstreams_responses=[{"1.1.1.1": 1000}],
                top_upstreams_avg_time=[{"1.1.1.1": 0.025}],
                time_units="hours",
            )
        )

        # Mock filtering status - matches OpenAPI FilterStatus schema
        # Filter objects require: enabled, id, name, rules_count, url
        client.get_filtering_status = AsyncMock(
            return_value=FilteringStatus(
                enabled=True,
                interval=24,
                filters=[
                    {
                        "id": 1,
                        "name": "AdGuard Base",
                        "url": "https://example.com/base.txt",
                        "enabled": True,
                        "rules_count": 5912,
                        "last_updated": "2024-01-15T10:30:00Z",
                    }
                ],
                whitelist_filters=[],
                user_rules=[],
            )
        )

        # Mock blocked services - per OpenAPI BlockedService schema
        # Required fields: icon_svg, id, name, rules
        client.get_all_blocked_services = AsyncMock(
            return_value=[
                BlockedService(id="facebook", name="Facebook", icon_svg="<svg></svg>"),
                BlockedService(id="youtube", name="YouTube", icon_svg="<svg></svg>"),
                BlockedService(id="tiktok", name="TikTok", icon_svg="<svg></svg>"),
                BlockedService(
                    id="instagram", name="Instagram", icon_svg="<svg></svg>"
                ),
            ]
        )
        client.get_blocked_services = AsyncMock(return_value=["facebook", "tiktok"])
        client.set_blocked_services = AsyncMock()

        # Mock clients
        client.get_clients = AsyncMock(return_value=[])
        client.update_client = AsyncMock()

        # Mock DHCP - matches OpenAPI DhcpStatus schema
        # Required fields: leases; Optional: enabled, interface_name, v4, v6, static_leases
        client.get_dhcp_status = AsyncMock(
            return_value=DhcpStatus(
                enabled=False,
                interface_name="",
                leases=[],
                static_leases=[],
            )
        )

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
